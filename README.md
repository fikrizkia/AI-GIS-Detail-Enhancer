# 🛰️ AI GIS & Satellite Map Detail Upscaler

A high-performance, standalone local web dashboard to upscale and reconstruct high-frequency details from GIS maps, blueprint blueprints, and satellite images. Powered by **FastAPI** (Python backend) and a **Vanilla HTML5/JS/CSS** frontend.

[English Version](#english) | [Versi Bahasa Indonesia](#bahasa-indonesia)

---

## Bahasa Indonesia

### 🌟 Fitur Utama
* **Teknologi AI Super-Resolution**:
  - **Real-ESRGAN (Vulkan GPU)**: Merekonstruksi detail tekstur jalan, pepohonan, sungai, dan bangunan pada peta secara realistis. Berjalan di GPU tanpa membutuhkan instalasi berat (tanpa PyTorch/CUDA).
  - **EDSR (Enhanced Deep Residual Networks)**: Menghasilkan tepian (edges) yang bersih dan tajam tanpa halusinasi buatan.
  - **FSRCNN**: Model AI super cepat untuk proses real-time (hanya beberapa detik).
  - **Pillow Lanczos**: Resampling tradisional berkualitas tinggi (instan).
* **Tiled Upscaling (Anti-Crash)**: Membagi gambar raksasa (seperti peta ukuran 5760x4096) menjadi bagian-bagian kecil (tiles), memprosesnya secara terpisah, dan menggabungkannya kembali dengan teknik blending khusus untuk menghindari error kehabisan memori (*Out-Of-Memory*).
* **Ringan untuk GitHub**: Semua file biner executable (`.exe`, `.dll`) dan file bobot model AI yang besar (~100MB+) disimpan **di luar folder proyek** (dalam cache lokal komputer Anda). Ini membuat folder proyek Anda sangat ringan dan siap diunggah ke GitHub secara instan!
* **Crop Optimization (Ultra-Fast Preview)**: Memotong area kecil (~300px) di tengah gambar asli dan upscaled untuk dibandingkan secara berdampingan tanpa memperlambat browser Anda.
* **Unduh PNG Lossless**: Tombol download bawaan untuk menyimpan hasil dalam format `.png` tanpa penurunan kualitas (lossless).
* **Instalasi Otomatis**: Secara otomatis memasang pustaka Python yang kurang dan mengunduh model AI ke folder cache luar saat aplikasi dijalankan pertama kali.

---

### 📁 Struktur Proyek (Ringan & Siap untuk GitHub)
Folder `GIS/` Anda hanya berisi file-file source code ringan berikut:
```text
GIS/
├── static/
│   └── index.html      # Tampilan antarmuka (Frontend UI)
├── server.py           # Server FastAPI & Mesin Upscale (Backend)
└── README.md           # Dokumentasi ini (file ini)
```
*(Semua biner berat dan model AI secara otomatis disimpan di `C:\Users\acer\.upscaler_cache\` di komputer Anda sehingga tidak akan ikut terunggah ke GitHub).*

---

### 💻 Cara Instalasi & Menjalankan

#### 1. Prasyarat
Pastikan Anda sudah menginstal Python (versi 3.8 ke atas) di sistem Anda.

#### 2. Jalankan Server
Buka terminal / PowerShell di dalam folder proyek Anda, lalu jalankan perintah:
```bash
python GIS/server.py
```
*Catatan: Pada saat pertama kali dijalankan, server akan otomatis mendeteksi dan menginstal pustaka yang diperlukan (`fastapi`, `uvicorn`, `opencv-contrib-python`, `pillow`, `requests`) serta menyiapkan biner pendukung di folder cache luar komputer Anda.*

#### 3. Akses Dashboard
Buka browser web Anda lalu akses alamat berikut:
```text
http://localhost:8050
```

---

### 🛠️ Panduan Penggunaan
1. **Pilih Gambar**: Pilih gambar Anda (misal `GIS 1.png` atau `GIS 2.png`) pada dropdown menu di panel kiri.
2. **Pilih Algoritma**:
   - Gunakan **Real-ESRGAN** untuk peta satelit/foto dunia nyata demi detail terbaik.
   - Gunakan **FSRCNN** dengan skala **2x** jika Anda ingin proses selesai dalam hitungan detik.
3. **Pilih Skala**: Pilih skala **2x**, **3x**, atau **4x** (skala 2x jauh lebih cepat dan hemat RAM).
4. **Klik Execute**: Klik tombol **Execute AI Upscaling**. Indikator loading dan timer akan muncul.
5. **Bandingkan & Unduh**:
   - Setelah selesai, tab **Side-by-Side Detail** akan aktif secara otomatis untuk melihat perbandingan ketajaman.
   - Klik tombol **Download PNG** berwarna hijau untuk mengunduh hasilnya langsung ke komputer Anda.
   - Gambar hasil upscale juga tersimpan otomatis di dalam folder `GIS/` Anda.

---

<br>

---

## English

### 🌟 Key Features
* **AI Super-Resolution Technologies**:
  - **Real-ESRGAN (Vulkan GPU)**: Reconstructs realistic high-frequency textures of roads, trees, rivers, and buildings on satellite maps. Runs on GPU via Vulkan without heavy framework installations (no PyTorch/CUDA required).
  - **EDSR (Enhanced Deep Residual Networks)**: Reconstructs clean, sharp borders and structures without artificial GAN hallucinations.
  - **FSRCNN**: Real-time super-resolution model for fast executions (takes only a few seconds).
  - **Pillow Lanczos**: Traditional mathematical resampling (instant).
* **Tiled Upscaling (Anti-Crash)**: Slices massive images (e.g., 5760x4096 maps) into smaller tiles, processes them independently, and blends them back together using overlapping boundaries to prevent *Out-Of-Memory* (OOM) crashes.
* **GitHub-Friendly (Lightweight)**: All heavy executable files (`.exe`, `.dll`) and large AI model weights (~100MB+) are stored **outside of the project directory** (in your local home cache folder). This keeps your project folder lightweight and instantly uploadable to GitHub!
* **Crop Optimization (Ultra-Fast Preview)**: Extracts a small center crop (~300px) from both the original and upscaled images to show side-by-side comparison without freezing the web browser.
* **Lossless PNG Download**: Seamless integrated browser download button for saving output files in lossless `.png` format.
* **Auto Setup**: Automatically installs missing Python packages and downloads AI model files to the external cache folder on first run.

---

### 📁 Project Structure (Lightweight & GitHub-Ready)
Your `GIS/` directory contains only these lightweight source files:
```text
GIS/
├── static/
│   └── index.html      # Web user interface (Frontend UI)
├── server.py           # FastAPI Web Server & Upscale Core (Backend)
└── README.md           # This documentation (this file)
```
*(All heavy binaries and models are automatically cached in `C:\Users\acer\.upscaler_cache\` on your local drive and will not be uploaded to GitHub).*

---

### 💻 Installation & Startup

#### 1. Prerequisites
Make sure you have Python (version 3.8 or newer) installed on your system.

#### 2. Start the Server
Open a terminal / command prompt in your project root directory and execute:
```bash
python GIS/server.py
```
*Note: On its first run, the backend will automatically install required Python libraries (`fastapi`, `uvicorn`, `opencv-contrib-python`, `pillow`, `requests`) and set up the portable binaries in your computer's external cache.*

#### 3. Access the Dashboard
Open your web browser and navigate to:
```text
http://localhost:8050
```

---

### 🛠️ Usage Guide
1. **Select Image**: Choose your image (e.g., `GIS 1.png` or `GIS 2.png`) from the dropdown in the configuration panel.
2. **Select Algorithm**:
   - Use **Real-ESRGAN** for satellite maps and photos to get the highest texture details.
   - Use **FSRCNN** with **2x** scale if you need a quick upscale (takes ~40 seconds).
3. **Select Scale**: Choose **2x**, **3x**, or **4x** (2x is 4x faster and uses less memory).
4. **Execute**: Click the **Execute AI Upscaling** button. A progress screen with a timer will appear.
5. **Compare & Download**:
   - Upon completion, the dashboard will switch to the **Side-by-Side Detail** tab for visual comparison.
   - Click the green **Download PNG** button to save the lossless file to your computer.
   - The upscaled file is also automatically saved in your local `GIS/` directory.
