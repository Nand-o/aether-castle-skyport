"""
Modul A - Kapal langit di jalur Catmull-Rom tertutup 3D (Aether Castle Skyport). PJ: Faris.
Dasar: catmull_rom_p7.py (Pertemuan 7, kode dosen). Sebagian kode baru dibuat dengan bantuan
asisten AI (Claude); fungsinya ditandai [AI] dan dicatat di tabel atribusi README.
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 3 (Interpolating Values):
         interpolasi spline, menghitung arc length, dan ease-in/ease-out.
Integrator: kinematik (tau maju dt / t_lap, posisi dihitung langsung dari kurva).

Jalankan:  pip install -r requirements.txt   lalu   python main.py
           (harness 3D mandiri untuk modul ini menyusul)
"""
import time
from collections import deque

import numpy as np
import pyray as rl

# ---------- Catmull-Rom (NumPy) ----------
# [DOSEN] catmull_rom_p7.py: matriks dan satu segmen, tidak diubah (rumusnya berlaku juga untuk titik 3D)
# p(u) = [u^3 u^2 u 1] . MCR . [P0 P1 P2 P3]^T   untuk segmen dari P1 ke P2, u dalam [0, 1]
MCR = 0.5 * np.array([[-1.0,  3.0, -3.0,  1.0],
                      [ 2.0, -5.0,  4.0, -1.0],
                      [-1.0,  0.0,  1.0,  0.0],
                      [ 0.0,  2.0,  0.0,  0.0]])

def catmull_rom(P0, P1, P2, P3, u):
    T = np.array([u**3, u**2, u, 1.0])
    return T @ MCR @ np.array([P0, P1, P2, P3])

# ---------- Rute kapal ----------
# [AI] 11 titik kunci rute tertutup mengelilingi pulau, dalam meter (+Y ke atas, -Z = utara),
#      dari tabel brief v3.2 §5.1. WP0 = tempat berlabuh di dermaga timur; WP4 = lewat dekat bendera.
WAYPOINTS = [
    (38.0,  4.5,   0.0),   # 0  berlabuh di dermaga
    (41.0,  9.0, -16.0),   # 1  naik meninggalkan dermaga
    (40.0, 18.0, -31.0),   # 2  timur laut
    (20.0, 30.0, -37.0),   # 3  mulai lintasan utara
    (-2.0, 34.0, -30.0),   # 4  lewat dekat bendera (~14 m dari tiang)
    (-24.0, 30.0, -36.0),  # 5  barat laut
    (-46.0, 21.0, -16.0),  # 6  barat
    (-44.0, 16.0,  16.0),  # 7  barat daya
    (-16.0, 14.0,  42.0),  # 8  selatan
    (18.0, 11.0,  44.0),   # 9  tenggara
    (41.0,  6.0,  18.0),   # 10 mendekati dermaga
]

# [AI] jalur TERTUTUP: n titik kunci = n segmen, t dalam [0, n). Empat titik tetangga diambil dengan
#      indeks modulo n, jadi tidak perlu titik hantu seperti di versi dosen (jalur terbuka).
def _segmen(K, t):
    """Kembalikan (G, u): 4 titik kontrol segmen ke-floor(t) berbentuk (4, 3) dan u lokal dalam [0, 1)."""
    n = len(K)
    i = int(t) % n
    u = t - int(t)
    G = K[[(i - 1) % n, i, (i + 1) % n, (i + 2) % n]]
    return G, u

def titik_jalur(K, t):
    """Posisi pada jalur tertutup di parameter global t (bagian bulat = segmen, sisanya = u)."""
    G, u = _segmen(np.asarray(K, dtype=float), t)
    return catmull_rom(G[0], G[1], G[2], G[3], u)      # [DOSEN] rumus satu segmen

# [AI] turunan P'(u) = [3u^2 2u 1 0] . MCR . G, dipakai untuk arah hadap kapal (Tantangan 3 P7).
#      Di titik kunci K_i hasilnya 1/2 (K_i+1 - K_i-1), sama dengan tangen Catmull-Rom di slide P7.
def tangen_jalur(K, t):
    """Turunan posisi terhadap t (belum dinormalisasi)."""
    G, u = _segmen(np.asarray(K, dtype=float), t)
    return np.array([3.0 * u * u, 2.0 * u, 1.0, 0.0]) @ MCR @ G

