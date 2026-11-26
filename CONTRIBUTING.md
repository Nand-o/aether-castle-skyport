# Panduan Kontribusi

Aturan kerja tim Aether Castle Skyport: cabang, pesan commit, label asal kode, dan pull request. Tujuannya satu: riwayat git yang rapi dan jujur, karena riwayat commit ikut dinilai dan dosen memeriksa kode setiap anggota.

## Alur kerja singkat

1. `git switch main` lalu `git pull`.
2. Kerjakan di cabang modulmu (lihat tabel di bawah).
3. Satu fitur per hari, dipecah menjadi **5–8 commit kecil**. Setiap commit jalan sendiri dan tesnya lulus.
4. Di akhir hari: `git push`, lalu buka **satu pull request** ke `main`.
5. Satu anggota lain mereview, lalu PR di-merge.

| Cabang | Pemilik | Isi |
| :--- | :--- | :--- |
| `main` | semua | Selalu bisa dijalankan. Tidak ada commit langsung ke sini. |
| `mod-a` | Faris | Modul A |
| `mod-c`, `world` | Nando | Modul C, `world_scene.py` |
| `mod-d` | Anggota 3 | Modul D |
| `integration` | Faris | `main.py` |
| `docs` | siapa saja | README dan dokumen lain |

## Pesan commit

Pesan commit cukup **satu baris**, mengikuti [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <ringkasan>
```

Penjelasan yang lebih panjang (apa yang berubah, kenapa, cara menguji, asal kode) ditulis di **deskripsi pull request**, bukan di commit.

### Type

| Type | Dipakai untuk |
| :--- | :--- |
| `feat` | Fitur atau perilaku baru |
| `fix` | Memperbaiki bug |
| `refactor` | Mengubah susunan kode tanpa mengubah perilaku |
| `perf` | Membuat lebih cepat |
| `test` | Menambah atau mengubah tes saja |
| `docs` | README, komentar, dokumen |
| `chore` | Konfigurasi, dependensi, menyalin kode dosen |
| `style` | Format saja (spasi, urutan import) |

### Scope

`a` (Modul A), `c` (Modul C), `d` (Modul D), `main`, `world`, `docs`. Boleh dikosongkan untuk perubahan yang menyentuh seluruh repo, misalnya `chore: add .gitignore`.

### Aturan

1. **Satu baris saja**, dalam bahasa Inggris, bentuk perintah (*add*, *fix*, *make*; bukan *added* atau *adds*), huruf kecil di awal, tanpa titik di akhir, maksimal 72 karakter.
2. **Satu commit, satu perubahan.** Kalau ringkasan butuh kata "dan", pecah menjadi dua commit.
3. Commit pertama setiap modul selalu salinan kode dosen apa adanya: `chore(<scope>): start from <file> (kode dosen, unchanged)`.
4. Commit hanya atas nama sendiri. Jangan commit pekerjaan orang lain atas nama kita.

### Contoh yang baik

```text
chore(d): start from boids_p18.py (kode dosen, unchanged)
feat(a): make titik_jalur a closed 3D path
feat(a): add tangen_jalur from the Catmull-Rom derivative
fix(c): flush the raylib batch before disabling backface culling
test(main): check the update order A, D, C with one shared dt
docs: add README with setup, controls and team
```

### Contoh yang perlu diperbaiki

| Kurang baik | Lebih baik |
| :--- | :--- |
| `update` | `feat(a): add ease-in/out docking at WP0` |
| `fix bug` | `fix(main): skip the update when dt is 0` |
| `Added new feature and fixed stuff.` | Dua commit: `feat(...)` dan `fix(...)` |
| `feat(c): banner, wind, HUD, mock ship, render` | Satu commit per bagian |

## Label asal kode

Tandai **di atas setiap fungsi atau blok**, bukan per baris:

| Label | Arti |
| :--- | :--- |
| `# [DOSEN]` | Dari kode praktikum dosen, tidak diubah atau hanya diubah sedikit |
| `# [KAMI]` | Ditulis kelompok |
| `# [AI]` | Dibuat dengan bantuan asisten AI, lalu dipahami dan disesuaikan oleh penulisnya |

Setiap fungsi yang dibantu AI **wajib** berlabel `[AI]` dan tercatat di tabel atribusi README. Kode dari sumber luar tanpa atribusi membuat modul itu dinilai 0.

## Sebelum commit

- [ ] Modul yang diubah masih bisa dijalankan sendiri (`python mod_x_....py`), dan perubahan hari itu terlihat bekerja.
- [ ] Kalau punya tes lokal, tesnya lulus. Tes disimpan di laptop masing-masing (`tests/`, `pytest.ini`, `requirements-dev.txt` ada di `.gitignore`), tidak di-commit.
- [ ] Label `[DOSEN]` / `[KAMI]` / `[AI]` sudah ada di fungsi yang baru atau berubah.
- [ ] Tidak ada file sampah ikut masuk (`git status`): `.venv/`, `__pycache__/`, `logs/`, video, dan screenshot sudah ada di `.gitignore`.

## Pull request

- **Judul:** sama gayanya dengan ringkasan commit, misalnya `Modul A hari 2: kapal bergerak dengan arc-length dan ease`.
- **Isi:** template muncul otomatis (`.github/pull_request_template.md`). Di sinilah penjelasan lengkapnya ditulis, karena commit hanya satu baris: fitur apa yang masuk, daftar perubahan, asal kode (`[DOSEN]`/`[KAMI]`/`[AI]`), dan cara menguji beserta apa yang harus terlihat di layar.
- **Reviewer:** Faris mereview D, Anggota 3 mereview A, Nando mereview `main.py`; C dan dunia direview Faris atau Anggota 3.
- **Review sekaligus latihan tanya jawab:** reviewer mencoba mengubah satu parameter di kode itu dan menebak akibatnya sebelum menjalankan.
