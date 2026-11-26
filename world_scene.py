# Nando memilih C14 dan menetapkan GLB untuk penggambaran lingkungan statis.
# Tata letak dan koordinat mengikuti brief tim.
# [AI] Dokumentasi: Claude (2026-11-23) merangkum W1–W3; Codex (2026-11-26)
# menjelaskan urutan pemuatan, gambar, dan pelepasan GLB.
"""
Dunia statis dan kamera orbit Aether Castle Skyport. PJ Nando.
Sumbu +Y ke atas, +X ke timur, -Z ke utara. Satuan meter, lantai pulau pada y=0.
Tanda ◇ menunjukkan nilai dari brief v2 yang perlu dicocokkan dengan prototipe.

Di main.py, muat model sekali sesudah init_window() dan ambil get_landmarks().
Setiap frame, panggil kamera.update(dt), gambar_langit(model) sebelum begin_mode_3d(),
lalu gambar_dunia(model) di dalamnya. Panggil unload_model(model) sebelum close_window().

Jalankan python world_scene.py [--primitives]. Gunakan panah kiri dan kanan untuk orbit.
"""
import argparse
import math
from pathlib import Path

import pyray as rl

# Aset C14 dan warna langit dari preview C16.
ASET_DUNIA = Path(__file__).resolve().parent / "assets" / "skyport_world.glb"
ASAL_MODEL = rl.Vector3(0.0, 0.0, 0.0)
LANGIT_PUNCAK = rl.Color(94, 166, 232, 255)
LANGIT_CAKRAWALA = rl.Color(210, 236, 245, 255)

# ---------- Tabel landmark (brief §4.4) ----------
# [AI] Claude (2026-11-23): konstanta landmark dari brief, penanda W1, dan geometri
# primitif beserta urutan gambar W2–W3 untuk mengecek skala dan tata letak.
# All positions in metres. (x, z) = centre on the ground plan; heights are measured from y = 0.
KEEP_PUSAT = (-18.0, -4.0)               # main keep centre (x, z) ◇ - Module D obstacle
KEEP_UKURAN = (16.0, 12.0)               # keep footprint along x and z ◇
KEEP_ATAP = 19.0                         # height of the keep's roof top ◇

SPIRE_PUSAT = (0.0, -16.0)               # banner spire centre (x, z) ◇
SPIRE_TINGGI = 28.0                      # spire tower top ◇
SPIRE_R = 3.5                            # radius perkiraan spire
TIANG_PUNCAK = 38.0                      # flagpole top ◇
TIANG_BENDERA = (0.0, 37.5, -16.0)       # banner pin point; MUST equal TIANG in mod_c_cloth.py

MENARA_SUDUT = [(-21.0, -19.0), (-21.0, 19.0), (21.0, -19.0)]   # corner towers T1, T2, T3 (x, z) ◇
MENARA_SUDUT_R = 2.8                     # corner tower radius ◇
MENARA_SUDUT_TINGGI = 21.0               # height of the cone tip ◇

GERBANG = [(-9.0, 25.0), (9.0, 25.0)]    # south gatehouse towers (x, z) ◇
GERBANG_R = 3.2                          # gate tower radius ◇
GERBANG_TINGGI = 11.0                    # gate tower height ◇

DERMAGA_X = (30.0, 41.0)                 # east pier extent along x ◇
DERMAGA_Z = (-4.0, 4.0)                  # east pier extent along z ◇
DERMAGA_Y = 1.0                          # pier deck height
TAMBAT = (38.0, 4.5, 0.0)                # docking berth = Module A waypoint WP0 ◇
TIANG_DERMAGA = (31.0, 3.0)              # pier mast (x, z) ◇ - dock pennant (Tier 2)
TIANG_DERMAGA_TINGGI = 8.0               # pier mast top ◇
TIANG_PENNANT = (31.0, 8.0, 3.0)         # pennant pin point (Tier 2); must equal the pennant's TIANG

PULAU_R = 32.0                           # radius plateau W3; menara sudut mencapai r ≈ 31,1 m

