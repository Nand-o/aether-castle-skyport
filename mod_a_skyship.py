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
        self.pos = titik_jalur(self.K, 0.0)
        self.vel = np.zeros(3)
        self.forward = self._arah(0.0)
        self.speed_scale = 1.0               # pengali kecepatan dari kawanan (D->A), 0,5..1
        self.n_boid_depan = 0                # jumlah boid di depan kapal, dikirim main.py dari Modul D
        self.kecepatan = 0.0                 # m/s
        self.simpangan_kecepatan = 0.0       # %, simpangan baku / rata-rata dalam JENDELA_SIGMA detik
        self._riwayat = deque()              # pasangan (dt, kecepatan) untuk simpangan

    def _arah(self, t):
        """Arah hadap = tangen kurva yang dinormalisasi (tetap terdefinisi walau kapal berhenti)."""
        d = tangen_jalur(self.K, t)
        return d / max(np.linalg.norm(d), 1e-9)

    def update(self, dt, n_boid_depan=0):
        if dt <= 0.0:                                # frame pertama atau jeda: tidak ada yang bergerak
            return
        # interaksi D->A: makin banyak boid di depan, makin lambat (paling lambat 50 % pada 10 boid)
        self.n_boid_depan = n_boid_depan
        target = 1.0 - LAMBAT_MAKS * min(1.0, n_boid_depan / BATAS_BOID)
        self.speed_scale += (target - self.speed_scale) * min(1.0, dt / TAU_HALUS)
        self.tau = (self.tau + dt * self.speed_scale / self.t_lap) % 1.0
        # ease dihitung atas satu putaran penuh, dan WP0 adalah dermaga: kapal otomatis
        # melambat sampai berhenti di dermaga, lalu berangkat pelan lagi
        s = ease_parabola(self.tau, EASE_T1, EASE_T2) if self.pakai_ease else self.tau
        # [DOSEN] pola P7: dengan tabel, jarak s diubah jadi t; tanpa tabel, t = s * jumlah segmen
        self.t = t_dari_s(self.ts, self.s_norm, s) if self.mode_arc else s * len(self.K)
        baru = titik_jalur(self.K, self.t)
        self.vel = (baru - self.pos) / dt            # kecepatan dari selisih posisi (Tantangan 1 P7)
        self.pos = baru
        self.forward = self._arah(self.t)
        self._ukur_kecepatan(dt)

    # Tombol T dan E: tanpa penyesuaian, tau yang sama menunjuk ke titik lain di jalur dan kapal meloncat
    # (begitu juga di demo P7). Jadi setelah mode berganti, tau dihitung ulang dari posisi kapal sekarang.
    def toggle_mode(self):
        self.mode_arc = not self.mode_arc
        self._selaraskan_tau()

    def toggle_ease(self):
        self.pakai_ease = not self.pakai_ease
        self._selaraskan_tau()

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

    def get_export_state(self):
        """Keadaan kapal untuk modul lain (salinan, jadi aman dibaca)."""
        return {"pos": self.pos.copy(), "vel": self.vel.copy(), "forward": self.forward.copy(),
                "radius": RADIUS_KAPAL}
