"""
Pertemuan 16 - Simulasi Kain (Cloth Simulation) Berbasis Grid
Praktikum: menggabungkan ratusan partikel pegas-massa (P15) menjadi selembar kain 3D,
lalu membandingkannya dengan metode Verlet + constraint jarak (Jakobsen).
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 7.5;
         Provot (1995); Jakobsen (2001) "Advanced Character Physics".

Jalankan:  pip install raylib numpy   lalu   python cloth_p16.py
Kontrol :  1 tirai, 2 taplak di atas bola, M ganti metode (pegas / Verlet-constraint),
           W angin on/off, B pegas lentur on/off, P lepas satu sudut,
           kiri/kanan putar kamera, R ulang, SPASI jeda
"""
import math
import numpy as np
import pyray as rl

G = np.array([0.0, -9.81, 0.0])
SUBSTEPS = 8
DT = 1.0 / 60.0 / SUBSTEPS
N = 25                                   # partikel per sisi -> 625 partikel
SIZE = 2.0                               # sisi kain (m)
MASS = 1.0 / (N * N)                     # total 1 kg
K = {"struktural": 120.0, "geser": 30.0, "lentur": 8.0}
C_SPRING, C_AIR, C_WIND = 0.02, 0.01, 1.2
BALL_C, BALL_R = np.array([0.0, 0.6, 0.0]), 0.55

# ---------- Membangun grid kain ----------
def idx(r, q):
    return r * N + q

