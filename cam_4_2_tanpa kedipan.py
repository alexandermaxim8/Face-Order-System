import cv2
import face_recognition as FR
import os
import numpy as np
import pickle

# Pengaturan font untuk menampilkan teks
font = cv2.FONT_HERSHEY_SIMPLEX

# Pengaturan kamera
width = 640
height = 480
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cam.set(cv2.CAP_PROP_FPS, 60)
cam.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))

# Inisialisasi list untuk encoding dan nama
known_encodings = []
known_names = []

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the encodings file
encodings_file = os.path.join(script_dir, 'encodings.pkl')

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
# Fungsi untuk mengonversi face distance menjadi nilai kepercayaan


while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame_count += 1

    # Ubah ukuran frame untuk mempercepat proses
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Konversi ke RGB (face_recognition menggunakan format RGB)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if frame_count % frame_skip == 0:
        # Hanya proses setiap 'frame_skip' frame
        # Deteksi lokasi wajah dan encoding dalam frame saat ini
        face_locations = FR.face_locations(rgb_small_frame, model='hog')
        face_encodings = FR.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # Bandingkan wajah dengan encoding yang dikenal
            matches = FR.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            # Menggunakan jarak terkecil ke encoding yang dikenal
            face_distances = FR.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if face_distances[best_match_index] < 0.4: # Jika jarak terkecil kurang dari 0.4, maka wajah dikenali
                name = known_names[best_match_index]
                name += f' ({face_distances[best_match_index]:.2f})'  # Menambahkan nilai kepercayaan pada nama
            else:
                name = "Unknown"
                name += f' ({face_distances[best_match_index]:.2f})' 

            face_names.append(name)
            print(face_names)

        # Simpan hasil pengenalan untuk digunakan pada frame berikutnya
        prev_face_locations = face_locations
        prev_face_names = face_names
    else:
        # Gunakan hasil pengenalan sebelumnya
        face_locations = prev_face_locations
        face_names = prev_face_names

    # Menampilkan hasil
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Skala kembali lokasi wajah karena kita mengubah ukuran frame sebelumnya
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Gambar kotak di sekitar wajah
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Tampilkan nama di bawah kotak
        cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, name, (left + 2, bottom - 5), font, 0.6, (0, 0, 0), 1)

    # Tampilkan frame hasil
    cv2.imshow('Face Recognition', frame)

    # Keluar jika tombol 'q' ditekan
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Membersihkan sumber daya
cam.release()
cv2.destroyAllWindows()
