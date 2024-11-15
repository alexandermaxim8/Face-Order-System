import cv2
import face_recognition as FR
import glob
import os
import numpy as np
import pickle

# Inisialisasi list untuk encoding dan nama
known_encodings = []
known_names = []

# Nama file untuk menyimpan encoding dan nama
encodings_file = 'encodings_hitamputih.pkl'

# Cek apakah file encoding sudah ada
if os.path.exists(encodings_file):
    print("Memuat encoding wajah dari file...")
    with open(encodings_file, 'rb') as f:
        all_data = pickle.load(f)
        known_encodings = all_data['encodings']
        known_names = all_data['names']
else:
    print("Melakukan pelatihan dan menyimpan hasilnya...")
    # Mendapatkan daftar folder dalam 'dataset'
    dataset_dir = 'dataset'
    people_dirs = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]

    # Memuat dan meng-encode setiap gambar untuk setiap orang
    for person_name in people_dirs:
        person_dir = os.path.join(dataset_dir, person_name)
        # Mendapatkan semua file gambar untuk orang tersebut
        image_paths = glob.glob(os.path.join(person_dir, '*.jpg')) + \
                      glob.glob(os.path.join(person_dir, '*.jpeg')) + \
                      glob.glob(os.path.join(person_dir, '*.png'))

        for image_path in image_paths:
            # Memuat gambar dalam grayscale
            image_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            # Pastikan gambar berhasil dimuat
            if image_gray is None:
                print(f"Gagal memuat gambar {image_path}")
                continue

            # Konversi gambar grayscale menjadi gambar pseudo-RGB
            image_rgb = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2RGB)

            # Deteksi lokasi wajah menggunakan model HOG
            face_locations = FR.face_locations(image_rgb, model='hog')

            # Jika setidaknya ada satu wajah terdeteksi
            if len(face_locations) == 1:
                # Mendapatkan encoding wajah menggunakan lokasi wajah yang terdeteksi
                encodings = FR.face_encodings(image_rgb, known_face_locations=face_locations, num_jitters=100, model='large')
                known_encodings.append(encodings[0])
                known_names.append(person_name)
                print(f"Berhasil memproses gambar {image_path}")
            elif len(face_locations) == 0:
                print(f"Wajah tidak terdeteksi dalam gambar {image_path}")
            else:
                print(f"Lebih dari satu wajah terdeteksi dalam gambar {image_path}, melewati gambar ini.")

    # Simpan encoding dan nama ke dalam file
    with open(encodings_file, 'wb') as f:
        all_data = {'encodings': known_encodings, 'names': known_names}
        pickle.dump(all_data, f)
    print("Encoding wajah telah disimpan ke file.")

print("Proses pelatihan selesai.")
