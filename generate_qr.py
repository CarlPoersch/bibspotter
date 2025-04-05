import qrcode
import os

os.makedirs("QR_Codes", exist_ok=True)

for i in range(1, 10):
    tischname = f"Tisch {i}"
    img = qrcode.make(tischname)
    img.save(f"QR_Codes/qr_tisch_{i}.png")