# ---------- Bentuk padat (W2) ----------
# Lapisan pulau: (y bawah, y atas, radius bawah, radius atas, warna).
PULAU_LAPISAN = [
    (-1.5, 0.0, PULAU_R, PULAU_R, "rumput"),
    (-8.0, -1.5, 27.0, PULAU_R, "tanah1"),
    (-16.0, -8.0, 19.0, 27.0, "tanah2"),
    (-25.0, -16.0, 10.0, 19.0, "tanah1"),
    (-34.0, -25.0, 0.0, 10.0, "tanah2"),
]
KEEP_DINDING = 14.0                      # m, height of the keep walls; the gable roof rises from here to KEEP_ATAP
MENARA_SUDUT_BADAN = 16.0                # m, corner tower body height; the cone roof goes up to MENARA_SUDUT_TINGGI
MENARA_SUDUT_ATAP_R = 3.4                # m, cone roof radius (a little wider than the tower = overhang)
GERBANG_LINTEL = (6.0, 10.0)             # m, bottom and top of the stone lintel between the two gate towers
TIANG_R = 0.15                           # m, flagpole radius
WARNA = {                                # flat colours (brief §4.2 rule 5: no shaders)
    "rumput": rl.Color(96, 140, 72, 255), "tanah1": rl.Color(122, 96, 70, 255), "tanah2": rl.Color(98, 78, 58, 255),
    "batu": rl.Color(168, 166, 158, 255), "batu_gelap": rl.Color(128, 126, 120, 255),
    "atap": rl.Color(150, 58, 44, 255), "atap_gelap": rl.Color(118, 44, 34, 255),
    "tiang": rl.Color(60, 60, 60, 255), "anglo": rl.Color(70, 50, 40, 255),
    "kayu": rl.Color(146, 104, 66, 255), "kayu_gelap": rl.Color(104, 72, 46, 255), "awan": rl.Color(246, 248, 252, 255),
}
# Wireframe W1 untuk mode primitif.
TAMPILKAN_PENANDA = False

# ---------- Dermaga, langit, awan (W3) ----------
DERMAGA_TEBAL = 0.5                      # m, deck thickness (deck top at DERMAGA_Y)
DERMAGA_PENYANGGA = [(33.0, -3.5), (33.0, 3.5), (39.0, -3.5), (39.0, 3.5)]   # support posts (x, z) under the deck
DERMAGA_PENYANGGA_BAWAH = -4.0           # m, the posts hang down to here (the pier sticks out past the island edge)
PATOK_TAMBAT = [(38.0, -3.6), (38.0, 3.6)]   # mooring bollards (x, z) on the deck, beside the berth WP0
TIANG_DERMAGA_R = 0.12                   # m, pier mast radius
LANGIT = rl.Color(178, 214, 240, 255)    # sky = clear colour of the window (main.py uses it too)
# clouds: (x, y, z, size in m). They sit on a ring ~130 m from the centre, beyond the camera's 100 m orbit,
# so a cloud is either behind the island (visible) or behind the camera (invisible) - it never blocks the view.
AWAN = [(-120.0, 30.0, -60.0, 9.0), (60.0, 40.0, -118.0, 11.0), (125.0, -15.0, 40.0, 10.0),
        (-40.0, -25.0, 124.0, 12.0), (-128.0, 5.0, 45.0, 8.0)]
# each cloud is 3 low-poly spheres; built once here, not every frame: (centre Vector3, radius)
AWAN_BOLA = [(rl.Vector3(x + dx * s, y + dy * s, z + dz * s), f * s)
             for x, y, z, s in AWAN
             for dx, dy, dz, f in ((0.0, 0.0, 0.0, 1.0), (0.9, -0.2, 0.0, 0.7), (-0.9, -0.25, 0.3, 0.6))]

