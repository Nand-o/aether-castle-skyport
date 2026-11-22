"""
Pertemuan 17 - Arsitektur Sistem Partikel (Emitter & Lifetime)
Praktikum: kelas Particle dan Emitter untuk efek api dan asap dasar.
Rujukan: Parent, R. (2012). Computer Animation: Algorithms and Techniques, Bab 7.3;
         Reeves (1983) "Particle Systems - A Technique for Modeling a Class of Fuzzy Objects".

Jalankan:  pip install raylib   lalu   python particles_p17.py
Kontrol :  mouse = pindahkan sumber api, atas/bawah = laju emisi api,
           W angin on/off, B blending aditif on/off, 1 api, 2 asap, 3 keduanya,
           SPASI ledakan percikan, P jeda
"""
import math
import random
import time
import pyray as rl

GRAVITY = (0.0, -9.81)
MAX_PARTICLES = 3000                  # batas anggaran partikel

# ---------- Utilitas ----------
def lerp(a, b, t):
    return a + (b - a) * t

def gradient(stops, t):
    """stops = [(t0, (r, g, b, a)), (t1, ...), ...] terurut; kembalikan warna pada t."""
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return tuple(int(lerp(a, b, u)) for a, b in zip(c0, c1))
    return stops[-1][1]

def rand_range(mean, var):
    """Nilai acak = rata-rata + variansi * U(-1, 1) (gaya Reeves)."""
    return mean + var * random.uniform(-1.0, 1.0)

# ---------- Partikel ----------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "age", "life", "size0", "size1", "style")

    def __init__(self, x, y, vx, vy, life, size0, size1, style):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.age, self.life = 0.0, life
        self.size0, self.size1 = size0, size1
        self.style = style                     # aturan warna, gaya, render

    @property
    def t(self):                               # umur relatif 0..1
        return self.age / self.life

    def alive(self):
        return self.age < self.life

# ---------- Gaya & gaya tampil per jenis partikel ----------
FIRE = dict(
    colors=[(0.0, (255, 230, 150, 150)), (0.3, (255, 150, 40, 130)),
            (0.7, (200, 50, 15, 70)), (1.0, (60, 15, 5, 0))],
    buoyancy=5.0, drag=1.5, turbulence=4.0, additive=True)
SMOKE = dict(
    colors=[(0.0, (90, 90, 95, 0)), (0.2, (110, 110, 115, 70)),
            (1.0, (170, 170, 175, 0))],
    buoyancy=1.6, drag=0.8, turbulence=1.2, additive=False)
SPARK = dict(
    colors=[(0.0, (255, 255, 220, 255)), (0.5, (255, 180, 60, 255)), (1.0, (200, 60, 20, 0))],
    buoyancy=0.0, drag=0.3, turbulence=0.0, additive=True, gravity=True)

# ---------- Emitter ----------
class Emitter:
    """Sumber partikel: menentukan berapa, di mana, dengan atribut awal apa."""
    def __init__(self, x, y, style, rate, rate_var, speed, speed_var, spread,
                 life, life_var, size0, size1, radius=0.15, direction=math.pi / 2):
        self.x, self.y, self.style = x, y, style
        self.rate, self.rate_var = rate, rate_var        # partikel per detik
        self.speed, self.speed_var, self.spread = speed, speed_var, spread
        self.life, self.life_var = life, life_var
        self.size0, self.size1 = size0, size1
        self.radius, self.direction = radius, direction
        self.carry = 0.0                                 # sisa pecahan partikel

    def emit(self, dt, particles):
        n_float = max(0.0, rand_range(self.rate, self.rate_var)) * dt + self.carry
        n = int(n_float)
        self.carry = n_float - n
        for _ in range(n):
            if len(particles) >= MAX_PARTICLES:
                return
            ang = self.direction + random.uniform(-self.spread, self.spread)
            spd = rand_range(self.speed, self.speed_var)
            r, a = self.radius * math.sqrt(random.random()), random.uniform(0, 2 * math.pi)
            particles.append(Particle(
                self.x + r * math.cos(a), self.y + 0.3 * r * math.sin(a),
                spd * math.cos(ang), spd * math.sin(ang),
                max(0.05, rand_range(self.life, self.life_var)),
                self.size0 * random.uniform(0.7, 1.3), self.size1, self.style))

    def burst(self, n, particles):
        """Emisi n partikel sekaligus (ledakan)."""
        self.carry += n
        self.emit(0.0, particles)

# ---------- Simulasi: gaya, gerak, dan kematian ----------
def update(particles, dt, wind):
    for p in particles:
        st = p.style
        ax = 0.0
        ay = st["buoyancy"] + (GRAVITY[1] if st.get("gravity") else 0.0)  # gaya apung
        ax += st["drag"] * (wind - p.vx)                   # hambatan relatif udara (P13)
        ay += st["drag"] * (0.0 - p.vy)
        k = st["turbulence"]
        ax += k * random.gauss(0, 1)                       # turbulensi acak
        ay += k * random.gauss(0, 1)
        p.vx += ax * dt                                    # semi-implisit Euler (P14)
        p.vy += ay * dt
        p.x += p.vx * dt
        p.y += p.vy * dt
        p.age += dt
        if p.y < 0.0 and st.get("gravity"):                # percikan memantul di lantai
            p.y, p.vy = 0.0, -0.4 * p.vy
    particles[:] = [p for p in particles if p.alive()]   # terminasi

