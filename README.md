# SMARTCITY-TRAFFIC 🚦

Sistem prediksi kemacetan lalu lintas dan rekomendasi rute alternatif berbasis AI untuk mendukung program Smart City di Kota Bengkulu.

## 📌 Deskripsi Proyek

SMARTCITY-TRAFFIC adalah aplikasi berbasis web yang dikembangkan dengan Streamlit dan Folium untuk memvisualisasikan data lalu lintas serta memberikan prediksi tingkat kemacetan secara real-time. Sistem ini juga dapat memberikan rekomendasi rute alternatif menggunakan layanan OpenRouteService.

## 🎯 Tujuan Proyek

* Memprediksi tingkat kemacetan lalu lintas berdasarkan parameter lingkungan dan lalu lintas aktual.
* Memberikan peringatan dini terhadap potensi kemacetan.
* Menyediakan rekomendasi rute alternatif bagi pengguna jalan.

## 🔍 Studi Kasus

Kota Bengkulu, sebagai bagian dari pengembangan Smart City, memerlukan sistem yang mampu menganalisis dan merespon kondisi lalu lintas secara cerdas dan cepat.

## 🧠 Model Kecerdasan Buatan

Model AI yang digunakan:

* XGBoost Regressor

  * Alasan pemilihan:

    * Performa tinggi untuk data tabular.
    * Mampu menangani fitur non-linear dan interaksi antar fitur.
    * Cepat dan efisien untuk inferensi real-time.

## 📊 Dataset

### Sumber Data

* Simulasi Data Lalu Lintas Bengkulu dalam model/traffic_data.csv
* Fitur:

  * datetime: waktu pengamatan
  * distance_km: jarak perjalanan dalam kilometer
  * num_segments: jumlah segmen jalan
  * temperature: suhu udara (°C)
  * rain: intensitas hujan (0–3)
  * traffic_level: tingkat kemacetan (target prediksi)

### Praproses

* Ekstraksi fitur waktu: jam, hari, dsb.
* Normalisasi / standardisasi data numerik.
* Pembagian data train-test.

## ⚙ Arsitektur Sistem

mermaid
graph TD;
  A[User Interface (Streamlit)] --> B[Prediksi Kemacetan (XGBoost)]
  A --> C[Peta Rute (Folium + OpenRouteService)]
  B --> D[Tampilan Prediksi dan Saran Rute]
  C --> D


Alur kerja:

1. Pengguna memasukkan waktu dan parameter lalu lintas.
2. Sistem memprediksi tingkat kemacetan menggunakan model AI.
3. Jika kemacetan tinggi, sistem menyarankan rute alternatif menggunakan OpenRouteService.

## 📈 Evaluasi Model

* Metrik evaluasi:

  * Mean Absolute Error (MAE)
  * Root Mean Squared Error (RMSE)
  * R² Score
* Strategi evaluasi:

  * Train-test split 80:20
  * Validasi silang (cross-validation) pada proses pelatihan model.

## 🧩 Struktur Proyek


SMARTCITY-TRAFFIC/
│
├── app.py                         # Aplikasi utama Streamlit
├── requirements.txt               # Daftar dependensi
├── README.md                      # Dokumentasi proyek
│
├── model/
│   ├── traffic_data.csv           # Dataset lalu lintas
│   ├── traffic_model.joblib       # Model terlatih (joblib)
│   ├── traffic_model_xgboost.json # Model terlatih (XGBoost JSON)
│   ├── train_model.py             # Script pelatihan model
│   └── model_metadata.json        # Metadata model


## ▶ Cara Menjalankan

### 1. Clone Repository

bash
git clone https://github.com/NamaKelompok/SMARTCITY-TRAFFIC.git
cd SMARTCITY-TRAFFIC


### 2. Install Dependencies

bash
pip install -r requirements.txt


### 3. Jalankan Aplikasi

bash
streamlit run app.py

## 🔮 Rencana Pengembangan

Berikut adalah beberapa fitur dan peningkatan yang direncanakan untuk versi berikutnya:

### ✅ Fitur yang Akan Ditambahkan

- 🔄 Integrasi Data Real-Time Lalu Lintas
  - Mengambil data kemacetan dari API seperti Google Maps Traffic atau HERE Traffic (jika tersedia untuk wilayah Bengkulu).
  - Membandingkan prediksi model dengan data real-time untuk evaluasi akurasi.

- 🧭 Opsi Algoritma Alternatif
  - Menambahkan pilihan algoritma pencarian rute seperti Dijkstra atau A\* sebagai alternatif OpenRouteService.

- 📊 Analisis Perbandingan Rute
  - Visualisasi perbandingan antara rute tercepat, terpendek, dan paling sedikit kemacetan.
  - Heatmap kemacetan di sekitar jalur utama di peta.

- 🗂 Riwayat dan Logging Penggunaan
  - Menyimpan riwayat rute yang dicari dan prediksi sebelumnya.
  - Logging aktivitas pengguna untuk analisis performa dan preferensi.

- 📈 Training Ulang Model AI
  - Menyediakan halaman khusus untuk upload dataset baru dan melatih ulang model XGBoost secara langsung.
  - Evaluasi performa model secara berkala.

- 📱 Versi Mobile Responsive
  - Membuat tampilan UI lebih ramah untuk perangkat mobile dan tablet.

- 🛜 Integrasi IoT dan Sensor
  - Mendukung input data dari sensor lalu lintas atau kamera CCTV untuk prediksi lebih akurat (jika tersedia).

## 🚀 Pengembangan Lanjutan

* Integrasi data real-time dari API lalu lintas (Waze, Google Traffic, atau IoT).
* Penambahan notifikasi berbasis lokasi.
* Visualisasi heatmap kemacetan.
* Integrasi dengan sistem transportasi umum dan peringatan cuaca ekstrem.