# ---------- Kamera ----------
# Parameter orbit mengikuti brief §4.3. Laju 1,2 rad/detik setara orbit W3 pada 60 FPS.
KAMERA_TARGET = (0.0, 10.0, 0.0)         # orbit centre (brief §4.3)
KAMERA_R = 100.0                         # m, horizontal orbit radius; with KAMERA_H the distance is ≈ 106 m (brief ≈ 105 ◇)
KAMERA_H = 35.0                          # tinggi kamera di atas target (m)
KAMERA_SUDUT_AWAL = 0.6                  # rad, start angle (same as the lecturer's cam_ang)
KAMERA_PUTAR = 1.2
KAMERA_FOVY = 45.0                       # degrees, vertical field of view (lecturer's value)

def v3(p):
    """[AI] (x, y, z) -> rl.Vector3, like the lecturer's v3 in cloth_p16.py."""
    return rl.Vector3(float(p[0]), float(p[1]), float(p[2]))

# [DOSEN] -> [AI] cloth_p16.py main(): the lecturer's orbit camera (cam_ang changed by left/right, position on a
#      circle around the target) moved into a class so main.py can own one camera object; target, radius and
#      height changed for the island. Claude, 2026-11-23; reviewed by Nando: pending
# Codex (2026-11-26): pakai dt agar laju orbit tetap saat FPS berubah.
class Kamera:
    def __init__(self):
        self.sudut = KAMERA_SUDUT_AWAL
        self.cam = rl.Camera3D(v3((0.0, 0.0, 0.0)), v3(KAMERA_TARGET), rl.Vector3(0, 1, 0), KAMERA_FOVY,
                               rl.CAMERA_PERSPECTIVE)
        self._letakkan()

    def update(self, dt=None):
        """Putar kamera dengan panah kiri dan kanan memakai dt dalam detik."""
        arah = int(rl.is_key_down(rl.KEY_RIGHT)) - int(rl.is_key_down(rl.KEY_LEFT))
        if not arah:
            return
        if dt is None:
            dt = rl.get_frame_time()
        if dt > 0.0:
            self.sudut += arah * KAMERA_PUTAR * dt
            self._letakkan()

    def _letakkan(self):
        # position on a horizontal circle of radius KAMERA_R around the target, KAMERA_H above it
        tx, ty, tz = KAMERA_TARGET
        self.cam.position = v3((tx + KAMERA_R * math.sin(self.sudut), ty + KAMERA_H, tz + KAMERA_R * math.cos(self.sudut)))

# ---------- Penanda posisi (W1) ----------
def gambar_penanda():
    """Draw inside rl.begin_mode_3d: one wireframe shape per landmark of brief §4.4."""
    # island outline on the deck level y = 0 (circle is drawn in the XY plane, so turn it 90° about X)
    rl.draw_circle_3d(v3((0.0, 0.0, 0.0)), PULAU_R, rl.Vector3(1, 0, 0), 90.0, rl.DARKGREEN)
    # keep: box from the ground to the roof top
    kx, kz = KEEP_PUSAT
    rl.draw_cube_wires(v3((kx, KEEP_ATAP / 2, kz)), KEEP_UKURAN[0], KEEP_ATAP, KEEP_UKURAN[1], rl.BROWN)
    # banner spire, flagpole and the banner pin point (red)
    sx, sz = SPIRE_PUSAT
    rl.draw_cylinder_wires(v3((sx, 0.0, sz)), SPIRE_R, SPIRE_R, SPIRE_TINGGI, 12, rl.MAROON)
    rl.draw_line_3d(v3((sx, SPIRE_TINGGI, sz)), v3((sx, TIANG_PUNCAK, sz)), rl.DARKGRAY)
    rl.draw_sphere(v3(TIANG_BENDERA), 0.6, rl.RED)
    # corner towers T1-T3 and gate towers
    for x, z in MENARA_SUDUT:
        rl.draw_cylinder_wires(v3((x, 0.0, z)), MENARA_SUDUT_R, MENARA_SUDUT_R, MENARA_SUDUT_TINGGI, 12, rl.GRAY)
    for x, z in GERBANG:
        rl.draw_cylinder_wires(v3((x, 0.0, z)), GERBANG_R, GERBANG_R, GERBANG_TINGGI, 12, rl.DARKGRAY)
    # pier box from y = 0 to the deck, the berth (blue) and the pier mast with the pennant pin point (orange)
    x0, x1 = DERMAGA_X
    z0, z1 = DERMAGA_Z
    rl.draw_cube_wires(v3(((x0 + x1) / 2, DERMAGA_Y / 2, (z0 + z1) / 2)), x1 - x0, DERMAGA_Y, z1 - z0, rl.BROWN)
    rl.draw_sphere(v3(TAMBAT), 0.8, rl.BLUE)
    mx, mz = TIANG_DERMAGA
    rl.draw_line_3d(v3((mx, DERMAGA_Y, mz)), v3((mx, TIANG_DERMAGA_TINGGI, mz)), rl.DARKGRAY)
    rl.draw_sphere(v3(TIANG_PENNANT), 0.5, rl.ORANGE)
    # axes at the origin: +X east (red), +Y up (green), +Z south (blue)
    rl.draw_line_3d(v3((0, 0, 0)), v3((10, 0, 0)), rl.RED)
    rl.draw_line_3d(v3((0, 0, 0)), v3((0, 10, 0)), rl.GREEN)
    rl.draw_line_3d(v3((0, 0, 0)), v3((0, 0, 10)), rl.BLUE)

