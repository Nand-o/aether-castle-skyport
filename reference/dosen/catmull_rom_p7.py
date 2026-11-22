"""
Pertemuan 7 - Kurva Catmull-Rom Splines & Kontrol Kecepatan (Arc-Length Parameterization)
Praktikum: objek bergerak melewati titik kunci dengan kecepatan konstan, dengan opsi ease-in/ease-out.
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 3 (Interpolating Values):
         interpolasi spline, menghitung arc length, dan ease-in/ease-out.

Jalankan:  pip install raylib numpy   lalu   python catmull_rom_p7.py
Kontrol :  geser titik kunci dengan mouse | M = mode t seragam / arc-length | E = ease-in/ease-out on/off
"""
import numpy as np
import pyray as rl

# ---------- Catmull-Rom (NumPy) ----------
# p(u) = [u^3 u^2 u 1] . MCR . [P0 P1 P2 P3]^T   untuk segmen dari P1 ke P2, u dalam [0, 1]
MCR = 0.5 * np.array([[-1.0,  3.0, -3.0,  1.0],
                      [ 2.0, -5.0,  4.0, -1.0],
                      [-1.0,  0.0,  1.0,  0.0],
                      [ 0.0,  2.0,  0.0,  0.0]])

def catmull_rom(P0, P1, P2, P3, u):
    T = np.array([u**3, u**2, u, 1.0])
    return T @ MCR @ np.array([P0, P1, P2, P3])

def tambah_titik_hantu(K):
    """Tambah titik hantu di kedua ujung agar segmen pertama & terakhir punya tetangga."""
    K = np.asarray(K, dtype=float)
    return np.vstack([2 * K[0] - K[1], K, 2 * K[-1] - K[-2]])

def titik_jalur(Kp, t):
    """t dalam [0, jumlah_segmen]; bagian bulat = nomor segmen, sisanya = u lokal."""
    nseg = len(Kp) - 3
    i = min(int(t), nseg - 1)
    return catmull_rom(Kp[i], Kp[i + 1], Kp[i + 2], Kp[i + 3], t - i)

# ---------- Arc-length: tabel (t, s) ----------
def bangun_tabel(Kp, sampel_per_segmen=60):
    """Aproksimasi arc length dengan jumlah panjang segmen garis kecil."""
    nseg = len(Kp) - 3
    ts = np.linspace(0.0, nseg, nseg * sampel_per_segmen + 1)
    pts = np.array([titik_jalur(Kp, t) for t in ts])
    panjang = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(panjang)])
    return ts, s / s[-1], s[-1]          # s dinormalisasi ke [0, 1]

def t_dari_s(ts, s_norm, s_target):
    """Invers tabel: cari parameter t yang jaraknya tepat s_target (interpolasi linier antar entri)."""
    return float(np.interp(s_target, s_norm, ts))

# ---------- Ease-in / ease-out (Parent): t' = ease(t) ----------
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

# ---------- Gambar ----------
def V(p):
    return rl.Vector2(float(p[0]), float(p[1]))

def main():
    K = np.array([[100.0, 480.0], [180.0, 240.0], [330.0, 200.0],
                  [650.0, 215.0], [700.0, 440.0], [740.0, 480.0]])
    Kp = tambah_titik_hantu(K)
    ts, s_norm, panjang = bangun_tabel(Kp)
    nseg = len(Kp) - 3
    mode_arc, pakai_ease = True, False
    ditarik, tau = -1, 0.0

    rl.init_window(800, 600, "P7 - Catmull-Rom & Kontrol Kecepatan")
    rl.set_target_fps(60)
    while not rl.window_should_close():
        dt = rl.get_frame_time()
        tau = (tau + dt / 6.0) % 1.0                    # waktu animasi 6 detik, dinormalisasi
        if rl.is_key_pressed(rl.KEY_M): mode_arc = not mode_arc
        if rl.is_key_pressed(rl.KEY_E): pakai_ease = not pakai_ease

        mp = rl.get_mouse_position()
        mouse = np.array([mp.x, mp.y])
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            jarak = np.linalg.norm(K - mouse, axis=1)
            if jarak.min() < 14:
                ditarik = int(jarak.argmin())
        if rl.is_mouse_button_released(rl.MOUSE_BUTTON_LEFT):
            ditarik = -1
        if ditarik >= 0:
            K[ditarik] = mouse
            Kp = tambah_titik_hantu(K)
            ts, s_norm, panjang = bangun_tabel(Kp)       # titik kunci berubah -> hitung ulang tabel

        # waktu -> (ease) -> jarak ternormalisasi -> parameter t -> posisi
        s = ease_sinus(tau) if pakai_ease else tau
        t = t_dari_s(ts, s_norm, s) if mode_arc else s * nseg
        pos = titik_jalur(Kp, t)

        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        kurva = [titik_jalur(Kp, x) for x in np.linspace(0.0, nseg, 200)]
        for i in range(len(kurva) - 1):
            rl.draw_line_ex(V(kurva[i]), V(kurva[i + 1]), 3, rl.DARKBLUE)
        for i in range(0, 11):                           # penanda jarak sama (s = i/10)
            q = titik_jalur(Kp, t_dari_s(ts, s_norm, i / 10.0))
            rl.draw_circle_v(V(q), 4, rl.LIGHTGRAY)
        for i, p in enumerate(K):
            rl.draw_circle_v(V(p), 8, rl.ORANGE)
            rl.draw_text(f"K{i}", int(p[0]) + 10, int(p[1]) - 24, 18, rl.DARKGRAY)
        rl.draw_circle_v(V(pos), 11, rl.MAROON)
        rl.draw_text(f"Mode: {'arc-length (kecepatan konstan)' if mode_arc else 't seragam'}", 20, 20, 20, rl.DARKGRAY)
        rl.draw_text(f"Ease-in/out: {'ON' if pakai_ease else 'OFF'}   Panjang jalur: {panjang:.0f} px", 20, 48, 18, rl.GRAY)
        rl.draw_text("M: ganti mode | E: ease | geser titik kunci dengan mouse", 20, 570, 18, rl.GRAY)
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
