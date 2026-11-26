# [AI] Claude, 2026-11-23: module docstring (W1-W3); reviewed by Nando: pending
# [AI] Codex, 2026-11-26: catatan integrasi GLB (W4-W5); review Nando tertunda.
"""
world_scene.py - dunia statis Aether Castle Skyport: pulau, kastil, menara, tiang, dermaga, langit, kamera.
PJ: Nando. Raylib menampilkan lingkungan statis dan kamera. Simulasi berjalan di modul masing-masing.
Koordinat dari tabel landmark brief §4.4: +Y ke atas, +X timur, -Z utara, 1 unit = 1 m, y = 0 = lantai pulau.
Nilai bertanda ◇ dibawa dari brief v2 dan harus dicek dengan prototipe; perubahan diumumkan ke semua PJ.

W1: konstanta landmark + kamera orbit + penampil penanda (wireframe) untuk mengecek posisi sebelum dimodelkan.
W2: pulau padat (5 silinder bertumpuk), keep beratap pelana, menara sudut beratap kerucut, menara bendera + tiang,
    menara gerbang dengan mangkuk anglo (hiasan) dan ambang gerbang.
W3: dermaga + tiang penyangga + patok tambat, tiang pennant, warna langit, awan, dan get_landmarks() untuk main.py.
W4–W5: aset GLB statis C14 dan jalur render Raylib. Primitif W3 tersedia untuk perbandingan.

Integrasi dengan main.py: panggil muat_model_dunia() sekali setelah init_window() dan simpan hasilnya.
Panggil gambar_langit(model) sebelum begin_mode_3d() dan gambar_dunia(model) di dalamnya.
Ambil get_landmarks() sekali di awal. Lepas model dengan rl.unload_model(model) sebelum close_window().

Jalankan:  python world_scene.py [--primitives]
Kontrol :  kiri/kanan putar kamera
"""
import argparse
import math
from pathlib import Path

import pyray as rl

# [AI] Codex, 2026-11-26: aset C14 dan warna langit dari preview C16; review Nando tertunda.
ASET_DUNIA = Path(__file__).resolve().parent / "assets" / "skyport_world.glb"
ASAL_MODEL = rl.Vector3(0.0, 0.0, 0.0)
LANGIT_PUNCAK = rl.Color(94, 166, 232, 255)
LANGIT_CAKRAWALA = rl.Color(210, 236, 245, 255)

# ---------- Tabel landmark (brief §4.4) ----------
# [AI] Claude, 2026-11-23: landmark register copied from brief §4.4 into named constants; reviewed by Nando: pending
# All positions in metres. (x, z) = centre on the ground plan; heights are measured from y = 0.
KEEP_PUSAT = (-18.0, -4.0)               # main keep centre (x, z) ◇ - Module D obstacle
KEEP_UKURAN = (16.0, 12.0)               # keep footprint along x and z ◇
KEEP_ATAP = 19.0                         # height of the keep's roof top ◇

SPIRE_PUSAT = (0.0, -16.0)               # banner spire centre (x, z) ◇
SPIRE_TINGGI = 28.0                      # spire tower top ◇
SPIRE_R = 3.5                            # spire radius - MY ESTIMATE, not in the brief
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

PULAU_R = 32.0                           # island radius - MY ESTIMATE: corner towers reach r ≈ 31.1 m; range 31..36

# ---------- Bentuk padat (W2) ----------
# [AI] Claude, 2026-11-23: shape choices for the solid models - MY CHOICES, not in the brief unless marked;
#      reviewed by Nando: pending
# The island is a stack of cylinders: (y_bottom, y_top, radius_bottom, radius_top, colour key).
# Row 0 is the grassy plateau (top at y = 0); the rest is the rocky underbelly that tapers to a point,
# so the island reads as floating from any angle (brief §4.2 rule 2).
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
TAMPILKAN_PENANDA = False                # True = also draw the W1 wireframe markers on top (to check alignment)

# ---------- Dermaga, langit, awan (W3) ----------
# [AI] Claude, 2026-11-23: pier details, sky and clouds - MY CHOICES, not in the brief; reviewed by Nando: pending
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
# [AI] Claude, 2026-11-23: camera parameters (brief §4.3); reviewed by Nando: pending
KAMERA_TARGET = (0.0, 10.0, 0.0)         # orbit centre (brief §4.3)
KAMERA_R = 100.0                         # m, horizontal orbit radius; with KAMERA_H the distance is ≈ 106 m (brief ≈ 105 ◇)
KAMERA_H = 35.0                          # m, camera height above the target (my choice); range 10..60
KAMERA_SUDUT_AWAL = 0.6                  # rad, start angle (same as the lecturer's cam_ang)
KAMERA_PUTAR = 0.02                      # rad per frame while the arrow key is held (lecturer's value)
KAMERA_FOVY = 45.0                       # degrees, vertical field of view (lecturer's value)

def v3(p):
    """[AI] (x, y, z) -> rl.Vector3, like the lecturer's v3 in cloth_p16.py."""
    return rl.Vector3(float(p[0]), float(p[1]), float(p[2]))