# ---------- Model padat (W2) ----------
def segitiga_dua_sisi(a, b, c, warna):
    """One triangle visible from both sides: drawn twice with opposite windings (only used for the few roof
    triangles, so the cheap trick is fine here; the banner uses the culling-off method instead)."""
    rl.draw_triangle_3d(v3(a), v3(b), v3(c), warna)
    rl.draw_triangle_3d(v3(a), v3(c), v3(b), warna)

def gambar_pulau():
    """Floating island: stacked cylinders from PULAU_LAPISAN (draw_cylinder starts at the bottom and goes up)."""
    for y0, y1, r0, r1, kunci in PULAU_LAPISAN:
        rl.draw_cylinder(v3((0.0, y0, 0.0)), r1, r0, y1 - y0, 24, WARNA[kunci])

def gambar_keep():
    """Gambar dinding dan enam segitiga atap pelana, masing-masing dua sisi."""
    kx, kz = KEEP_PUSAT
    w, d = KEEP_UKURAN
    rl.draw_cube(v3((kx, KEEP_DINDING / 2, kz)), w, KEEP_DINDING, d, WARNA["batu"])
    x0, x1, z0, z1, y0, y1 = kx - w / 2, kx + w / 2, kz - d / 2, kz + d / 2, KEEP_DINDING, KEEP_ATAP
    # the four eave corners and the two ends of the ridge
    a, b, c, e = (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)
    p, q = (x0, y1, kz), (x1, y1, kz)
    for tri, kunci in (((a, b, q), "atap"), ((a, q, p), "atap"),               # north slope
                       ((e, c, q), "atap_gelap"), ((e, q, p), "atap_gelap"),   # south slope (darker = simple tint)
                       ((a, e, p), "batu_gelap"), ((b, c, q), "batu_gelap")):  # the two gable ends
        segitiga_dua_sisi(*tri, WARNA[kunci])