# ---------- Arc-length: tabel (t, s) ----------
# [DOSEN] catmull_rom_p7.py: bangun_tabel dan t_dari_s. Satu-satunya perubahan [KAMI]: jalur tertutup
#         punya n segmen untuk n titik kunci (dosen: len - 3 karena ada dua titik hantu).
def bangun_tabel(K, sampel_per_segmen=60):
    """Aproksimasi arc length dengan jumlah panjang segmen garis kecil."""
    nseg = len(K)
    ts = np.linspace(0.0, nseg, nseg * sampel_per_segmen + 1)
    pts = np.array([titik_jalur(K, t) for t in ts])
    panjang = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(panjang)])
    return ts, s / s[-1], s[-1]          # s dinormalisasi ke [0, 1]

def t_dari_s(ts, s_norm, s_target):
    """Invers tabel: cari parameter t yang jaraknya tepat s_target (interpolasi linier antar entri)."""
    return float(np.interp(s_target, s_norm, ts))

# ---------- Ease-in / ease-out (Parent): t' = ease(t) ----------
# [DOSEN] catmull_rom_p7.py: ease_sinus dan ease_parabola, tidak diubah
def ease_sinus(t):
    return (np.sin(t * np.pi - np.pi / 2.0) + 1.0) / 2.0

def ease_parabola(t, t1=0.3, t2=0.7):
    """Percepatan konstan sampai t1, kecepatan konstan t1..t2, perlambatan konstan t2..1."""
    v0 = 2.0 / (1.0 + t2 - t1)           # agar total jarak = 1
    if t < t1:
        return v0 * t * t / (2.0 * t1)
    if t <= t2:
        return v0 * t1 / 2.0 + v0 * (t - t1)
    return 1.0 - v0 * (1.0 - t) ** 2 / (2.0 * (1.0 - t2))

# ---------- Kapal ----------
T_LAP = 50.0          # s, waktu satu putaran (rute ~300 m -> rata-rata ~6 m/s)
T_LAP_MIN, T_LAP_MAX = 20.0, 150.0   # s, batas tombol [ dan ] (~15 m/s sampai ~2 m/s)
LANGKAH_T_LAP = 1.25  # tiap tekan [ atau ], waktu putaran dikali / dibagi 1,25
EASE_T1, EASE_T2 = 0.3, 0.7   # batas fase ease_parabola: percepat sampai t1, konstan, perlambat setelah t2
RADIUS_KAPAL = 4.5    # m, ukuran kapal yang dipakai modul lain (kawanan menjauh, bendera kena angin)
JENDELA_SIGMA = 2.0   # s, rentang waktu untuk menghitung simpangan kecepatan di HUD
BATAS_BOID = 10       # jumlah boid di depan kapal yang membuat kapal paling lambat (interaksi D->A)
LAMBAT_MAKS = 0.5     # kapal melambat paling banyak 50 %
TAU_HALUS = 1.0       # s, konstanta waktu: perubahan kecepatan dari kawanan dihaluskan supaya tidak tersentak

# [AI] kebalikan ease: s -> tau, lewat tabel (ease_parabola naik terus, jadi bisa dibalik dengan np.interp)
_TAU = np.linspace(0.0, 1.0, 2001)
_EASE = np.array([ease_parabola(x, EASE_T1, EASE_T2) for x in _TAU])

def balik_ease(s):
    return float(np.interp(s, _EASE, _TAU))

# ---------- Gambar ----------
# [DOSEN] V() dari catmull_rom_p7.py, diubah ke 3D: titik NumPy (x, y, z) -> rl.Vector3
def v3(p):
    return rl.Vector3(float(p[0]), float(p[1]), float(p[2]))

