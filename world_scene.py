# [AI] Claude, 2026-11-23: module docstring (W1); reviewed by Nando: pending
"""
world_scene.py - dunia statis Aether Castle Skyport: pulau, kastil, menara, tiang, dermaga, langit, kamera.
PJ: Nando. Hanya primitif raylib (kubus, silinder, kerucut, bola); tidak ada kode simulasi di sini.
Koordinat dari tabel landmark brief §4.4: +Y ke atas, +X timur, -Z utara, 1 unit = 1 m, y = 0 = lantai pulau.
Nilai bertanda ◇ dibawa dari brief v2 dan harus dicek dengan prototipe; perubahan diumumkan ke semua PJ.

W1: konstanta landmark + kamera orbit + penampil penanda (wireframe) untuk mengecek posisi sebelum dimodelkan.

Jalankan:  python world_scene.py
Kontrol :  kiri/kanan putar kamera
"""
import math
import pyray as rl

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

# ---------- Program mandiri ----------
# [AI] Claude, 2026-11-23: standalone viewer for W1; reviewed by Nando: pending
LEBAR, TINGGI = 1280, 720                # window size in pixels (assignment target 1280 x 720)

def main():
    rl.init_window(LEBAR, TINGGI, "world_scene - penanda landmark (W1)")
    rl.set_target_fps(60)
    kamera = Kamera()
    while not rl.window_should_close():
        kamera.update()
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        rl.begin_mode_3d(kamera.cam)
        rl.draw_grid(100, 1.0)                       # 1 m grid, 100 m wide, on y = 0
        gambar_penanda()
        rl.end_mode_3d()
        rl.draw_text("world_scene W1 - penanda landmark (brief §4.4)", 20, 16, 20, rl.DARKGRAY)
        rl.draw_text("merah = TIANG bendera   oranye = TIANG pennant   biru = tambat (WP0)   hijau = tepi pulau",
                     20, 44, 18, rl.GRAY)
        rl.draw_text(f"kamera: sudut {math.degrees(kamera.sudut) % 360:.0f} deg, "
                     f"jarak {math.hypot(KAMERA_R, KAMERA_H):.0f} m", 20, 70, 18, rl.GRAY)
        rl.draw_text("kiri/kanan = putar kamera", 20, TINGGI - 28, 18, rl.GRAY)
        rl.draw_fps(LEBAR - 100, 16)
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
