import cv2
import face_recognition as FR
import os
import numpy as np
import pickle

# Pengaturan font untuk menampilkan teks
font = cv2.FONT_HERSHEY_SIMPLEX

# Pengaturan kamera
width = 360
height = 360
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cam.set(cv2.CAP_PROP_FPS, 20)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 3) 
cam.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))

# Inisialisasi list untuk encoding dan nama
known_encodings = []
known_names = []

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the encodings file
encodings_file = os.path.join(script_dir, 'encodings_hitamputih_part2.pkl')

# Memuat encoding wajah dan nama dari file pickle
with open(encodings_file, 'rb') as f:
    all_data = pickle.load(f)
    known_encodings = all_data['encodings']
    known_names = all_data['names']

# Variabel untuk kontrol frekuensi pemrosesan
process_this_frame = True
frame_skip = 2  # Proses setiap 2 frame
frame_count = 0

# Variabel untuk menyimpan hasil pengenalan sebelumnya
prev_face_locations = []
prev_face_names = []
pembagi=0.5
while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame_count += 1

    # Konversi frame ke grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame= cv2.equalizeHist(gray_frame)

    # # Ubah ukuran frame untuk mempercepat proses
    small_gray_frame = cv2.resize(gray_frame, (0, 0), fx=pembagi, fy=pembagi)

    if frame_count % frame_skip == 0:
        # Deteksi lokasi wajah dalam frame grayscale
        face_locations = FR.face_locations(small_gray_frame, model='hog')
        print("face_locations", np.shape(face_locations))

        # Untuk encoding wajah, kita perlu gambar RGB
        # Konversi frame kecil ke RGB
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Dapatkan encoding wajah
        face_encodings = FR.face_encodings(rgb_small_frame, face_locations)
        print("face_encodings", np.shape(face_encodings))
        face_names = []
        for face_encoding in face_encodings:
            print("face_encoding: ", face_encoding)
            # Bandingkan wajah dengan encoding yang dikenal
            matches = FR.compare_faces(known_encodings, face_encoding, tolerance=0.4)
            print("matches", matches)
            name = "Unknown"

            # Menggunakan jarak terkecil ke encoding yang dikenal
            face_distances = FR.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if face_distances[best_match_index] < 0.45:
                name = known_names[best_match_index]
                name += f' ({face_distances[best_match_index]:.2f})'  # Menambahkan nilai kepercayaan pada nama
            else:
                name = "Unknown"
                name += f' ({face_distances[best_match_index]:.2f})' 

            face_names.append(name)
        print("face_names: ", face_names)

        # Simpan hasil pengenalan untuk digunakan pada frame berikutnya
        prev_face_locations = face_locations
        prev_face_names = face_names
    else:
        # Gunakan hasil pengenalan sebelumnya
        face_locations = prev_face_locations
        face_names = prev_face_names

    # Menampilkan hasil pada frame grayscale
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Skala kembali lokasi wajah karena kita mengubah ukuran frame sebelumnya
        top /= pembagi
        right /= pembagi
        bottom /= pembagi
        left /= pembagi
        top = int(top)
        right = int(right)
        bottom = int(bottom)
        left = int(left)

        # Gambar kotak di sekitar wajah pada frame grayscale
        cv2.rectangle(gray_frame,(left, top), (right, bottom), (255), 2)

        # Tampilkan nama di bawah kotak
        cv2.rectangle(gray_frame, (left, bottom - 20), (right, bottom), (255), cv2.FILLED)
        cv2.putText(gray_frame, name, (left + 2, bottom - 5), font, pembagi, (0, 0, 0), 1)

    # Tampilkan frame hasil dalam grayscale
    cv2.imshow('Face Recognition', gray_frame)

    # Keluar jika tombol 'q' ditekan
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Membersihkan sumber daya
cam.release()
cv2.destroyAllWindows()
