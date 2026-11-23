"""Tes tanpa jendela untuk Modul A (mod_a_skyship.py). Jalankan dari root repo:  pytest"""
import numpy as np
import mod_a_skyship as A

K = np.asarray(A.WAYPOINTS, dtype=float)


def test_rute_11_titik_dan_wp0_di_dermaga():
    assert K.shape == (11, 3)
    assert np.allclose(K[0], (38.0, 4.5, 0.0))


def test_jalur_melewati_setiap_waypoint():
    for i in range(len(K)):
        assert np.allclose(A.titik_jalur(K, float(i)), K[i], atol=1e-9)


def test_jalur_tertutup_tanpa_loncatan():
    n = len(K)
    assert np.allclose(A.titik_jalur(K, n - 1e-9), K[0], atol=1e-6)   # ujung segmen terakhir = WP0
    assert np.allclose(A.titik_jalur(K, float(n)), K[0], atol=1e-9)   # t = n kembali ke awal


def test_tangen_di_waypoint_sesuai_rumus_catmull_rom():
    n = len(K)
    for i in range(n):
        harap = 0.5 * (K[(i + 1) % n] - K[(i - 1) % n])                 # V_i = 1/2 (K_i+1 - K_i-1), slide P7
        assert np.allclose(A.tangen_jalur(K, float(i)), harap, atol=1e-9)


def test_tabel_arc_length_jalur_tertutup():
    ts, sn, L = A.bangun_tabel(K)
    assert ts[0] == 0.0 and ts[-1] == len(K)       # n titik kunci = n segmen (jalur tertutup)
    assert sn[0] == 0.0 and sn[-1] == 1.0
    assert np.all(np.diff(sn) > 0)                 # naik terus, jadi bisa dibalik dengan np.interp
    assert abs(L - 300.4) < 0.5                    # panjang rute ~300 m (prototipe: 300,4 m)
