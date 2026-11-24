# Aether Castle Skyport

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![raylib](https://img.shields.io/badge/raylib%20%28pyray%29-6.0.1-black)
![NumPy](https://img.shields.io/badge/NumPy-2.3.5-013243?logo=numpy&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20progress-orange)

Diorama interaktif 3D sebuah pulau melayang dengan kastil, dermaga kapal langit, bendera raksasa, dan kawanan wyvern. Proyek akhir mata kuliah **Animasi Komputer** (Semester 5, dosen Med Irzal). Dibangun dengan **Python, raylib (`pyray`), dan NumPy**, tanpa mesin fisika: kurva, solver kain, dan perilaku kawanan ditulis sendiri.

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Fitur](#fitur)
- [Status Pengerjaan](#status-pengerjaan)
- [Tech Stack](#tech-stack)
- [Menjalankan Secara Lokal](#menjalankan-secara-lokal)
- [Kontrol](#kontrol)
- [Interaksi Antarmodul](#interaksi-antarmodul)
- [Struktur Repo](#struktur-repo)
- [Tim](#tim)
- [Atribusi Kode](#atribusi-kode)
- [Rujukan](#rujukan)
- [Kontribusi](#kontribusi)

## Tentang Proyek

Satu adegan, tiga modul simulasi yang saling memengaruhi saat program berjalan:

- **Kapal langit** berputar mengelilingi pulau di jalur Catmull-Rom tertutup dengan kecepatan konstan, lalu melambat saat berlabuh di dermaga.
- **Bendera raksasa** di menara utara berkibar karena angin, dan berkibar lebih kencang saat kapal lewat.
- **Kawanan wyvern** terbang di atas kastil, menghindari menara, dan berpencar saat kapal menembus mereka. Kapal pun melambat kalau banyak wyvern di depannya.

Semua modul memakai satu `dt` dari game loop dan dirancang untuk 60 FPS pada 1280 × 720.

## Fitur

| Modul | Materi | Isi |
| :--- | :--- | :--- |
| **A — Kapal langit** | P5–P7: kurva & gerak terkendali | Catmull-Rom tertutup 3D, tabel arc-length (kecepatan konstan), ease-in/out ke dermaga, arah hadap dari tangen kurva |
| **C — Bendera kastil** | P15–P16: pegas & kain | Pegas-massa dan Verlet + constraint jarak (12 grup), angin per segitiga, render satu sisi, 4 substep × 2 iterasi |
| **D — Kawanan wyvern** | P17–P18: boids | Cohesion, separation, alignment dalam 3D, menghindari menara dan kapal |

Setiap modul punya tombol untuk mengubah simulasi dan angka pengukuran di layar (misalnya regangan kain %, simpangan kecepatan kapal, polarisasi kawanan), ditambah FPS untuk seluruh program.

## Status Pengerjaan

- [x] Repo, `.gitignore`, `requirements.txt`, kode dosen di `reference/dosen/`
- [x] Modul C: bendera + harness mandiri dengan kapal tiruan
- [ ] Modul A: jalur tertutup 3D + tabel arc-length *(sedang dikerjakan, cabang `mod-a`)*
- [ ] Modul A: gerak kapal, ease, interaksi D→A, harness mandiri
- [ ] Modul D: kawanan wyvern 3D
- [ ] `world_scene.py`: pulau, kastil, dermaga, kamera
- [ ] `main.py`: game loop bersama, HUD, menu bantuan `H`, rekam CSV
- [ ] Bendera kecil di dermaga *(tambahan)*
- [ ] Pengukuran di laptop demo, laporan, video, slide

## Tech Stack

- **Python 3.13**
- **raylib 6.0.1** lewat `pyray`: jendela, input, kamera, dan menggambar saja
- **NumPy 2.3.5**: semua perhitungan simulasi

Versi dipatok di [`requirements.txt`](requirements.txt), sama dengan laptop demo (HP Victus 15).

## Menjalankan Secara Lokal

Clone repo:

```bash
git clone https://github.com/Nand-o/aether-castle-skyport.git
cd aether-castle-skyport
```

Buat virtual environment Python 3.13 dan pasang dependensi:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jalankan modul yang sudah ada secara mandiri:

```bash
python mod_c_cloth.py      # bendera kastil + kapal tiruan
```

Program lengkap (`python main.py`) menyusul setelah integrasi.

## Kontrol

| Tombol | Fungsi | Lingkup |
| :--- | :--- | :--- |
| `H` | Bantuan (daftar semua tombol) | Global |
| `P` / `R` | Jeda / ulang | Global |
| `←` `→` | Putar kamera | Global |
| `W` | Angin kencang on/off | Global |
| `L` | Mulai / berhenti rekam CSV | Global |
| `F1` / `F2` / `F3` | Interaksi A→C / A→D / D→A on/off | Global |
| `T` | Mode arc-length ↔ t seragam | Modul A |
| `E` | Ease-in/out on/off | Modul A |
| `[` `]` | Putaran lebih lambat / lebih cepat | Modul A |
| `M` | Metode Verlet ↔ pegas-massa | Modul C |
| `B` | Pegas lentur on/off | Modul C |
| `+` `-` | Iterasi Verlet | Modul C |
| `1` `2` `3` | Cohesion / separation / alignment on/off | Modul D |

Tombol global baru aktif penuh di `main.py`. Harness mandiri tiap modul menampilkan tombolnya sendiri lewat `H`.

## Interaksi Antarmodul

| Tombol | Arah | Data | Efek |
| :---: | :---: | :--- | :--- |
| `F2` | A → D | Posisi kapal | Kapal menjadi pemangsa; kawanan berpencar lalu berkumpul lagi |
| `F3` | D → A | Jumlah wyvern di depan kapal | Kapal melambat sampai 50 % |
| `F1` | A → C | Posisi dan kecepatan kapal | Angin tambahan di sekitar bendera saat kapal lewat |

A↔D adalah pasangan dua arah; A→C adalah interaksi ketiga. Modul tidak saling import: `main.py` yang meneruskan keluaran satu modul ke modul lain.

## Struktur Repo

```text
aether-castle-skyport/
├── main.py              # game loop bersama (menyusul)
├── world_scene.py       # pulau, kastil, dermaga, kamera (menyusul)
├── mod_a_skyship.py     # Modul A: kapal langit
├── mod_c_cloth.py       # Modul C: bendera kastil
├── mod_d_boids.py       # Modul D: kawanan wyvern (menyusul)
├── reference/dosen/     # kode praktikum dosen, tidak diubah
└── requirements.txt     # dependensi program
```

## Tim

| Anggota | GitHub | Bagian |
| :--- | :--- | :--- |
| Nando | [@Nand-o](https://github.com/Nand-o) | Modul C (bendera), `world_scene.py`, bendera dermaga |
| Faris | [@farismlna](https://github.com/farismlna) | Modul A (kapal), `main.py`, README |
| Anggota 3 | *(menyusul)* | Modul D (kawanan) |

Setiap anggota menulis, meng-commit, dan mempresentasikan modulnya sendiri.

## Atribusi Kode

Kode praktikum dosen dipakai sebagai titik awal dan disimpan utuh di [`reference/dosen/`](reference/dosen/). Commit pertama setiap modul adalah salinan kode dosen tanpa perubahan, jadi setiap pengembangan kelompok terlihat di riwayat git.

Asal kode ditandai di atas setiap fungsi atau blok:

| Label | Arti |
| :--- | :--- |
| `[DOSEN]` | Dari kode praktikum dosen, tidak diubah atau hanya diubah sedikit |
| `[KAMI]` | Ditulis kelompok |
| `[AI]` | Dibuat dengan bantuan asisten AI, lalu dipahami dan disesuaikan oleh penulisnya |

| File | Dasar dari dosen | Pengembangan |
| :--- | :--- | :--- |
| `mod_a_skyship.py` | `catmull_rom_p7.py` | Jalur tertutup 3D, arah hadap dari tangen, rute 11 titik |
| `mod_c_cloth.py` | `cloth_p16.py` | Bendera 14 × 20 dipaku di tiang, angin dari kapal, substep × iterasi, render satu sisi |
| `mod_d_boids.py` | `boids_p18.py` | *(menyusul)* |

## Rujukan

- Parent, R. (2012). *Computer Animation: Algorithms and Techniques* (3rd ed.). Morgan Kaufmann.
- Reynolds, C. W. (1987). Flocks, herds and schools: A distributed behavioral model. *SIGGRAPH '87*.
- Provot, X. (1995). Deformation constraints in a mass-spring model to describe rigid cloth behavior. *Graphics Interface '95*.
- Jakobsen, T. (2001). Advanced character physics. *GDC*.
- Kode praktikum Animasi Komputer (Med Irzal): `catmull_rom_p7.py`, `spring_mass_p15.py`, `cloth_p16.py`, `particles_p17.py`, `boids_p18.py`.

## Kontribusi

Aturan cabang, pesan commit, dan pull request ada di [CONTRIBUTING.md](CONTRIBUTING.md).