def gambar_menara():
    """Corner towers with cone roofs, the banner spire with its pole, and the gate towers with brazier bowls."""
    for x, z in MENARA_SUDUT:
        rl.draw_cylinder(v3((x, 0.0, z)), MENARA_SUDUT_R, MENARA_SUDUT_R, MENARA_SUDUT_BADAN, 12, WARNA["batu"])
        rl.draw_cylinder(v3((x, MENARA_SUDUT_BADAN, z)), 0.0, MENARA_SUDUT_ATAP_R,
                         MENARA_SUDUT_TINGGI - MENARA_SUDUT_BADAN, 12, WARNA["atap"])
    sx, sz = SPIRE_PUSAT
    rl.draw_cylinder(v3((sx, 0.0, sz)), SPIRE_R, SPIRE_R, SPIRE_TINGGI, 16, WARNA["batu"])
    rl.draw_cylinder(v3((sx, SPIRE_TINGGI - 1.5, sz)), SPIRE_R + 0.5, SPIRE_R + 0.5, 1.5, 16, WARNA["batu_gelap"])
    rl.draw_cylinder_ex(v3((sx, SPIRE_TINGGI, sz)), v3((sx, TIANG_PUNCAK, sz)), TIANG_R, TIANG_R, 8, WARNA["tiang"])
    for x, z in GERBANG:
        rl.draw_cylinder(v3((x, 0.0, z)), GERBANG_R, GERBANG_R, GERBANG_TINGGI, 12, WARNA["batu_gelap"])
        rl.draw_cylinder(v3((x, GERBANG_TINGGI, z)), 1.2, 0.8, 0.6, 10, WARNA["anglo"])   # brazier bowl (decoration)
    # stone lintel over the gate, between the inner faces of the two gate towers
    (gx0, gz), (gx1, _) = GERBANG
    ly0, ly1 = GERBANG_LINTEL
    rl.draw_cube(v3(((gx0 + gx1) / 2, (ly0 + ly1) / 2, gz)), (gx1 - gx0) - 2 * GERBANG_R + 1.0, ly1 - ly0, 2.0,
                 WARNA["batu_gelap"])

def gambar_dermaga():
    """East pier: wooden deck, support posts under it, two mooring bollards at the berth, and the pennant mast."""
    x0, x1 = DERMAGA_X
    z0, z1 = DERMAGA_Z
    rl.draw_cube(v3(((x0 + x1) / 2, DERMAGA_Y - DERMAGA_TEBAL / 2, (z0 + z1) / 2)), x1 - x0, DERMAGA_TEBAL, z1 - z0,
                 WARNA["kayu"])
    alas = DERMAGA_Y - DERMAGA_TEBAL                  # underside of the deck
    for x, z in DERMAGA_PENYANGGA:
        rl.draw_cylinder(v3((x, DERMAGA_PENYANGGA_BAWAH, z)), 0.3, 0.3, alas - DERMAGA_PENYANGGA_BAWAH, 8,
                         WARNA["kayu_gelap"])
    for x, z in PATOK_TAMBAT:
        rl.draw_cylinder(v3((x, DERMAGA_Y, z)), 0.25, 0.3, 0.8, 8, WARNA["kayu_gelap"])
    mx, mz = TIANG_DERMAGA
    rl.draw_cylinder_ex(v3((mx, DERMAGA_Y, mz)), v3((mx, TIANG_DERMAGA_TINGGI + 0.5, mz)), TIANG_DERMAGA_R,
                        TIANG_DERMAGA_R, 8, WARNA["tiang"])

def gambar_awan():
    """Clouds: low-poly spheres (8 rings x 10 slices) from the list built once in AWAN_BOLA."""
    for pusat, r in AWAN_BOLA:
        rl.draw_sphere_ex(pusat, r, 8, 10, WARNA["awan"])

# [AI] Codex (2026-11-26): muat dan validasi GLB C14, gambar dunia dan langit,
# serta gunakan jalur primitif W3 untuk membandingkan kedua tampilan.
def muat_model_dunia():
    """Muat model sesudah konteks grafis Raylib tersedia."""
    if not ASET_DUNIA.is_file():
        raise FileNotFoundError(f"Aset world GLB tidak ditemukan: {ASET_DUNIA}")
    model = rl.load_model(str(ASET_DUNIA))
    if not rl.is_model_valid(model):
        rl.unload_model(model)
        raise RuntimeError(f"Raylib gagal memuat aset world: {ASET_DUNIA}")
    return model


def gambar_langit(model=None):
    """Gambar latar setelah begin_drawing() dan sebelum begin_mode_3d()."""
    rl.clear_background(LANGIT)
    if model is not None:
        rl.draw_rectangle_gradient_v(0, 0, rl.get_screen_width(), rl.get_screen_height(),
                                     LANGIT_PUNCAK, LANGIT_CAKRAWALA)


