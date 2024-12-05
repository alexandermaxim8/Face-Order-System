import numpy as np

list_A = np.array(["kamen faiz", "B", "C", "F"])  # List yang ingin dicek
list_B = np.array(["kamen rider", "B", "C", "D", "E"])  # List referensi

# Menggunakan numpy.isin dengan negasi untuk menemukan elemen yang tidak ada
not_in_B_mask = ~np.isin(list_A, list_B)

# Menggunakan numpy.where untuk mendapatkan indeks elemen tersebut
not_in_B_indices = np.where(not_in_B_mask)[0]

# Output
print(f"Indeks elemen dari list_A yang tidak ada di list_B: {not_in_B_indices}")
print(f"Elemen dari list_A yang tidak ada di list_B: {list_A[not_in_B_indices]}")
