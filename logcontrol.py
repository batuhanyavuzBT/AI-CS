import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import re
import os

# Log dosyasının yolu
LOG_FILE_PATH = r'C:\Users\YAU9BU\Desktop\proje_spyder\templates\log.txt'

def get_file_size(file_path):
    """Dosyanın boyutunu bayt cinsinden döndürür."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def read_log_file(file_path):
    """Log dosyasını okur ve istek boyutlarını döndürür."""
    sizes = []
    size_pattern = re.compile(r'Current log file size: (\d+) bytes')
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            match = size_pattern.search(line)
            if match:
                sizes.append(int(match.group(1)))
        return np.array(sizes).reshape(-1, 1)  # scikit-learn için uygun biçim
    except FileNotFoundError:
        print("Log dosyası bulunamadı.")
        return np.array([]).reshape(-1, 1)

def train_model(data):
    """Isolation Forest modelini eğitir."""
    model = IsolationForest(contamination=0.1)  # Anomali oranını gerektiği gibi ayarlayın
    model.fit(data)
    return model

def save_model(model, filename):
    """Eğitilen modeli bir dosyaya kaydeder."""
    joblib.dump(model, filename)

def load_model(filename):
    """Bir dosyadan eğitilen modeli yükler."""
    return joblib.load(filename)

def detect_anomalies(model, new_size):
    """Yeni istek boyutunun anormal olup olmadığını eğitilen model ile tespit eder."""
    prediction = model.predict(np.array([[new_size]]))
    return prediction == -1

def main():
    sizes = read_log_file(LOG_FILE_PATH)
    
    if sizes.size == 0:
        print("Analiz edilecek veri yok.")
        return

    # Modeli eğit veya mevcut modeli yükle
    model_filename = 'anomaly_model.pkl'
    try:
        model = load_model(model_filename)
    except FileNotFoundError:
        model = train_model(sizes)
        save_model(model, model_filename)

    # Yeni istek boyutunu simüle et (bu değeri gerçek istek boyutlarıyla değiştirin)
    new_request_size = get_file_size(LOG_FILE_PATH)  # Gerçek boyutu al
    print(f"Yeni istek boyutu: {new_request_size} bytes")

    if detect_anomalies(model, new_request_size):
        print(f"Uyarı: Yeni istek boyutu {new_request_size} byte anormal.")
    else:
        print(f"Yeni istek boyutu {new_request_size} byte normal aralıkta.")

if __name__ == "__main__":
    main()