# [AI] warna dan segitiga dua sisi untuk kapal (bentuk dasar raylib saja, tanpa model 3D)
WARNA_LAMBUNG = rl.Color(146, 104, 66, 255)    # kayu, sama dengan dermaga di world_scene.py
WARNA_SAYAP = rl.Color(232, 222, 196, 255)     # kain layar
WARNA_SIRIP = rl.Color(150, 58, 44, 255)       # merah atap kastil
WARNA_LENTERA = rl.Color(255, 196, 64, 255)

def segitiga_dua_sisi(a, b, c, warna):
    """raylib hanya menggambar sisi depan segitiga, jadi digambar dua kali dengan urutan titik dibalik."""
    rl.draw_triangle_3d(v3(a), v3(b), v3(c), warna)
    rl.draw_triangle_3d(v3(a), v3(c), v3(b), warna)

# [AI] kapal mengikuti pola game loop P7: waktu tau (0..1) -> parameter t -> posisi di jalur
class Skyship:
    def __init__(self, waypoints=WAYPOINTS, t_lap=T_LAP):
        self.K = np.asarray(waypoints, dtype=float)
        self.ts, self.s_norm, self.panjang = bangun_tabel(self.K)
        self.t_lap = t_lap
        self.mode_arc = True                 # True: kecepatan konstan (tabel arc-length); False: t seragam
        self.pakai_ease = True               # True: pelan saat berangkat dan tiba di dermaga (WP0)
        self.tau = 0.0                       # waktu putaran ternormalisasi, 0 = 1 = di dermaga
        self.t = 0.0                         # parameter global jalur, 0..n
        self.s = 0.0                         # jarak tempuh ternormalisasi dalam satu putaran, 0..1
        self.step_ms = 0.0                   # lama update() terakhir, ms
        self.pos = titik_jalur(self.K, 0.0)
        self.vel = np.zeros(3)
        self.forward = self._arah(0.0)
        self.right, self.up = self._kanan_atas(self.forward)
        self.speed_scale = 1.0               # pengali kecepatan dari kawanan (D->A), 0,5..1
        self.n_boid_depan = 0                # jumlah boid di depan kapal, dikirim main.py dari Modul D
        self.kecepatan = 0.0                 # m/s
        self.simpangan_kecepatan = 0.0       # %, simpangan baku / rata-rata dalam JENDELA_SIGMA detik
        self._riwayat = deque()              # pasangan (dt, kecepatan) untuk simpangan
        # titik garis rute dan penanda jarak sama, dihitung sekali di sini (bukan tiap frame)
        n = len(self.K)
        self._garis = [v3(titik_jalur(self.K, t)) for t in np.linspace(0.0, n, 400 + 1)]
        self._penanda = [v3(titik_jalur(self.K, t_dari_s(self.ts, self.s_norm, i / 20))) for i in range(20)]

    def _arah(self, t):
        """Arah hadap = tangen kurva yang dinormalisasi (tetap terdefinisi walau kapal berhenti)."""
        d = tangen_jalur(self.K, t)
        return d / max(np.linalg.norm(d), 1e-9)

    @staticmethod
    def _kanan_atas(maju):
        """Vektor kanan (mendatar) dan atas kapal dari arah maju, terhadap sumbu atas dunia (0, 1, 0).
        Dipakai untuk menggambar sayap dan sirip. Rute tidak pernah tegak lurus (maks ~36 derajat)."""
        kanan = np.cross(maju, (0.0, 1.0, 0.0))
        kanan /= max(np.linalg.norm(kanan), 1e-9)
        return kanan, np.cross(kanan, maju)

    def update(self, dt, n_boid_depan=0):
        if dt <= 0.0:                                # frame pertama atau jeda: tidak ada yang bergerak
            return
        t0 = time.perf_counter()
        # interaksi D->A: makin banyak boid di depan, makin lambat (paling lambat 50 % pada 10 boid)
        self.n_boid_depan = n_boid_depan
        target = 1.0 - LAMBAT_MAKS * min(1.0, n_boid_depan / BATAS_BOID)
        self.speed_scale += (target - self.speed_scale) * min(1.0, dt / TAU_HALUS)
        self.tau = (self.tau + dt * self.speed_scale / self.t_lap) % 1.0
        # ease dihitung atas satu putaran penuh, dan WP0 adalah dermaga: kapal otomatis
        # melambat sampai berhenti di dermaga, lalu berangkat pelan lagi
        self.s = ease_parabola(self.tau, EASE_T1, EASE_T2) if self.pakai_ease else self.tau
        # [DOSEN] pola P7: dengan tabel, jarak s diubah jadi t; tanpa tabel, t = s * jumlah segmen
        self.t = t_dari_s(self.ts, self.s_norm, self.s) if self.mode_arc else self.s * len(self.K)
        baru = titik_jalur(self.K, self.t)
        self.vel = (baru - self.pos) / dt            # kecepatan dari selisih posisi (Tantangan 1 P7)
        self.pos = baru
        self.forward = self._arah(self.t)
        self.right, self.up = self._kanan_atas(self.forward)
        self._ukur_kecepatan(dt)
        self.step_ms = (time.perf_counter() - t0) * 1000.0

    # Tombol T dan E: tanpa penyesuaian, tau yang sama menunjuk ke titik lain di jalur dan kapal meloncat
    # (begitu juga di demo P7). Jadi setelah mode berganti, tau dihitung ulang dari posisi kapal sekarang.
    def toggle_mode(self):
        self.mode_arc = not self.mode_arc
        self._selaraskan_tau()

    def toggle_ease(self):
        self.pakai_ease = not self.pakai_ease
        self._selaraskan_tau()

    def handle_input(self):
        """Tombol Modul A. main.py cukup memanggil ini (jangan tangani T/E/[/] lagi di main.py).
        Dosen memakai M untuk mode; di sini T, karena M sudah dipakai Modul C."""
        if rl.is_key_pressed(rl.KEY_T): self.toggle_mode()
        if rl.is_key_pressed(rl.KEY_E): self.toggle_ease()
        if rl.is_key_pressed(rl.KEY_LEFT_BRACKET): self.lebih_lambat()
        if rl.is_key_pressed(rl.KEY_RIGHT_BRACKET): self.lebih_cepat()

    # Tombol [ dan ]: hanya kecepatan putaran yang berubah, tau tetap, jadi posisi kapal tidak meloncat
    def lebih_lambat(self):
        self.t_lap = min(self.t_lap * LANGKAH_T_LAP, T_LAP_MAX)

    def lebih_cepat(self):
        self.t_lap = max(self.t_lap / LANGKAH_T_LAP, T_LAP_MIN)

    def _selaraskan_tau(self):
        """Cari tau yang menghasilkan parameter t sekarang di mode yang baru (posisi kapal tidak berubah)."""
        s = float(np.interp(self.t, self.ts, self.s_norm)) if self.mode_arc else self.t / len(self.K)
        self.tau = balik_ease(s) if self.pakai_ease else s

    def _ukur_kecepatan(self, dt):
        """Kecepatan sekarang dan simpangannya selama JENDELA_SIGMA detik terakhir (angka untuk tombol T)."""
        self.kecepatan = float(np.linalg.norm(self.vel))
        self._riwayat.append((dt, self.kecepatan))
        while sum(d for d, _ in self._riwayat) > JENDELA_SIGMA:
            self._riwayat.popleft()
        v = np.array([x for _, x in self._riwayat])
        self.simpangan_kecepatan = float(100.0 * v.std() / v.mean()) if v.mean() > 1e-9 else 0.0

    def get_metrics(self):
        """Angka untuk HUD dan CSV (main.py)."""
        return {"ship_speed": self.kecepatan, "speed_sigma": self.simpangan_kecepatan,
                "t": self.t, "s": self.s, "path_length": float(self.panjang),
                "speed_scale": self.speed_scale, "boids_ahead": self.n_boid_depan,
                "mode_arc": self.mode_arc, "ease": self.pakai_ease, "step_ms": self.step_ms}

    def get_export_state(self):
        """Keadaan kapal untuk modul lain (salinan, jadi aman dibaca)."""
        return {"pos": self.pos.copy(), "vel": self.vel.copy(), "forward": self.forward.copy(),
                "radius": RADIUS_KAPAL}

    # ---------- gambar (dipanggil di antara begin_mode_3d dan end_mode_3d) ----------
    def render_3d(self):
        """Lambung sepanjang forward, sayap sepanjang right, sirip ke arah up: arah hadap dan
        kemiringan kapal langsung terbaca. Ujung sayap = RADIUS_KAPAL (4,5 m) dari pusat."""
        p, f, r, u = self.pos, self.forward, self.right, self.up
        rl.draw_cylinder_ex(v3(p - 4.0 * f), v3(p + 4.0 * f), 1.5, 0.6, 12, WARNA_LAMBUNG)   # buritan -> haluan
        for sisi in (1.0, -1.0):                                                          # sayap kanan, kiri
            segitiga_dua_sisi(p + 1.0 * f + sisi * r, p - 2.0 * f + sisi * r,
                              p - 2.5 * f + sisi * RADIUS_KAPAL * r, WARNA_SAYAP)
        segitiga_dua_sisi(p - 1.5 * f + u, p - 4.0 * f + u, p - 4.2 * f + 3.5 * u, WARNA_SIRIP)  # sirip ekor
        rl.draw_sphere(v3(p + 4.4 * f), 0.45, WARNA_LENTERA)                               # lentera di haluan

    def render_rute(self):
        """Pola gambar P7 dalam 3D: garis kurva, titik kunci (WP0 = dermaga, biru), dan 20 penanda
        berjarak sama (s = i/20, abu-abu). Penanda yang rapat sama rata menunjukkan tabel arc-length."""
        for a, b in zip(self._garis, self._garis[1:]):
            rl.draw_line_3d(a, b, rl.DARKBLUE)
        for q in self._penanda:
            rl.draw_sphere_ex(q, 0.35, 6, 8, rl.GRAY)
        for i, k in enumerate(self.K):
            rl.draw_sphere_ex(v3(k), 0.8, 8, 10, rl.BLUE if i == 0 else rl.ORANGE)