# [DOSEN] -> [AI] cloth_p16.py main(): the lecturer's orbit camera (cam_ang changed by left/right, position on a
#      circle around the target) moved into a class so main.py can own one camera object; target, radius and
#      height changed for the island. Claude, 2026-11-23; reviewed by Nando: pending
class Kamera:
    def __init__(self):
        self.sudut = KAMERA_SUDUT_AWAL
        self.cam = rl.Camera3D(v3((0.0, 0.0, 0.0)), v3(KAMERA_TARGET), rl.Vector3(0, 1, 0), KAMERA_FOVY,
                               rl.CAMERA_PERSPECTIVE)
        self._letakkan()

    def update(self):
        """Global keys left/right (brief §7.4): rotate around the island, as in the lecturer's main()."""
        if rl.is_key_down(rl.KEY_LEFT): self.sudut -= KAMERA_PUTAR
        if rl.is_key_down(rl.KEY_RIGHT): self.sudut += KAMERA_PUTAR
        self._letakkan()

    def _letakkan(self):
        # position on a horizontal circle of radius KAMERA_R around the target, KAMERA_H above it
        tx, ty, tz = KAMERA_TARGET
        self.cam.position = v3((tx + KAMERA_R * math.sin(self.sudut), ty + KAMERA_H, tz + KAMERA_R * math.cos(self.sudut)))

# ---------- Penanda posisi (W1) ----------
# [AI] Claude, 2026-11-23: wireframe markers for every landmark, to check the coordinates before modelling
#      (W2 and W3 replace them with solid primitives). reviewed by Nando: pending
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
# [AI] Claude, 2026-11-23: solid models from raylib primitives (brief §4.2); everything is drawn from the constants
#      above, nothing is computed per frame except the draw calls. reviewed by Nando: pending
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
    """Main keep: a box for the walls and a gable roof (ridge along x) from 8 triangles."""
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

# [AI] Claude, 2026-11-23: W3 pier and clouds; reviewed by Nando: pending
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

# [AI] Codex, 2026-11-26: memuat model statis C14 memakai Raylib; review Nando tertunda.
def muat_model_dunia():
    """Muat model sesudah konteks grafis Raylib tersedia."""
    if not ASET_DUNIA.is_file():
        raise FileNotFoundError(f"Aset world GLB tidak ditemukan: {ASET_DUNIA}")
    model = rl.load_model(str(ASET_DUNIA))
    if not rl.is_model_valid(model):
        rl.unload_model(model)
        raise RuntimeError(f"Raylib gagal memuat aset world: {ASET_DUNIA}")
    return model


# [AI] Codex, 2026-11-26: latar langit untuk viewer dan main.py; review Nando tertunda.
def gambar_langit(model=None):
    """Gambar latar setelah begin_drawing() dan sebelum begin_mode_3d()."""
    rl.clear_background(LANGIT)
    if model is not None:
        rl.draw_rectangle_gradient_v(0, 0, rl.get_screen_width(), rl.get_screen_height(),
                                     LANGIT_PUNCAK, LANGIT_CAKRAWALA)


# [AI] Claude, 2026-11-23: W1-W3 draw order; reviewed by Nando: pending
# [AI] Codex, 2026-11-26: jalur GLB statis; review Nando tertunda.
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
# [AI] Claude, 2026-11-23: obstacle spheres for Module D, built from the landmark table (brief §4.4, §5.3
#      "MENARA = (centre, radius) obstacle spheres"). PROPOSAL for Faris: one sphere per building at half its
#      height, radius = its horizontal radius (keep: half the footprint diagonal). Module D's flee() adds its own
#      margin (jari + 6.0). Faris decides the final shape. reviewed by Nando: pending
MENARA = ([((x, MENARA_SUDUT_TINGGI / 2, z), MENARA_SUDUT_R) for x, z in MENARA_SUDUT]
          + [((x, GERBANG_TINGGI / 2, z), GERBANG_R) for x, z in GERBANG]
          + [((SPIRE_PUSAT[0], SPIRE_TINGGI / 2, SPIRE_PUSAT[1]), SPIRE_R),
             ((KEEP_PUSAT[0], KEEP_ATAP / 2, KEEP_PUSAT[1]), math.hypot(*KEEP_UKURAN) / 2)])

def get_landmarks():
    """Read-only coordinates for main.py to pass on (modules never import world_scene):
    Banner(TIANG=lm["tiang_bendera"]), pennant at lm["tiang_pennant"], Module A berth lm["tambat"],
    Module D obstacles lm["menara"] = list of ((x, y, z), radius)."""
    return {"tiang_bendera": TIANG_BENDERA, "tiang_pennant": TIANG_PENNANT, "tambat": TAMBAT,
            "menara": [tuple(m) for m in MENARA]}

# ---------- Program mandiri ----------
# [AI] Claude, 2026-11-23: standalone viewer (W1, W2: solids + optional markers); reviewed by Nando: pending
LEBAR, TINGGI = 1280, 720                # window size in pixels (assignment target 1280 x 720)

# [AI] Codex, 2026-11-26: viewer GLB dan pengelolaan umur model; review Nando tertunda.
def main(primitives=False):
    rl.init_window(LEBAR, TINGGI, "World Scene - Aether Castle Skyport")
    model = None
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
            if TAMPILKAN_PENANDA:
                gambar_penanda()
            rl.end_mode_3d()
            rl.draw_text(f"Aether Castle Skyport | {mode}", 20, 16, 20, rl.DARKGRAY)
            if TAMPILKAN_PENANDA:
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


# [AI] Codex, 2026-11-26: pilih tampilan pembanding W3 lewat argumen CLI; review Nando tertunda.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Viewer world Aether Castle Skyport")
    parser.add_argument("--primitives", action="store_true", help="Tampilkan world primitif W3 untuk perbandingan")
    main(primitives=parser.parse_args().primitives)
