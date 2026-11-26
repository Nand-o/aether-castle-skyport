# World statis Aether Castle Skyport

## Menjalankan viewer

Dari root repo pada branch `world`, pasang dependensi dari `requirements.txt` lalu pilih mode viewer.

```powershell
python world_scene.py                 # GLB statis C14
python world_scene.py --primitives    # World W3 untuk perbandingan
```

Gunakan panah kiri dan kanan untuk memutar kamera.

## Alasan memilih GLB

Primitif Raylib di W3 memudahkan tim menguji skala, posisi landmark, dan kamera. Untuk tampilan akhir, bentuk-bentuk dasar itu belum memberi detail yang cukup pada tebing, halaman, dinding kastil, dan struktur dermaga. GLB memungkinkan lingkungan tersebut dimodelkan di Blender dan dibawa ke Raylib sebagai satu berkas berisi geometri, material, dan tekstur. glTF dirancang untuk pengiriman dan pemuatan aset 3D di aplikasi runtime. [Spesifikasi glTF dari Khronos](https://www.khronos.org/gltf/)

[`skyport_world.glb`](skyport_world.glb) berisi pulau, kastil, courtyard, rampart, dan dermaga. Raylib memuat model sekali setelah jendela dibuka. Simulasi kapal, kain, dan boids tetap berjalan pada modul Python masing-masing. Titik tambat, pin kain, dan proxy rintangan diteruskan melalui `get_landmarks()`.

Contoh referensi visual untuk pemodelan 3D dapat dilihat di [Poly Haven Models](https://polyhaven.com/models) dan [Kenney 3D Assets](https://kenney.nl/assets/category:3D).
