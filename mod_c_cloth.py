# [DOSEN] -> [AI] cloth_p16.py docstring, rewritten for the banner (C1-C5). Claude, 2026-11-23; reviewed by Nando: pending
"""
Modul C - Bendera raksasa di menara utara (Aether Castle Skyport). PJ: Nando.
Dasar: cloth_p16.py (Pertemuan 16, kode dosen): pegas-massa (P15) dan Verlet + constraint jarak (Jakobsen).
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 7.5;
         Provot (1995); Jakobsen (2001) "Advanced Character Physics".
Integrator: Verlet (redaman 0,99) + relaksasi Gauss-Seidel 12 grup, 4 substep x 2 iterasi per frame;
            mode pegas: semi-implisit Euler dengan langkah <= 1/480 s. Semua memakai dt bersama dari main.py.

Jalankan:  pip install -r requirements.txt   lalu   python mod_c_cloth.py
Kontrol :  M ganti metode (Verlet-constraint / pegas), + / - iterasi Verlet, B pegas lentur on/off,
           W angin kencang on/off, F1 interaksi A->C (kapal tiruan) on/off, kiri/kanan putar kamera,
           R ulang, P / SPASI jeda, H bantuan
"""
import math
import time
import numpy as np
import pyray as rl

# [DOSEN] cloth_p16.py: gravity and the lecturer's step size, unchanged.
#         Since C2, DT is the LARGEST step spring mode may take (the step itself comes from the shared dt).
G = np.array([0.0, -9.81, 0.0])
SUBSTEPS = 8
DT = 1.0 / 60.0 / SUBSTEPS

# [AI] Claude, 2026-11-22: banner size and position (brief §5.2, §4.4), replacing the lecturer's square
#      N x N curtain; reviewed by Nando: pending
NR, NC = 14, 20                          # particles down the pole x out from the pole; range 5..20 x 8..30 (more = slower)
CELL = 0.5                               # m, rest length of one structural edge -> banner 9.5 x 6.5 m; range 0.3..0.8 (◇)
TIANG = np.array([0.0, 37.5, -16.0])     # m, top of the flagpole (brief §4.4 ◇); must match world_scene.py
MASS = 0.1                               # kg per particle (lecturer: 1 kg spread over the whole cloth); 280 x 0.1 = 28 kg
# [AI] Claude, 2026-11-22: Verlet stepping (brief §5.2, bonus §12); reviewed by Nando: pending
SUBSTEPS_VERLET = 4                      # Verlet steps per frame, each dt/4; range 1..8 (lecturer: 1)
ITERS_VERLET = 2                         # Gauss-Seidel passes per step; range 1..20, keys + / - (lecturer: 12)
MODE_AWAL = "verlet"                     # method at start: "verlet" or "pegas", key M (lecturer started in "pegas")
# [AI] Claude, 2026-11-23: ship wake for interaction A->C (brief §5.2, §6); reviewed by Nando: pending
R_KAPAL = 25.0                           # m, distance at which the ship's wake fades to zero; range 10..40
GAIN_KAPAL = 2.0                         # wake strength: wind = GAIN x ship velocity at the ship; range 0..4 (0 = off)
# [DOSEN] -> [AI] cloth_p16.py K: the lecturer's ratio 15 : 3.75 : 1 kept, values raised for 0.1-kg particles
#      (brief §5.2). Used by spring mode only. Claude, 2026-11-22; reviewed by Nando: pending
K = {"struktural": 6000.0, "geser": 1500.0, "lentur": 400.0}   # N/m; brief §10: 1500 = rubbery, 20000 blew up
# [DOSEN] cloth_p16.py: spring damping, air drag and wind coefficient, unchanged
C_SPRING, C_AIR, C_WIND = 0.02, 0.01, 1.2
# [DOSEN] cloth_p16.py: ball of the lecturer's scene 2, unchanged. Kept only because collide() reads it;
#         the banner is always scene 1, so the ball never exists here.
BALL_C, BALL_R = np.array([0.0, 0.6, 0.0]), 0.55

# ---------- Membangun grid kain ----------
# [DOSEN] -> [AI] cloth_p16.py idx: row-major index; the row length nc is now an argument (default NC)
#      so a second, smaller banner can use it too. Claude, 2026-11-22; reviewed by Nando: pending
def idx(r, q, nc=NC):
    return r * nc + q

