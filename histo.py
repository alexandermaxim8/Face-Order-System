# import Opencv
import cv2
import  os

# import Numpy
import numpy as np
dataset_dir = 'dataset'
lokasi_folder=os.listdir(dataset_dir)[1]
print(lokasi_folder)
# read a image using imread
img = cv2.imread("dataset/satwika/satwika4.jpg")



# Konversi gambar berwarna ke grayscale
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# # Tampilkan gambar asli dan hasil konversi
# cv2.imshow("Gambar Berwarna", img)
# cv2.imshow("Gambar Hitam Putih", img_gray)


# # creating a Histograms Equalization
# # of a image using cv2.equalizeHist()
equ = cv2.equalizeHist(img_gray)

# # stacking images side-by-side
res = np.hstack((img_gray, equ))

# # show image input vs output
cv2.imshow("halo", res)

cv2.waitKey(0)
cv2.destroyAllWindows()