# ---------- Program mandiri ----------
# [DOSEN] -> [AI] main() catmull_rom_p7.py dijadikan harness 3D: satu dt seperti di main.py, kamera orbit,
#      HUD dari get_metrics() dan layar bantuan H. Pulau dan dermaga hanya pengganti world_scene.py.
LEBAR, TINGGI = 1280, 720                 # px, target tugas 1280 x 720
LANGIT = rl.Color(178, 214, 240, 255)     # sama dengan world_scene.py
KAMERA_TARGET = np.array([0.0, 15.0, 0.0])
KAMERA_R, KAMERA_H = 95.0, 40.0           # m, jarak mendatar dan tinggi kamera dari target
KAMERA_PUTAR = 1.2                        # rad/s saat panah kiri/kanan ditahan
BANTUAN = [("T", "arc-length <-> t seragam"), ("E", "ease-in/out on/off"),
           ("[  ]", "putaran lebih lambat / cepat"), ("N", "(tahan) kawanan tiruan, uji D->A"),
           ("<-  ->", "putar kamera"), ("P", "jeda"), ("R", "ulang dari dermaga"), ("H", "tutup bantuan")]

def gambar_pulau():
    """Lantai pulau (r 32 m, y = 0) dan dermaga timur (dek y = 1 m), supaya letak WP0 terbaca."""
    rl.draw_cylinder(v3((0.0, -1.5, 0.0)), 32.0, 32.0, 1.5, 24, rl.Color(96, 140, 72, 255))
    rl.draw_cylinder(v3((0.0, -20.0, 0.0)), 30.0, 0.0, 18.5, 24, rl.Color(122, 96, 70, 255))
    rl.draw_cube(v3((35.5, 0.75, 0.0)), 11.0, 0.5, 8.0, WARNA_LAMBUNG)

