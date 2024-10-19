import cv2
import face_recognition as FR
import dlib
import os
import numpy as np
import pickle
from scipy.spatial import distance as dist

# Pengaturan font untuk menampilkan teks
font = cv2.FONT_HERSHEY_SIMPLEX

# Pengaturan kamera
width = 640
height = 480
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cam.set(cv2.CAP_PROP_FPS, 30)  # Atur FPS sesuai kebutuhan Anda

# Inisialisasi list untuk encoding dan nama
known_encodings = []
known_names = []

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
print("lokasi folder: ", script_dir)
# Construct the full path to the encodings file
encodings_file = os.path.join(script_dir, 'encodings.pkl')
print("encoding file ", encodings_file)
# Memuat encoding wajah dan nama dari file pickle
with open(encodings_file, 'rb') as f:
    all_data = pickle.load(f)
    known_encodings = all_data['encodings']
    known_names = all_data['names']


# Inisialisasi detektor dan prediktor untuk facial landmarks
detector = dlib.get_frontal_face_detector()
facial_landmark_file=   os.path.join(script_dir,'shape_predictor_68_face_landmarks.dat')
print("facial landmark file ",facial_landmark_file)
predictor = dlib.shape_predictor(facial_landmark_file)  

# Fungsi untuk menghitung Eye Aspect Ratio (EAR)
def calculate_ear(eye):
    # Menghitung jarak Euclidean antara titik mata vertikal
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # Menghitung jarak Euclidean antara titik mata horizontal
    C = dist.euclidean(eye[0], eye[3])

    # Menghitung EAR
    ear = (A + B) / (2.0 * C)
    return ear

# Ambang batas EAR dan jumlah frame berturut-turut untuk menganggap kedipan
EAR_THRESHOLD = 0.21
EAR_CONSEC_FRAMES = 3

# Inisialisasi penghitung kedipan
blink_counter = 0
blink_total = 0
liveness = False

while True:
    ret, frame = cam.read()
    if not ret:
        break

    # Konversi ke grayscale untuk deteksi wajah dengan dlib
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Deteksi wajah menggunakan dlib
    faces = detector(gray, 0)

    face_names = []
    face_locations = []

    for face in faces:
        # Dapatkan koordinat wajah
        (x, y, w, h) = (face.left(), face.top(), face.width(), face.height())

        # Prediksi facial landmarks
        shape = predictor(gray, face)
        shape_np = np.zeros((68, 2), dtype=int)
        for i in range(0, 68):
            shape_np[i] = (shape.part(i).x, shape.part(i).y)

        # Mendapatkan koordinat mata kiri dan kanan
        left_eye = shape_np[36:42]
        right_eye = shape_np[42:48]

        # Menghitung EAR untuk mata kiri dan kanan
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        ear = (left_ear + right_ear) / 2.0

        # Periksa apakah EAR di bawah ambang batas
        if ear < EAR_THRESHOLD:
            blink_counter += 1
        else:
            if blink_counter >= EAR_CONSEC_FRAMES:
                blink_total += 1
                liveness = True
            blink_counter = 0

        # Gambar poligon pada mata (opsional)
        # cv2.polylines(frame, [left_eye], True, (0, 255, 0), 1)
        # cv2.polylines(frame, [right_eye], True, (0, 255, 0), 1)

        # Konversi koordinat untuk face_recognition
        top = y
        right = x + w
        bottom = y + h
        left = x

        face_locations.append((top, right, bottom, left))

    # Jika liveness terdeteksi, lakukan pengenalan wajah
    if liveness:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Dapatkan encoding wajah
        face_encodings = FR.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            # Bandingkan wajah dengan encoding yang dikenal
            matches = FR.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            # Menggunakan jarak terkecil ke encoding yang dikenal
            face_distances = FR.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if face_distances[best_match_index] < 0.4:
                name = known_names[best_match_index]
                name += f' ({face_distances[best_match_index]:.2f})'
            else:
                name = "Unknown"
                name += f' ({face_distances[best_match_index]:.2f})'

            face_names.append(name)
            print(name)
    else:
        face_names = ["Tidak ada kedipan terdeteksi"]
        # Anda dapat memilih untuk tidak menampilkan nama jika liveness tidak terdeteksi

    # Menampilkan hasil
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Gambar kotak di sekitar wajah
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Tampilkan nama di bawah kotak
        cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, name, (left + 2, bottom - 5), font, 0.6, (0, 0, 0), 1)

    # Tampilkan jumlah kedipan (opsional)
    cv2.putText(frame, f'Kedipan: {blink_total}', (10, 30), font, 0.7, (0, 0, 255), 2)

    # Tampilkan frame hasil
    cv2.imshow('Face Recognition with Liveness Detection', frame)

    # Reset liveness untuk frame berikutnya
    liveness = False

    # Keluar jika tombol 'q' ditekan
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Membersihkan sumber daya
cam.release()
cv2.destroyAllWindows()
