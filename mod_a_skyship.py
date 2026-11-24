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

# [AI] kapal mengikuti pola game loop P7: waktu tau (0..1) -> parameter t -> posisi di jalur
class Skyship:
    def __init__(self, waypoints=WAYPOINTS, t_lap=T_LAP):
        self.K = np.asarray(waypoints, dtype=float)
        self.ts, self.s_norm, self.panjang = bangun_tabel(self.K)
        self.t_lap = t_lap
        self.tau = 0.0                       # waktu putaran ternormalisasi, 0 = 1 = di dermaga
        self.t = 0.0                         # parameter global jalur, 0..n
        self.pos = titik_jalur(self.K, 0.0)

    def update(self, dt):
        self.tau = (self.tau + dt / self.t_lap) % 1.0
        self.t = self.tau * len(self.K)
        self.pos = titik_jalur(self.K, self.t)