# [DOSEN] -> [AI] cloth_p16.py build_cloth: one nr x nc banner hanging from `tiang` with the whole column 0 pinned
#      (Latihan 2 P16, flag on a pole). Size and position are arguments so the Tier 2 pennant can reuse it.
#      The spring list and the 12-group formula are the lecturer's; only the loop bounds changed.
#      Claude, 2026-11-22; reviewed by Nando: pending
def build_cloth(nr=NR, nc=NC, cell=CELL, tiang=TIANG):
    tiang = np.asarray(tiang, dtype=float)
    P = np.zeros((nr * nc, 3))
    for r in range(nr):
        for q in range(nc):
            # row r goes down the pole, column q streams west (-X); the banner starts flat in the XY plane
            P[idx(r, q, nc)] = tiang + (-q * cell, -r * cell, 0.0)
    si, sj, kind, group = [], [], [], []
    def add(a, b, kd, g):
        si.append(a); sj.append(b); kind.append(kd); group.append(g)
    # group: pegas dalam satu grup tidak berbagi partikel -> bisa dikoreksi serentak
    for r in range(nr):
        for q in range(nc):
            if q + 1 < nc: add(idx(r, q, nc), idx(r, q + 1, nc), "struktural", 0 + q % 2)
            if r + 1 < nr: add(idx(r, q, nc), idx(r + 1, q, nc), "struktural", 2 + r % 2)
            if q + 1 < nc and r + 1 < nr:
                add(idx(r, q, nc), idx(r + 1, q + 1, nc), "geser", 4 + r % 2)
                add(idx(r, q + 1, nc), idx(r + 1, q, nc), "geser", 6 + r % 2)
            if q + 2 < nc: add(idx(r, q, nc), idx(r, q + 2, nc), "lentur", 8 + (q % 4) // 2)
            if r + 2 < nr: add(idx(r, q, nc), idx(r + 2, q, nc), "lentur", 10 + (r % 4) // 2)
    si, sj, kind, group = np.array(si), np.array(sj), np.array(kind), np.array(group)
    pinned = np.zeros(nr * nc, bool)
    pinned[[idx(r, 0, nc) for r in range(nr)]] = True      # the whole column 0 is tied to the pole
    tris = []
    for r in range(nr - 1):
        for q in range(nc - 1):
            tris += [(idx(r, q, nc), idx(r + 1, q, nc), idx(r, q + 1, nc)),
                     (idx(r + 1, q, nc), idx(r + 1, q + 1, nc), idx(r, q + 1, nc))]
    # scene = 1: collide() reads this key; only the lecturer's scene 2 has a ball
    return dict(scene=1, pos=P, prev=P.copy(), vel=np.zeros_like(P), si=si, sj=sj, kind=kind, group=group,
                rest=np.linalg.norm(P[sj] - P[si], axis=1),
                kval=np.array([K[x] for x in kind]), pinned=pinned, tris=np.array(tris))

# ---------- Gaya ----------
# [DOSEN] cloth_p16.py: spring_forces, unchanged
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

# [DOSEN] cloth_p16.py: wind_forces, unchanged (it also accepts a per-triangle wind of shape (T, 3))
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

# [DOSEN] cloth_p16.py: collide, unchanged. Kept on purpose so step_springs and step_verlet stay unchanged;
#         its floor is y = 0 and the banner hangs far above it, and the ball only exists in scene 2.
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
# [DOSEN] cloth_p16.py: step_springs, unchanged
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
# [DOSEN] cloth_p16.py: step_verlet, unchanged
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

# [DOSEN] cloth_p16.py: stretch, unchanged
def stretch(c):
    """Regangan pegas struktural: (rata-rata, maksimum)."""
    s = c["kind"] == "struktural"
    e = np.linalg.norm(c["pos"][c["sj"][s]] - c["pos"][c["si"][s]], axis=1) / c["rest"][s] - 1.0
    return float(np.mean(np.abs(e))), float(np.max(e))

# [DOSEN] cloth_p16.py: wind_at, unchanged (main.py's angin_global replaces it in the integrated program)
def wind_at(t):
    return np.array([1.5, 0.0, 4.0 + 2.0 * math.sin(1.3 * t)])   # angin berhembus naik-turun

# ---------- Interaksi A -> C ----------
# [AI] Claude, 2026-11-23: wind_ship, typed in from brief §5.2 (formula from Faris's prototype `angin_kapal`,
#      [KAMI]); named like the lecturer's wind_forces. reviewed by Nando: pending
def wind_ship(c, kapal, R=R_KAPAL, gain=GAIN_KAPAL):
    """Extra wind (T, 3) on every triangle from the passing ship: gain * f(d) * ship velocity,
    with f = (1 - (d/R)^2)^2 -> 1 at the ship, falls smoothly to 0 at distance R (and stays 0 beyond)."""
    t = c["tris"]
    pusat = (c["pos"][t[:, 0]] + c["pos"][t[:, 1]] + c["pos"][t[:, 2]]) / 3     # triangle centres (T, 3)
    d = np.linalg.norm(pusat - kapal["pos"], axis=1)                            # distance to the ship (T,)
    f = np.clip(1.0 - (d / R) ** 2, 0.0, None) ** 2                             # smooth falloff 1 -> 0
    return gain * f[:, None] * kapal["vel"]

# ---------- Tampilan 3D ----------
# [DOSEN] cloth_p16.py: v3, unchanged
def v3(p):
    return rl.Vector3(float(p[0]), float(p[1]), float(p[2]))

# ---------- Kelas modul (antarmuka tim, brief §7.2) ----------
# [DOSEN] -> [AI] cloth_p16.py: the lecturer's two banner colours, now created once instead of for every quad
#      every frame (C5). Claude, 2026-11-23; reviewed by Nando: pending
WARNA_A = rl.Color(242, 140, 40, 255)    # orange
WARNA_B = rl.Color(20, 33, 61, 255)      # dark blue

# [AI] Claude, 2026-11-22: Module C class with the team interface. It only wraps the lecturer's functions
#      above (the physics itself is unchanged) and adds the shared dt and substeps x iterations.
#      reviewed by Nando: pending
class Banner:
    def __init__(self, NR=NR, NC=NC, TIANG=TIANG, CELL=CELL):
        self.NR, self.NC, self.CELL = NR, NC, CELL
        self.TIANG = np.asarray(TIANG, dtype=float)
        self.mode = MODE_AWAL
        self.substeps = SUBSTEPS_VERLET
        self.iters = ITERS_VERLET
        self.bending = True
        self.resets = 0                      # NaN auto-resets so far (HUD)
        self.dt_terakhir = 1.0 / 60.0        # last shared dt; needed when M switches to Verlet
        self.step_ms = 0.0                   # [AI] C3: cost of update() in ms, smoothed (HUD, report)
        self.angin_kapal_maks = 0.0          # [AI] C4: strongest ship wind on any triangle this frame (m/s)
        self.reset()

    def reset(self):
        """Rebuild the banner in its start pose (key R)."""
        self.c = build_cloth(self.NR, self.NC, self.CELL, self.TIANG)
        # both constraint masks are built once here, not every frame
        self.semua = np.ones(len(self.c["si"]), bool)
        self.tanpa_lentur = self.c["kind"] != "lentur"
        # [AI] C3: the free (flying) edge = last column; its mean speed is the "tip speed" on the HUD
        self.ujung = np.array([idx(r, self.NC - 1, self.NC) for r in range(self.NR)])

    def handle_input(self):
        """Module C keys only (brief §7.4): M, B, + and -. W (strong wind) belongs to main.py / the harness."""
        if rl.is_key_pressed(rl.KEY_M):
            self.mode = "verlet" if self.mode == "pegas" else "pegas"
            # [DOSEN] -> [AI] the lecturer's switch line, but with OUR Verlet step dt / substeps instead of 1/60:
            #      Verlet stores velocity only as pos - prev, so prev must be one Verlet step behind
            self.c["prev"] = self.c["pos"] - self.c["vel"] * (self.dt_terakhir / self.substeps)
        if rl.is_key_pressed(rl.KEY_B):
            self.bending = not self.bending
        if rl.is_key_pressed(rl.KEY_EQUAL) or rl.is_key_pressed(rl.KEY_KP_ADD):
            self.iters = min(20, self.iters + 1)
        if rl.is_key_pressed(rl.KEY_MINUS) or rl.is_key_pressed(rl.KEY_KP_SUBTRACT):
            self.iters = max(1, self.iters - 1)      # never 0: step_verlet needs at least one pass (else it crashes)

    def update(self, dt, angin_global, kapal=None):
        """Advance by the shared dt from main.py.
        angin_global: wind vector (3,) in m/s, or None for no wind.
        kapal: ship state {"pos", "vel"} from Module A for A->C, or None when F1 switches it off."""
        if dt <= 0.0:                            # first frame or paused: Verlet divides by dt
            return
        t0 = time.perf_counter()                 # [AI] C3: step_ms = wall-clock cost of this update
        self.dt_terakhir = dt
        c = self.c
        active = self.semua if self.bending else self.tanpa_lentur
        # [AI] C4, interaction A->C: add the ship's wake to the global wind, per triangle.
        #      (3,) + (T, 3) broadcasts to (T, 3); the lecturer's wind_forces accepts that unchanged.
        wind = angin_global
        self.angin_kapal_maks = 0.0
        if kapal is not None:
            wk = wind_ship(c, kapal)
            self.angin_kapal_maks = float(np.max(np.linalg.norm(wk, axis=1)))
            wind = (np.zeros(3) if angin_global is None else angin_global) + wk
        if self.mode == "verlet":
            h = dt / self.substeps               # substeps x iterations (brief §5.2): smaller h -> fewer passes needed
            for _ in range(self.substeps):
                step_verlet(c, h, active, wind, self.iters)
        else:
            n = max(1, math.ceil(dt / DT - 1e-9))    # enough steps that none is larger than the lecturer's DT
            for _ in range(n):
                step_springs(c, dt / n, active, wind)
        # [DOSEN] cloth_p16.py main(): NaN auto-reset; [AI] counted for the HUD
        if not np.all(np.isfinite(c["pos"])):
            self.reset()
            self.resets += 1
        # [AI] C3: smooth step_ms over ~20 frames (0.05 per frame) so the HUD number is readable
        ms = (time.perf_counter() - t0) * 1000.0
        self.step_ms = ms if self.step_ms == 0.0 else self.step_ms + 0.05 * (ms - self.step_ms)

    def render_3d(self):
        """Draw inside rl.begin_mode_3d(camera). [DOSEN] -> [AI] the lecturer's drawing loop from main(), changed
        in C5 (brief §5.2): every triangle is drawn ONCE with backface culling switched off, instead of twice with
        opposite windings. raylib collects triangles in a batch and sends them to the GPU later, so the batch is
        flushed before culling goes off (earlier objects keep culling) and again before it comes back on (the
        banner is really drawn while culling is off). Without these flushes the setting does not apply to the banner.
        Claude, 2026-11-23; reviewed by Nando: pending"""
        P, nc = self.c["pos"], self.NC
        V = [v3(p) for p in P]                       # one Vector3 per particle, reused by up to 6 triangles
        rl.rl_draw_render_batch_active()             # flush 1: everything drawn so far, still with culling on
        rl.rl_disable_backface_culling()             # both sides of every triangle are visible from here
        for r in range(self.NR - 1):                 # gambar sebagai segitiga (sekali, dua sisi terlihat)
            for q in range(nc - 1):
                a, b = V[idx(r, q, nc)], V[idx(r + 1, q, nc)]
                c2, d = V[idx(r, q + 1, nc)], V[idx(r + 1, q + 1, nc)]
                col = WARNA_A if (r // 3 + q // 3) % 2 else WARNA_B
                rl.draw_triangle_3d(a, b, c2, col)
                rl.draw_triangle_3d(b, d, c2, col)
        rl.rl_draw_render_batch_active()             # flush 2: the banner, while culling is still off
        rl.rl_enable_backface_culling()
        for i in np.flatnonzero(self.c["pinned"]):  # the pinned particles, as small black spheres
            rl.draw_sphere(V[i], 0.1, rl.BLACK)

    def get_metrics(self):
        """Plain values for the HUD and the CSV (brief §5.2, §7.5)."""
        e_avg, e_max = stretch(self.c)
        active = self.semua if self.bending else self.tanpa_lentur
        tip = float(np.mean(np.linalg.norm(self.c["vel"][self.ujung], axis=1)))   # [AI] C3: m/s
        return {"mode": self.mode, "substeps": self.substeps, "iters": self.iters, "bending": self.bending,
                "partikel": len(self.c["pos"]), "constraint": int(active.sum()),
                "stretch_mean": e_avg, "stretch_max": e_max, "resets": self.resets,
                "tip_speed": tip, "step_ms": self.step_ms,
                "ship_wind_at_banner": self.angin_kapal_maks}                       # [AI] C4: m/s, CSV column

    def get_export_state(self):
        """Module C gives nothing to other modules (brief §5 table: exports = metrics only)."""
        return {}

# ---------- Program mandiri (Tahap 2) ----------
# [AI] Claude, 2026-11-23: window size, HUD and H overlay of the standalone harness (brief §5.2 HUD list, §7.5).
#      In the full program main.py draws its own HUD from get_metrics(). reviewed by Nando: pending
LEBAR, TINGGI = 1280, 720                # window size in pixels (assignment target: 60 FPS at 1280 x 720)
BANTUAN = [                              # (key, what it does) for the H overlay
    ("M", "ganti metode: Verlet-constraint / pegas-massa"),
    ("+ / -", "iterasi Verlet per substep (1..20)"),
    ("B", "pegas / constraint lentur on/off"),
    ("W", "angin kencang on/off (main.py di program lengkap)"),
    ("F1", "interaksi A->C on/off (kapal tiruan)"),
    ("kiri / kanan", "putar kamera"),
    ("R", "ulang bendera"),
    ("P / SPASI", "jeda"),
    ("H", "tutup bantuan"),
]

def gambar_hud(m, kencang, paused, inter_ac):
    """Module C numbers on screen: every value comes from Banner.get_metrics()."""
    if m["mode"] == "verlet":
        metode = f"Verlet + constraint jarak, {m['substeps']} substep x {m['iters']} iterasi"
    else:
        metode = f"Pegas-massa + semi-implisit Euler, langkah <= {DT * 1000:.2f} ms"
    baris = [
        (f"Modul C - Bendera  |  {metode}", 20, rl.DARKGRAY),
        (f"regangan rata-rata = {m['stretch_mean'] * 100:.2f} %   maks = {m['stretch_max'] * 100:.2f} %", 20, rl.MAROON),
        (f"{m['partikel']} partikel, {m['constraint']} constraint   lentur = {'on' if m['bending'] else 'off'}"
         f"   reset NaN = {m['resets']}", 18, rl.GRAY),
        (f"kecepatan ujung bendera = {m['tip_speed']:.2f} m/s   step = {m['step_ms']:.2f} ms", 18, rl.GRAY),
        (f"angin kapal di bendera = {m['ship_wind_at_banner']:.2f} m/s   F1 A->C = {'on' if inter_ac else 'off'}",
         18, rl.GRAY),
        (f"angin = {'KENCANG' if kencang else 'normal'}" + ("   [JEDA]" if paused else ""), 18, rl.GRAY),
    ]
    y = 16
    for teks, ukuran, warna in baris:
        rl.draw_text(teks, 20, y, ukuran, warna)
        y += ukuran + 8
    rl.draw_fps(LEBAR - 100, 16)
    rl.draw_text("H = bantuan", 20, TINGGI - 28, 18, rl.GRAY)

def gambar_bantuan():
    """H overlay: every control of the standalone program (assignment rule: controls on screen or under H)."""
    w, h = 620, 64 + 28 * len(BANTUAN)
    x, y = (LEBAR - w) // 2, (TINGGI - h) // 2
    rl.draw_rectangle(x, y, w, h, rl.fade(rl.BLACK, 0.8))
    rl.draw_text("Kontrol Modul C (standalone)", x + 20, y + 16, 22, rl.RAYWHITE)
    for k, (tombol, arti) in enumerate(BANTUAN):
        rl.draw_text(tombol, x + 20, y + 56 + 28 * k, 18, rl.GOLD)
        rl.draw_text(arti, x + 170, y + 56 + 28 * k, 18, rl.RAYWHITE)

# [AI] Claude, 2026-11-23: mock ship for testing A->C without Module A (brief §5.2 "Done when").
#      It flies back and forth on the real north-pass line (WP3 -> WP5, about 14 m from the pole) and exports
#      pos and vel exactly like Module A will: vel = (new_pos - old_pos) / dt. reviewed by Nando: pending
KAPAL_A = np.array([40.0, 34.0, -30.0])     # m, one end of the pass
KAPAL_B = np.array([-40.0, 34.0, -30.0])    # m, other end of the pass
KAPAL_V = 6.0                               # m/s, mock ship speed (route average, brief §5.1)

def kapal_tiruan(t):
    """Mock ship position at time t: ping-pong between KAPAL_A and KAPAL_B at speed KAPAL_V."""
    L = float(np.linalg.norm(KAPAL_B - KAPAL_A))
    s = (t * KAPAL_V) % (2.0 * L)                 # distance flown inside the current out-and-back trip
    u = s / L if s < L else 2.0 - s / L           # 0 -> 1 on the way out, 1 -> 0 on the way back
    return KAPAL_A + u * (KAPAL_B - KAPAL_A)

# [DOSEN] -> [AI] cloth_p16.py main() as the standalone harness: it now plays the role of main.py (one shared dt,
#      the wind with W = strong, F1 = A->C on/off with the mock ship, camera, pause, reset, HUD, H overlay)
#      and calls the Banner class. Claude, 2026-11-22 (C2), 2026-11-23 (C3, C4); reviewed by Nando: pending
def main():
    bendera = Banner()
    kencang, paused, bantuan, t, cam_ang = False, False, False, 0.0, 0.6
    inter_ac, kapal_pos, kapal_vel = True, kapal_tiruan(0.0), np.zeros(3)   # F1 state and mock ship state
    rl.init_window(LEBAR, TINGGI, "Modul C - bendera di tiang (standalone)")
    rl.set_target_fps(60)
    pusat = TIANG + np.array([-4.0, -6.0, 0.0])     # camera target (m): roughly the middle of the hanging banner
    jarak = 22.0                                     # camera orbit radius (m); range 12..40
    cam = rl.Camera3D(v3(pusat + (0.0, 2.0, jarak)), v3(pusat), rl.Vector3(0, 1, 0), 45.0,
                      rl.CAMERA_PERSPECTIVE)
    while not rl.window_should_close():
        bendera.handle_input()                                      # M, B, + / -
        if rl.is_key_pressed(rl.KEY_W): kencang = not kencang       # wind key: main.py owns it in the full program
        if rl.is_key_pressed(rl.KEY_R): bendera.reset()
        if rl.is_key_pressed(rl.KEY_SPACE) or rl.is_key_pressed(rl.KEY_P): paused = not paused
        if rl.is_key_pressed(rl.KEY_H): bantuan = not bantuan
        if rl.is_key_pressed(rl.KEY_F1): inter_ac = not inter_ac      # same meaning as F1 in main.py
        if rl.is_key_down(rl.KEY_LEFT): cam_ang -= 0.02
        if rl.is_key_down(rl.KEY_RIGHT): cam_ang += 0.02
        cam.position = v3(pusat + (jarak * math.sin(cam_ang), 2.0, jarak * math.cos(cam_ang)))

        dt = min(rl.get_frame_time(), 1 / 30)                      # ONE shared dt, as main.py will do (brief §6.2)
        if not paused and dt > 0:
            t += dt
            angin = wind_at(t) * (2.0 if kencang else 1.0)          # lecturer's wind, doubled by W (stand-in for angin_global)
            baru = kapal_tiruan(t)
            kapal_vel = (baru - kapal_pos) / dt                      # same velocity export as Module A
            kapal_pos = baru
            kapal = {"pos": kapal_pos, "vel": kapal_vel}
            bendera.update(dt, angin, kapal if inter_ac else None)   # switched off = None, as main.py does

        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        rl.begin_mode_3d(cam)
        # flagpole from the top of the spire (y = 28 m) to just above TIANG; world_scene.py draws the real one
        rl.draw_cylinder_ex(v3(TIANG - (0.0, 9.5, 0.0)), v3(TIANG + (0.0, 0.5, 0.0)), 0.15, 0.15, 8, rl.DARKGRAY)
        bendera.render_3d()
        rl.draw_sphere(v3(kapal_pos), 1.5, rl.MAROON if inter_ac else rl.GRAY)   # mock ship (grey = F1 off)
        rl.end_mode_3d()
        gambar_hud(bendera.get_metrics(), kencang, paused, inter_ac)
        if bantuan:
            gambar_bantuan()
        rl.end_drawing()
    rl.close_window()

# [DOSEN] cloth_p16.py: entry point, unchanged
if __name__ == "__main__":
    main()