# ---------- Render ----------
W, H, SCALE, GROUND = 960, 640, 100.0, 600

def to_screen(x, y):
    return rl.Vector2(x * SCALE, GROUND - y * SCALE)

def soft_circle(c, radius, inner, outer):
    """Lingkaran bertepi lembut (pusat -> transparan). raylib 6 memakai Vector2,
    raylib 5 memakai (x, y) int; dukung keduanya."""
    try:
        rl.draw_circle_gradient(c, radius, inner, outer)
    except TypeError:
        rl.draw_circle_gradient(int(c.x), int(c.y), radius, inner, outer)

def render(particles, additive_on):
    for additive in (False, True):                        # asap dulu, api di atasnya
        if additive and additive_on:
            rl.begin_blend_mode(rl.BLEND_ADDITIVE)
        for p in particles:
            if p.style["additive"] != additive:
                continue
            r, g, b, a = gradient(p.style["colors"], p.t)
            size = lerp(p.size0, p.size1, p.t) * SCALE
            soft_circle(to_screen(p.x, p.y), size, rl.Color(r, g, b, a), rl.Color(r, g, b, 0))
        if additive and additive_on:
            rl.end_blend_mode()

def main():
    fire = Emitter(4.8, 0.5, FIRE, rate=220, rate_var=40, speed=1.0, speed_var=0.4,
                   spread=0.35, life=0.7, life_var=0.25, size0=0.2, size1=0.04, radius=0.3)
    smoke = Emitter(4.8, 1.5, SMOKE, rate=40, rate_var=10, speed=0.6, speed_var=0.2,
                    spread=0.5, life=3.5, life_var=1.0, size0=0.15, size1=0.6, radius=0.25)
    sparks = Emitter(4.8, 0.6, SPARK, rate=0, rate_var=0, speed=5.0, speed_var=2.0,
                     spread=math.pi, life=1.4, life_var=0.5, size0=0.03, size1=0.01)
    particles, show, use_wind, additive_on, paused, t = [], 3, False, True, False, 0.0
    rl.init_window(W, H, "P17 - Sistem partikel: api & asap")
    rl.set_target_fps(60)
    while not rl.window_should_close():
        dt = min(rl.get_frame_time(), 1 / 30)
        if rl.is_key_pressed(rl.KEY_ONE): show = 1
        if rl.is_key_pressed(rl.KEY_TWO): show = 2
        if rl.is_key_pressed(rl.KEY_THREE): show = 3
        if rl.is_key_pressed(rl.KEY_W): use_wind = not use_wind
        if rl.is_key_pressed(rl.KEY_B): additive_on = not additive_on
        if rl.is_key_pressed(rl.KEY_P): paused = not paused
        if rl.is_key_pressed(rl.KEY_UP): fire.rate = min(fire.rate * 1.25, 2000)
        if rl.is_key_pressed(rl.KEY_DOWN): fire.rate = max(fire.rate / 1.25, 10)
        if rl.is_mouse_button_down(rl.MOUSE_BUTTON_LEFT):
            mx, my = rl.get_mouse_x() / SCALE, (GROUND - rl.get_mouse_y()) / SCALE
            fire.x, fire.y = mx, max(0.2, my)
        smoke.x, smoke.y = fire.x, fire.y + 1.2
        sparks.x, sparks.y = fire.x, fire.y + 0.1
        if rl.is_key_pressed(rl.KEY_SPACE):
            sparks.burst(150, particles)

        t0 = time.perf_counter()
        if not paused:
            t += dt
            wind = 1.5 + 1.0 * math.sin(0.7 * t) if use_wind else 0.0
            if show in (1, 3): fire.emit(dt, particles)
            if show in (2, 3): smoke.emit(dt, particles)
            update(particles, dt, wind)
        ms = (time.perf_counter() - t0) * 1000

        rl.begin_drawing()
        rl.clear_background(rl.Color(20, 24, 36, 255))
        rl.draw_rectangle(0, GROUND, W, H - GROUND, rl.Color(40, 44, 58, 255))
        render(particles, additive_on)
        rl.draw_text(f"partikel hidup: {len(particles)} / {MAX_PARTICLES}   laju api: {fire.rate:.0f}/s",
                     20, 16, 20, rl.RAYWHITE)
        rl.draw_text(f"update: {ms:.1f} ms   angin: {'on' if use_wind else 'off'}   "
                     f"aditif: {'on' if additive_on else 'off'}", 20, 42, 18, rl.LIGHTGRAY)
        rl.draw_text("mouse geser api | atas/bawah laju | W angin | B aditif | 1/2/3 | SPASI percikan | P jeda",
                     20, H - 26, 16, rl.LIGHTGRAY)
        rl.end_drawing()
    rl.close_window()

if __name__ == "__main__":
    main()