def build_cloth(scene):
    h = SIZE / (N - 1)
    P = np.zeros((N * N, 3))
    for r in range(N):
        for q in range(N):
            if scene == 1:   # tirai vertikal, baris 0 di atas
                P[idx(r, q)] = (-SIZE / 2 + q * h, 2.6 - r * h, 0.0)
            else:            # taplak horizontal di atas bola
                P[idx(r, q)] = (-SIZE / 2 + q * h, 1.6, -SIZE / 2 + r * h)
    si, sj, kind, group = [], [], [], []
    def add(a, b, kd, g):
        si.append(a); sj.append(b); kind.append(kd); group.append(g)
    # group: pegas dalam satu grup tidak berbagi partikel -> bisa dikoreksi serentak
    for r in range(N):
        for q in range(N):
            if q + 1 < N: add(idx(r, q), idx(r, q + 1), "struktural", 0 + q % 2)
            if r + 1 < N: add(idx(r, q), idx(r + 1, q), "struktural", 2 + r % 2)
            if q + 1 < N and r + 1 < N:
                add(idx(r, q), idx(r + 1, q + 1), "geser", 4 + r % 2)
                add(idx(r, q + 1), idx(r + 1, q), "geser", 6 + r % 2)
            if q + 2 < N: add(idx(r, q), idx(r, q + 2), "lentur", 8 + (q % 4) // 2)
            if r + 2 < N: add(idx(r, q), idx(r + 2, q), "lentur", 10 + (r % 4) // 2)
    si, sj, kind, group = np.array(si), np.array(sj), np.array(kind), np.array(group)
    pinned = np.zeros(N * N, bool)
    if scene == 1:
        pinned[[idx(0, q) for q in range(0, N, 4)] + [idx(0, N - 1)]] = True
    tris = []
    for r in range(N - 1):
        for q in range(N - 1):
            tris += [(idx(r, q), idx(r + 1, q), idx(r, q + 1)),
                     (idx(r + 1, q), idx(r + 1, q + 1), idx(r, q + 1))]
    return dict(scene=scene, pos=P, prev=P.copy(), vel=np.zeros_like(P), si=si, sj=sj, kind=kind, group=group,
                rest=np.linalg.norm(P[sj] - P[si], axis=1),
                kval=np.array([K[x] for x in kind]), pinned=pinned, tris=np.array(tris))

# ---------- Gaya ----------
def spring_forces(c, active):
    i, j = c["si"][active], c["sj"][active]
    d = c["pos"][j] - c["pos"][i]
    L = np.linalg.norm(d, axis=1)
    n = d / np.maximum(L, 1e-9)[:, None]
    v_rel = np.sum((c["vel"][j] - c["vel"][i]) * n, axis=1)
    f = (c["kval"][active] * (L - c["rest"][active]) + C_SPRING * v_rel)[:, None] * n
    F = np.zeros_like(c["pos"])
    np.add.at(F, i, f)
    np.add.at(F, j, -f)
    return F

def wind_forces(c, wind, vel):
    """Gaya aerodinamis per segitiga: F = C (n . (w - v)) n * luas, dibagi ke 3 titik."""
    t = c["tris"]
    p0, p1, p2 = c["pos"][t[:, 0]], c["pos"][t[:, 1]], c["pos"][t[:, 2]]
    cr = np.cross(p1 - p0, p2 - p0)                 # |cr| = 2 x luas
    area = 0.5 * np.linalg.norm(cr, axis=1)
    n = cr / np.maximum(2 * area, 1e-12)[:, None]
    v_avg = (vel[t[:, 0]] + vel[t[:, 1]] + vel[t[:, 2]]) / 3
    f = (C_WIND * np.sum((wind - v_avg) * n, axis=1) * area)[:, None] * n / 3
    F = np.zeros_like(c["pos"])
    for k in range(3):
        np.add.at(F, t[:, k], f)
    return F

def collide(c):
    """Proyeksikan titik yang menembus lantai/bola ke permukaan. Kembalikan mask kontak."""
    p = c["pos"]
    contact = p[:, 1] < 0.0                          # lantai
    p[contact, 1] = 0.0
    if c["scene"] == 2:                              # bola (hanya adegan 2)
        d = p - BALL_C
        dist = np.linalg.norm(d, axis=1)
        inside = dist < BALL_R + 0.02
        p[inside] = BALL_C + d[inside] / dist[inside, None] * (BALL_R + 0.02)
        contact |= inside
    return contact

# ---------- Metode A: pegas-massa + semi-implisit Euler ----------
def step_springs(c, dt, active, wind):
    F = MASS * G + spring_forces(c, active) - C_AIR * c["vel"]
    if wind is not None:
        F += wind_forces(c, wind, c["vel"])
    c["vel"] += F / MASS * dt
    c["vel"][c["pinned"]] = 0.0
    old = c["pos"].copy()
    c["pos"] += c["vel"] * dt
    contact = collide(c)
    c["vel"] = (c["pos"] - old) / dt                 # koreksi v setelah tabrakan
    c["vel"][contact] *= 0.8                         # gesekan sederhana
    c["prev"] = old

# ---------- Metode B: Verlet + constraint jarak (Jakobsen) ----------
def step_verlet(c, dt, active, wind, iters=12):
    vel = (c["pos"] - c["prev"]) / dt
    a = np.tile(G, (len(vel), 1))
    if wind is not None:
        a += wind_forces(c, wind, vel) / MASS
    new = c["pos"] + 0.99 * (c["pos"] - c["prev"]) + a * dt * dt   # 0.99 = redaman
    new[c["pinned"]] = c["pos"][c["pinned"]]
    c["prev"], c["pos"] = c["pos"], new
    w = (~c["pinned"]).astype(float)                 # bobot: titik paku tidak bergerak
    for _ in range(iters):                           # relaksasi Gauss-Seidel per grup
        for g in range(12):
            s = active & (c["group"] == g)
            i, j, rest = c["si"][s], c["sj"][s], c["rest"][s]
            d = c["pos"][j] - c["pos"][i]
            L = np.linalg.norm(d, axis=1)
            ws = np.maximum(w[i] + w[j], 1e-9)
            corr = ((L - rest) / np.maximum(L, 1e-9) / ws)[:, None] * d
            c["pos"][i] += corr * w[i, None]         # geser kedua ujung agar
            c["pos"][j] -= corr * w[j, None]         # panjang kembali = rest
        contact = collide(c)
    # gesekan sederhana: titik yang menyentuh permukaan kehilangan sebagian kecepatan
    c["prev"][contact] += 0.8 * (c["pos"][contact] - c["prev"][contact])
    c["vel"] = (c["pos"] - c["prev"]) / dt

def stretch(c):
    """Regangan pegas struktural: (rata-rata, maksimum)."""
    s = c["kind"] == "struktural"
    e = np.linalg.norm(c["pos"][c["sj"][s]] - c["pos"][c["si"][s]], axis=1) / c["rest"][s] - 1.0
    return float(np.mean(np.abs(e))), float(np.max(e))

def wind_at(t):
    return np.array([1.5, 0.0, 4.0 + 2.0 * math.sin(1.3 * t)])   # angin berhembus naik-turun

# ---------- Tampilan 3D ----------
def v3(p):
    return rl.Vector3(float(p[0]), float(p[1]), float(p[2]))

def main():
    scene, method, use_wind, use_bend, paused = 1, "pegas", False, True, False
    cloth, t, cam_ang = build_cloth(1), 0.0, 0.6
    rl.init_window(1000, 680, "P16 - Simulasi kain")
    rl.set_target_fps(60)
    cam = rl.Camera3D(rl.Vector3(0, 2.0, 5.2), rl.Vector3(0, 1.3, 0), rl.Vector3(0, 1, 0), 45.0,
                      rl.CAMERA_PERSPECTIVE)
    while not rl.window_should_close():
        if rl.is_key_pressed(rl.KEY_ONE): scene, cloth = 1, build_cloth(1)
        if rl.is_key_pressed(rl.KEY_TWO): scene, cloth = 2, build_cloth(2)
        if rl.is_key_pressed(rl.KEY_R): cloth = build_cloth(scene)
        if rl.is_key_pressed(rl.KEY_M):
            method = "verlet" if method == "pegas" else "pegas"
            cloth["prev"] = cloth["pos"] - cloth["vel"] * DT * SUBSTEPS
        if rl.is_key_pressed(rl.KEY_W): use_wind = not use_wind
        if rl.is_key_pressed(rl.KEY_B): use_bend = not use_bend
        if rl.is_key_pressed(rl.KEY_P): cloth["pinned"][idx(0, N - 1)] = False
        if rl.is_key_pressed(rl.KEY_SPACE): paused = not paused
        if rl.is_key_down(rl.KEY_LEFT): cam_ang -= 0.02
        if rl.is_key_down(rl.KEY_RIGHT): cam_ang += 0.02
        cam.position = rl.Vector3(5.2 * math.sin(cam_ang), 2.0, 5.2 * math.cos(cam_ang))

        active = np.ones(len(cloth["si"]), bool) if use_bend else (cloth["kind"] != "lentur")
        if not paused:
            if method == "pegas":                       # banyak substep kecil
                for _ in range(SUBSTEPS):
                    t += DT
                    step_springs(cloth, DT, active, wind_at(t) if use_wind else None)
            else:                                       # satu langkah besar per frame
                t += DT * SUBSTEPS
                step_verlet(cloth, DT * SUBSTEPS, active, wind_at(t) if use_wind else None)
            if not np.all(np.isfinite(cloth["pos"])):
                cloth = build_cloth(scene)

        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        rl.begin_mode_3d(cam)
        rl.draw_grid(10, 0.5)
        if scene == 2:
            rl.draw_sphere(v3(BALL_C), BALL_R, rl.Color(200, 205, 220, 255))
        P = cloth["pos"]
        for r in range(N - 1):                          # gambar sebagai segitiga dua sisi
            for q in range(N - 1):
                a, b, c2, d = P[idx(r, q)], P[idx(r + 1, q)], P[idx(r, q + 1)], P[idx(r + 1, q + 1)]
                col = rl.Color(242, 140, 40, 255) if (r // 3 + q // 3) % 2 else rl.Color(20, 33, 61, 255)
                for tri in ((a, b, c2), (b, d, c2)):
                    rl.draw_triangle_3d(v3(tri[0]), v3(tri[1]), v3(tri[2]), col)
                    rl.draw_triangle_3d(v3(tri[0]), v3(tri[2]), v3(tri[1]), col)
        for p in P[cloth["pinned"]]:
            rl.draw_sphere(v3(p), 0.03, rl.BLACK)
        rl.end_mode_3d()
        name = "Pegas-massa + semi-implisit Euler" if method == "pegas" else "Verlet + constraint jarak"
        rl.draw_text(("Tirai" if scene == 1 else "Taplak di atas bola") + f"  |  {name}", 20, 16, 20, rl.DARKGRAY)
        rl.draw_text(f"{N * N} partikel, {int(active.sum())} pegas   angin = {'on' if use_wind else 'off'}"
                     f"   lentur = {'on' if use_bend else 'off'}", 20, 44, 18, rl.GRAY)
        e_avg, e_max = stretch(cloth)
        rl.draw_text(f"regangan rata-rata = {e_avg * 100:.1f} %   maks = {e_max * 100:.1f} %",
                     20, 68, 18, rl.MAROON)
        rl.draw_text("1/2 adegan | M metode | W angin | B lentur | P lepas sudut | kiri/kanan kamera | R ulang",
                     20, 680 - 26, 16, rl.GRAY)
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
