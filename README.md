# Aether Castle Skyport

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![raylib](https://img.shields.io/badge/raylib%20%28pyray%29-6.0.1-black)
![NumPy](https://img.shields.io/badge/NumPy-2.3.5-013243?logo=numpy&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20progress-orange)

Diorama interaktif 3D sebuah pulau melayang dengan kastil, dermaga kapal langit, bendera raksasa, dan kawanan wyvern. Proyek akhir mata kuliah **Animasi Komputer** (Semester 5, dosen Med Irzal). Dikembangkan dengan **Python, raylib (`pyray`), dan NumPy**. Algoritma animasi dan simulasi diimplementasikan di Python tanpa mesin fisika eksternal.

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Fitur](#fitur)
- [Status Pengerjaan](#status-pengerjaan)
- [World Statis dan Cakupan GLB](#world-statis-dan-cakupan-glb)
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

Diorama ini dirancang untuk menghubungkan tiga modul simulasi dalam satu adegan.

- **Kapal langit** berputar mengelilingi pulau di jalur Catmull-Rom tertutup dengan kecepatan konstan, lalu melambat saat mendekati titik tambat.
- **Bendera raksasa** di menara utara berkibar karena angin, dan berkibar lebih kencang saat kapal lewat.
- **Kawanan wyvern** terbang di atas kastil, menghindari menara, dan berpencar saat kapal menembus mereka. Kapal pun melambat kalau banyak wyvern di depannya.

Integrasi akan memakai satu `dt` dari game loop. Target aplikasi gabungan adalah **60 FPS pada 1280 × 720**, yang masih perlu diukur pada laptop demo.

## Fitur

| Modul | Materi | Isi |
| :--- | :--- | :--- |
| **A — Kapal langit** | P5–P7: kurva & gerak terkendali | Catmull-Rom tertutup 3D, tabel arc-length (kecepatan konstan), ease-in/out ke dermaga, arah hadap dari tangen kurva |
| **C — Bendera kastil** | P15–P16: pegas & kain | Pegas-massa dan Verlet + constraint jarak (12 grup), angin per segitiga, render dua sisi dengan satu panggilan gambar per segitiga, 4 substep × 2 iterasi |
| **D — Kawanan wyvern** | P17–P18: boids | Direncanakan memakai cohesion, separation, dan alignment dalam 3D, serta penghindaran menara dan kapal |

Setiap modul dirancang memiliki kontrol dan metrik di layar, seperti regangan kain, simpangan kecepatan kapal, atau polarisasi kawanan. HUD gabungan akan menampilkan FPS.

## Status Pengerjaan

- [x] Repo, `.gitignore`, `requirements.txt`, dan kode praktikum A serta C di `reference/dosen/`
- [x] Modul A mempunyai inti gerak kapal, rute tertutup 3D, arc-length, ease, keluaran keadaan kapal, dan respons terhadap masukan jumlah boid di depan.
- [x] Modul C mempunyai harness mandiri dengan kapal tiruan, kontrol, dan HUD. `F1` menyalakan atau mematikan pengaruh kapal tiruan pada kain.
- [x] Viewer `world_scene.py` memuat lingkungan statis C14, dengan kamera orbit dan mode pembanding primitif W3.
- [ ] Harness mandiri Modul A dengan visualisasi, kontrol, dan HUD.
- [ ] Modul D dan harness mandiri kawanan wyvern 3D.
- [ ] `main.py` untuk satu game loop, HUD gabungan, bantuan `H`, rekam CSV, dan interaksi langsung A↔D serta A→C.
- [ ] Pengujian clearance dan pengukuran aplikasi gabungan di laptop demo, lalu laporan, video, dan slide.
- [ ] Bendera kecil di dermaga sebagai tambahan Tier 2.

## World Statis dan Cakupan GLB

Viewer saat ini menampilkan lingkungan C14 yang disiapkan di Blender dan diekspor sebagai [GLB statis](assets/skyport_world.glb). Jalur ini memberi detail pada tebing, courtyard, rampart, dan struktur dermaga. GLB dipakai untuk menggambar lingkungan. Gerak serta interaksi kapal, bendera, dan kawanan tetap menjadi tanggung jawab modul Python.

Brief v3.1 §4.2 menetapkan primitif Raylib sebagai baseline. Penggunaan GLB untuk versi pengumpulan **masih menunggu konfirmasi langsung dari dosen**. Mode `--primitives` menyediakan world W3 sebagai pembanding dan dasar cadangan jika primitif diwajibkan. Lihat [README aset](assets/README.md) untuk cara menjalankan kedua mode.

## Tech Stack

- **Python 3.13**
- **raylib 6.0.1** lewat `pyray`: jendela, input, kamera, dan menggambar saja
- **NumPy 2.3.5**: semua perhitungan simulasi

Versi dipatok di [`requirements.txt`](requirements.txt), sama dengan laptop demo (HP Victus 15).

## Menjalankan Secara Lokal

Clone repo dengan perintah berikut.

```bash
git clone https://github.com/Nand-o/aether-castle-skyport.git
cd aether-castle-skyport
```

Buat virtual environment Python 3.13 dan pasang dependensi.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Viewer world dan harness kain bisa dijalankan secara mandiri.

```bash
python world_scene.py                 # world statis C14
python world_scene.py --primitives    # pembanding W3
python mod_c_cloth.py                 # bendera kastil + kapal tiruan
```

Program lengkap (`python main.py`) menyusul setelah integrasi.

## Kontrol

Pada viewer world, panah kiri dan kanan memutar kamera. Pada harness kain, tekan `H` untuk melihat kontrol dan `F1` untuk menguji pengaruh kapal tiruan. Tabel berikut adalah peta kontrol aplikasi gabungan.

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

## Interaksi Antarmodul

Interaksi berikut akan dihubungkan lewat `main.py`.

| Tombol | Arah | Data | Efek |
| :---: | :---: | :--- | :--- |
| `F2` | A → D | Posisi kapal | Kapal menjadi pemangsa; kawanan berpencar lalu berkumpul lagi |
| `F3` | D → A | Jumlah wyvern di depan kapal | Kapal melambat sampai 50 % |
| `F1` | A → C | Posisi dan kecepatan kapal | Angin tambahan di sekitar bendera saat kapal lewat |

A↔D adalah pasangan dua arah dan A→C adalah interaksi ketiga. `main.py` akan meneruskan keluaran setiap modul ke modul lain.

## Struktur Repo

```text
aether-castle-skyport/
├── main.py              # game loop bersama (menyusul)
├── world_scene.py       # viewer lingkungan statis dan kamera orbit
├── assets/             # GLB lingkungan dan README aset
├── mod_a_skyship.py     # Modul A: kapal langit
├── mod_c_cloth.py       # Modul C: bendera kastil
├── mod_d_boids.py       # Modul D: kawanan wyvern (menyusul)
├── reference/dosen/     # kode praktikum dosen, tidak diubah
└── requirements.txt     # dependensi program
```

## Tim

| Anggota | GitHub | Bagian yang dikerjakan | PJ demo dan tanya jawab |
| :--- | :--- | :--- | :--- |
| Nando | [@Nand-o](https://github.com/Nand-o) | Modul C, `world_scene.py`, dan pennant sebagai Tier 2 | Modul C |
| Faris | [@farismlna](https://github.com/farismlna) | Implementasi A, rencana implementasi D dan `main.py`, serta README | Modul D dan cadangan Modul A |
| Anggota 3 | *(menyusul)* | Nama dan kontribusi akan dilengkapi | Modul A |

## Atribusi Kode

Kode praktikum yang sudah diadopsi disimpan utuh di [`reference/dosen/`](reference/dosen/). Riwayat Modul A dan C mencatat versi awal kode dosen dan perubahan setelahnya. Label pada kode menunjukkan sumber per bagian.

| Label | Arti |
| :--- | :--- |
| `[DOSEN]` | Dari kode praktikum dosen, tidak diubah atau hanya diubah sedikit |
| `[KAMI]` | Ditulis kelompok |
| `[AI]` | Bagian yang dibuat atau direvisi dengan bantuan asisten AI |

| Bagian | Sumber | Pengembangan |
| :--- | :--- | :--- |
| `mod_a_skyship.py` | `catmull_rom_p7.py`, bantuan AI pada blok berlabel | Jalur tertutup 3D, rute 11 titik, arah dari tangen, serta metrik kapal. |
| `mod_c_cloth.py` | `cloth_p16.py`, bantuan AI pada blok berlabel | Bendera 14 × 20, angin kapal, substep dan iterasi Verlet, serta render dua sisi. |
| `world_scene.py` | Brief tim, contoh kamera dari `cloth_p16.py`, dan bantuan AI pada blok berlabel | Nando memilih C14 dan menetapkan GLB untuk lingkungan statis. Kode world menyediakan landmark, orbit, jalur GLB, dan pembanding W3. |
| `assets/skyport_world.glb` | Ekspor Blender C14 dengan bantuan AI berdasarkan brief dan referensi visual tim | Geometri dan tekstur lingkungan statis. |

## Rujukan

- Parent, R. (2012). *Computer Animation: Algorithms and Techniques* (3rd ed.). Morgan Kaufmann.
- Reynolds, C. W. (1987). Flocks, herds and schools: A distributed behavioral model. *SIGGRAPH '87*.
- Provot, X. (1995). Deformation constraints in a mass-spring model to describe rigid cloth behavior. *Graphics Interface '95*.
- Jakobsen, T. (2001). Advanced character physics. *GDC*.
- Kode praktikum Animasi Komputer (Med Irzal) di repo meliputi `catmull_rom_p7.py`, `spring_mass_p15.py`, `cloth_p16.py`, dan `particles_p17.py`. Rujukan `boids_p18.py` direncanakan untuk Modul D.

## Kontribusi

Aturan cabang, pesan commit, dan pull request ada di [CONTRIBUTING.md](CONTRIBUTING.md).
