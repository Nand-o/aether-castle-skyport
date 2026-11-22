"""
Pertemuan 15 - Spring-Mass Systems (Sistem Pegas-Massa) 1D & 2D
Praktikum: hukum Hooke + redaman untuk tali elastis (1D) dan struktur jeli / soft body (2D).
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 7.1 & 7.2.

Jalankan:  pip install raylib numpy   lalu   python spring_mass_p15.py
Kontrol :  1 tali, 2 jeli, seret partikel dengan mouse (pegas maya),
           S pegas geser (shear) on/off, atas/bawah ubah k, D redaman on/off,
           R ulang, SPASI jeda
"""
import numpy as np
import pyray as rl

G = np.array([0.0, -9.81])
SUBSTEPS = 8                       # beberapa langkah fisika per frame (stabilitas, P14)
DT = 1.0 / 60.0 / SUBSTEPS         # ~2,1 ms

# ---------- Sistem pegas-massa (data disimpan sebagai array NumPy) ----------
class SpringMass:
    def __init__(self, pos, mass=0.1):
        self.pos = np.array(pos, dtype=float)          # (N, 2) posisi partikel
        self.vel = np.zeros_like(self.pos)              # (N, 2) kecepatan
        self.mass = np.full(len(self.pos), mass)        # (N,)  massa
        self.pinned = np.zeros(len(self.pos), bool)     # partikel yang dipaku
        self.si, self.sj = [], []                       # indeks ujung pegas
        self.rest, self.kind = [], []                   # panjang diam & jenis

    def add_spring(self, i, j, kind="struktural"):
        self.si.append(i); self.sj.append(j)
        self.rest.append(np.linalg.norm(self.pos[j] - self.pos[i]))
        self.kind.append(kind)

    def finalize(self):
        self.si, self.sj = np.array(self.si), np.array(self.sj)
        self.rest, self.kind = np.array(self.rest), np.array(self.kind)

def spring_forces(sm, k, c, active):
    """Hooke + redaman sepanjang pegas: F_i = [k(L - L0) + c (v_j - v_i).n] n, F_j = -F_i."""
    i, j = sm.si[active], sm.sj[active]
    d = sm.pos[j] - sm.pos[i]
    L = np.linalg.norm(d, axis=1)
    n = d / np.maximum(L, 1e-9)[:, None]                 # arah satuan i -> j
    v_rel = np.sum((sm.vel[j] - sm.vel[i]) * n, axis=1)  # laju memanjang
    f = (k * (L - sm.rest[active]) + c * v_rel)[:, None] * n
    F = np.zeros_like(sm.pos)
    np.add.at(F, i, f)                                   # tarik i ke arah j
    np.add.at(F, j, -f)                                  # Newton III
    return F

def step(sm, dt, k, c, active, drag=None, k_mouse=40.0):
    F = sm.mass[:, None] * G                             # gravitasi
    F += spring_forces(sm, k, c, active)                 # semua pegas
    if drag is not None:                                 # pegas maya ke mouse
        idx, target = drag
        F[idx] += k_mouse * (target - sm.pos[idx]) - 2.0 * sm.vel[idx]
    a = F / sm.mass[:, None]
    sm.vel += a * dt                                     # semi-implisit Euler (P14)
    sm.vel[sm.pinned] = 0.0
    sm.pos += sm.vel * dt
    below = sm.pos[:, 1] < 0.0                           # lantai sederhana (P19-20)
    sm.pos[below, 1] = 0.0
    sm.vel[below, 1] = np.maximum(sm.vel[below, 1], 0.0)
    sm.vel[below, 0] *= 0.95                             # gesekan kasar

def total_length_error(sm, active):
    d = sm.pos[sm.sj[active]] - sm.pos[sm.si[active]]
    return np.mean(np.abs(np.linalg.norm(d, axis=1) / sm.rest[active] - 1.0))

# ---------- Pembangun bentuk ----------
def make_rope(n=20, length=3.0, anchor=(5.0, 5.0)):
    pts = [(anchor[0] + i * length / (n - 1), anchor[1]) for i in range(n)]
    sm = SpringMass(pts, mass=0.05)
    sm.pinned[0] = True
    for i in range(n - 1):
        sm.add_spring(i, i + 1)
    sm.finalize()
    return sm

