"""Tes tanpa jendela untuk Modul A (mod_a_skyship.py). Jalankan dari root repo:  pytest"""
import numpy as np
import mod_a_skyship as A

K = np.asarray(A.WAYPOINTS, dtype=float)


def test_rute_11_titik_dan_wp0_di_dermaga():
    assert K.shape == (11, 3)
    assert np.allclose(K[0], (38.0, 4.5, 0.0))