def gambar_dunia(model=None):
    """Gambar world di mode 3D. Tanpa model, gunakan primitif W3."""
    if model is not None:
        rl.draw_model(model, ASAL_MODEL, 1.0, rl.WHITE)
        return
    gambar_awan()
    gambar_pulau()
    gambar_keep()
    gambar_menara()
    gambar_dermaga()

# ---------- Data untuk modul lain (lewat main.py) ----------
# [AI] Claude (2026-11-23): proxy bola awal dari landmark brief §4.4 dan §5.3.
# Codex (2026-11-26): get_landmarks() menyalin daftar proxy agar pemanggil tidak mengubah data world.
# Pusat proxy di setengah tinggi bangunan; margin dan bentuk akhir diperiksa bersama Modul D.
MENARA = ([((x, MENARA_SUDUT_TINGGI / 2, z), MENARA_SUDUT_R) for x, z in MENARA_SUDUT]
          + [((x, GERBANG_TINGGI / 2, z), GERBANG_R) for x, z in GERBANG]
          + [((SPIRE_PUSAT[0], SPIRE_TINGGI / 2, SPIRE_PUSAT[1]), SPIRE_R),
             ((KEEP_PUSAT[0], KEEP_ATAP / 2, KEEP_PUSAT[1]), math.hypot(*KEEP_UKURAN) / 2)])

def get_landmarks():
    """Read-only coordinates for main.py to pass on (modules never import world_scene):
    Banner(TIANG=lm["tiang_bendera"]), pennant at lm["tiang_pennant"], Module A berth lm["tambat"],
    Module D obstacles lm["menara"] = list of ((x, y, z), radius)."""
    return {"tiang_bendera": TIANG_BENDERA, "tiang_pennant": TIANG_PENNANT, "tambat": TAMBAT,
            "menara": MENARA.copy()}

# ---------- Program mandiri ----------
# [AI] Claude (2026-11-23): viewer mandiri dan penanda. Codex (2026-11-26):
# muat model sekali, lepas saat keluar, dan sediakan --primitives untuk membandingkan W3.
# Wireframe dibatasi ke W3 karena mengikuti geometri primitif.
LEBAR, TINGGI = 1280, 720                # window size in pixels (assignment target 1280 x 720)

def main(primitives=False):
    rl.init_window(LEBAR, TINGGI, "World Scene - Aether Castle Skyport")
    model = None
    tampilkan_penanda = primitives and TAMPILKAN_PENANDA
    try:
        if not primitives:
            model = muat_model_dunia()
        mode = "Primitif W3" if primitives else "GLB statis C14"
        rl.set_target_fps(60)
        kamera = Kamera()
        while not rl.window_should_close():
            kamera.update()
            rl.begin_drawing()
            gambar_langit(model)
            rl.begin_mode_3d(kamera.cam)
            gambar_dunia(model)
            if tampilkan_penanda:
                gambar_penanda()
            rl.end_mode_3d()
            rl.draw_text(f"Aether Castle Skyport | {mode}", 20, 16, 20, rl.DARKGRAY)
            if tampilkan_penanda:
                rl.draw_text("merah = TIANG bendera   oranye = TIANG pennant   biru = tambat (WP0)   hijau = tepi pulau",
                             20, 44, 18, rl.GRAY)
            rl.draw_text(f"kamera: sudut {math.degrees(kamera.sudut) % 360:.0f} deg, "
                         f"jarak {math.hypot(KAMERA_R, KAMERA_H):.0f} m", 20, 70, 18, rl.GRAY)
            rl.draw_text("kiri/kanan = putar kamera", 20, TINGGI - 28, 18, rl.GRAY)
            rl.draw_fps(LEBAR - 100, 16)
            rl.end_drawing()
    finally:
        if model is not None:
            rl.unload_model(model)
        rl.close_window()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Viewer world Aether Castle Skyport")
    parser.add_argument("--primitives", action="store_true", help="Tampilkan world primitif W3 untuk perbandingan")
    main(primitives=parser.parse_args().primitives)