def gambar_kawanan_tiruan(kapal):
    """Pengganti Modul D: 10 bola gelap di depan kapal selama N ditahan (hanya tampilan)."""
    for i in range(BATAS_BOID):
        q = kapal.pos + (9.0 + 2.0 * (i % 5)) * kapal.forward + (3.0 * (i // 5) - 1.5) * kapal.right
        rl.draw_sphere_ex(v3(q), 0.6, 6, 8, rl.DARKGRAY)

def gambar_hud(kapal, paused):
    m = kapal.get_metrics()
    baris = [f"Mode (T): {'arc-length' if m['mode_arc'] else 't seragam'}   Ease (E): {'ON' if m['ease'] else 'OFF'}",
             f"Kecepatan: {m['ship_speed']:.2f} m/s   simpangan 2 s: {m['speed_sigma']:.1f} %",
             f"Waktu putaran ([ ]): {kapal.t_lap:.1f} s   panjang rute: {m['path_length']:.1f} m",
             f"t = {m['t']:.2f} / {len(kapal.K)}   s = {m['s']:.3f}",
             f"Boid di depan (N): {m['boids_ahead']}   skala laju: {m['speed_scale']:.2f}",
             f"update(): {m['step_ms']:.3f} ms" + ("   [JEDA]" if paused else "")]
    rl.draw_rectangle(10, 10, 500, 46 + 24 * len(baris), rl.fade(rl.RAYWHITE, 0.85))
    rl.draw_text("Modul A - kapal langit", 20, 18, 20, rl.DARKGRAY)
    for i, teks in enumerate(baris):
        rl.draw_text(teks, 20, 46 + 24 * i, 18, rl.DARKGRAY)
    rl.draw_fps(LEBAR - 100, 16)
    rl.draw_text("H = bantuan", 20, TINGGI - 28, 18, rl.GRAY)

def gambar_bantuan():
    x, y = LEBAR // 2 - 230, 200
    rl.draw_rectangle(x, y, 460, 40 + 30 * len(BANTUAN), rl.fade(rl.BLACK, 0.75))
    for i, (tombol, arti) in enumerate(BANTUAN):          # dua kolom, karena huruf raylib tidak sama lebar
        rl.draw_text(tombol, x + 24, y + 22 + 30 * i, 20, rl.GOLD)
        rl.draw_text(arti, x + 120, y + 22 + 30 * i, 20, rl.RAYWHITE)

def main():
    kapal = Skyship()
    sudut, paused, bantuan = 0.6, False, False
    rl.init_window(LEBAR, TINGGI, "Modul A - kapal langit (standalone)")
    rl.set_target_fps(60)
    cam = rl.Camera3D(v3(KAMERA_TARGET), v3(KAMERA_TARGET), rl.Vector3(0, 1, 0), 45.0, rl.CAMERA_PERSPECTIVE)
    while not rl.window_should_close():
        dt = min(rl.get_frame_time(), 1 / 30)       # satu dt untuk semua, dibatasi 1/30 s seperti main.py
        kapal.handle_input()                        # T, E, [ ]
        if rl.is_key_pressed(rl.KEY_P): paused = not paused
        if rl.is_key_pressed(rl.KEY_R): kapal = Skyship()
        if rl.is_key_pressed(rl.KEY_H): bantuan = not bantuan
        sudut += (rl.is_key_down(rl.KEY_RIGHT) - rl.is_key_down(rl.KEY_LEFT)) * KAMERA_PUTAR * dt
        cam.position = v3(KAMERA_TARGET + (KAMERA_R * np.sin(sudut), KAMERA_H, KAMERA_R * np.cos(sudut)))
        # kawanan tiruan: selama N ditahan, seolah 10 boid ada di depan kapal (di main.py angka ini dari Modul D)
        n_boid = BATAS_BOID if rl.is_key_down(rl.KEY_N) else 0
        if not paused:
            kapal.update(dt, n_boid)

        rl.begin_drawing()
        rl.clear_background(LANGIT)
        rl.begin_mode_3d(cam)
        gambar_pulau()
        kapal.render_rute()
        kapal.render_3d()
        if n_boid:
            gambar_kawanan_tiruan(kapal)
        rl.end_mode_3d()
        gambar_hud(kapal, paused)
        if bantuan:
            gambar_bantuan()
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
