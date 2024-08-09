from scapy.all import sniff
import os

# Dosya yolunu tanımlayın
file_path = r"C:\Users\YAU9BU\Desktop\proje_spyder\sniff.txt"

# Paketleri işleyen bir fonksiyon
def packet_callback(packet):
    with open(file_path, "a") as f:
        f.write(f"{packet.summary()}\n")

# Sniffer'ı başlatın
try:
    sniff(prn=packet_callback, store=0)
except KeyboardInterrupt:
    print("Trafik izleme durduruldu.")