def make_jelly(cols=7, rows=7, size=1.8, center=(4.8, 3.6), tilt=0.35):
    h = size / (cols - 1)
    idx = lambda r, q: r * cols + q
    cs, sn = np.cos(tilt), np.sin(tilt)               # dimiringkan agar jatuh di sudut
    pts = []
    for r in range(rows):
        for q in range(cols):
            x, y = q * h - size / 2, r * h - size / 2
            pts.append((center[0] + cs * x - sn * y, center[1] + sn * x + cs * y))
    sm = SpringMass(pts, mass=0.05)
    for r in range(rows):
        for q in range(cols):
            if q + 1 < cols: sm.add_spring(idx(r, q), idx(r, q + 1))
            if r + 1 < rows: sm.add_spring(idx(r, q), idx(r + 1, q))
            if q + 1 < cols and r + 1 < rows:              # diagonal penahan geser
                sm.add_spring(idx(r, q), idx(r + 1, q + 1), "geser")
                sm.add_spring(idx(r, q + 1), idx(r + 1, q), "geser")
    sm.finalize()
    return sm

# ---------- Tampilan: meter -> piksel ----------
W, H = 960, 640
SCALE, GROUND = 100.0, 600

def to_screen(p):
    return (p[0] * SCALE, GROUND - p[1] * SCALE)

def to_world(sx, sy):
    return np.array([sx / SCALE, (GROUND - sy) / SCALE])

def main():
    scene, use_shear, damping, paused = 1, True, True, False
    k, c = 500.0, 0.5
    sm = make_rope()
    drag = None
    rl.init_window(W, H, "P15 - Sistem pegas-massa")
    rl.set_target_fps(60)
    while not rl.window_should_close():
        if rl.is_key_pressed(rl.KEY_ONE): scene, sm, drag = 1, make_rope(), None
        if rl.is_key_pressed(rl.KEY_TWO): scene, sm, drag = 2, make_jelly(), None
        if rl.is_key_pressed(rl.KEY_R): sm, drag = (make_rope() if scene == 1 else make_jelly()), None
        if rl.is_key_pressed(rl.KEY_S): use_shear = not use_shear
        if rl.is_key_pressed(rl.KEY_D): damping = not damping
        if rl.is_key_pressed(rl.KEY_SPACE): paused = not paused
        if rl.is_key_pressed(rl.KEY_UP): k = min(k * 1.5, 20000.0)
        if rl.is_key_pressed(rl.KEY_DOWN): k = max(k / 1.5, 5.0)

        mouse = to_world(rl.get_mouse_x(), rl.get_mouse_y())
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            near = int(np.argmin(np.linalg.norm(sm.pos - mouse, axis=1)))
            if np.linalg.norm(sm.pos[near] - mouse) < 0.4:
                drag = [near, mouse]
        if rl.is_mouse_button_released(rl.MOUSE_BUTTON_LEFT):
            drag = None
        if drag is not None:
            drag[1] = mouse

        active = np.ones(len(sm.si), bool) if use_shear else (sm.kind != "geser")
        if not paused:
            for _ in range(SUBSTEPS):
                step(sm, DT, k, c if damping else 0.0, active, drag)
                if not np.all(np.isfinite(sm.pos)):      # meledak: mulai ulang
                    sm = make_rope() if scene == 1 else make_jelly()
                    break

        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        rl.draw_line(0, GROUND, W, GROUND, rl.DARKGRAY)
        for s in np.nonzero(active)[0]:
            a, b = to_screen(sm.pos[sm.si[s]]), to_screen(sm.pos[sm.sj[s]])
            stretch = np.linalg.norm(sm.pos[sm.sj[s]] - sm.pos[sm.si[s]]) / sm.rest[s] - 1.0
            col = rl.MAROON if stretch > 0.02 else (rl.DARKBLUE if stretch < -0.02 else rl.DARKGRAY)
            rl.draw_line_ex(a, b, 1.5 if sm.kind[s] == "geser" else 3, col)
        for idx, p in enumerate(sm.pos):
            x, y = to_screen(p)
            rl.draw_circle(int(x), int(y), 6 if sm.pinned[idx] else 4,
                           rl.BLACK if sm.pinned[idx] else rl.ORANGE)
        if drag is not None:
            a, b = to_screen(sm.pos[drag[0]]), to_screen(drag[1])
            rl.draw_line_ex(a, b, 1, rl.GRAY)
        title = "Tali elastis (1D)" if scene == 1 else "Jeli / soft body (2D)"
        rl.draw_text(title, 20, 16, 22, rl.DARKGRAY)
        rl.draw_text(f"k = {k:.0f} N/m   c = {c if damping else 0:.1f} N.s/m   "
                     f"geser = {'on' if use_shear else 'off'}   dt = {DT * 1000:.1f} ms x {SUBSTEPS}",
                     20, 46, 18, rl.GRAY)
        rl.draw_text(f"regangan rata-rata = {total_length_error(sm, active) * 100:.1f} %",
                     20, 70, 18, rl.GRAY)
        rl.draw_text("merah = tertarik, biru = tertekan", 20, 94, 16, rl.LIGHTGRAY)
        rl.draw_text("1 tali | 2 jeli | mouse seret | S geser | atas/bawah k | D redaman | R ulang | SPASI jeda",
                     20, H - 26, 16, rl.GRAY)
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
