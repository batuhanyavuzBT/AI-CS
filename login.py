from flask import Flask, request, render_template_string, render_template, redirect, url_for, jsonify
import csv
import os
from datetime import datetime
import re
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from apscheduler.schedulers.background import BackgroundScheduler
from scapy.all import sniff



app = Flask(__name__)

# HTML formu
LOGIN_FORM = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giriş Yap</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .login-container {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            width: 300px;
        }
        .login-container h1 {
            margin: 0 0 20px;
            text-align: center;
            font-size: 24px;
            color: #333;
        }
        .login-container label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        .login-container input {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .login-container button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            border: none;
            border-radius: 4px;
            color: #fff;
            font-size: 16px;
            cursor: pointer;
        }
        .login-container button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Giriş Yap</h1>
        <form method="post">
            <label for="username">Kullanıcı Adı</label>
            <input type="text" id="username" name="username" required>
            <label for="password">Şifre</label>
            <input type="password" id="password" name="password" required>
            <button type="submit">Giriş Yap</button>
        </form>
        {% if error %}
            <p style="color: red;">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
'''

def verify_user(username, password):
    with open('login.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['kullanici'] == username and row['sifre'] == password:
                return True
    return False

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            return redirect(url_for('success'))
        else:
            error = 'Kullanıcı adı veya şifre yanlış.'
    return render_template_string(LOGIN_FORM, error=error)

@app.route('/success')
def success():
    return render_template('anasayfa.html')

# Log dosyasının yolu
LOG_FILE_PATH = r'C:\Users\YAU9BU\Desktop\proje_spyder\templates\log.txt'
MODEL_FILE_PATH = r'C:\Users\YAU9BU\Desktop\proje_spyder\anomaly_model.csv'  # Model dosya yolu

@app.route('/send-request', methods=['POST'])
def send_request():
    data = request.json
    
    # JSON verisinin byte cinsinden boyutu
    data_size = len(str(data).encode('utf-8'))
    
    log_entry = (f"Request received at {datetime.now()}: {data}\n"
                 f"Data size: {data_size} bytes\n")

    try:
        # Log dosyasını aç ve log girdisini ekle
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(log_entry)
        return jsonify(data)
    except Exception as e:
        print(f"Failed to write to log file: {e}")
        return "Internal Server Error", 500

def get_file_size(file_path):
    """Dosyanın boyutunu bayt cinsinden döndürür."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def read_log_file(file_path):
    """Log dosyasını okur ve istek boyutlarını döndürür."""
    sizes = []
    size_pattern = re.compile(r'Data size: (\d+) bytes')
    
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
    try:
        joblib.dump(model, filename)
        print(f"Model başarıyla kaydedildi: {filename}")
    except Exception as e:
        print(f"Model kaydedilirken bir hata oluştu: {e}")

def load_model(filename):
    """Bir dosyadan eğitilen modeli yükler."""
    try:
        return joblib.load(filename)
    except Exception as e:
        print(f"Model yüklenirken bir hata oluştu: {e}")
        raise

def detect_anomalies(model, new_size):
    """Yeni istek boyutunun anormal olup olmadığını eğitilen model ile tespit eder."""
    prediction = model.predict(np.array([[new_size]]))
    return prediction == -1

def analyze_requests():
    sizes = read_log_file(LOG_FILE_PATH)
    
    if sizes.size == 0:
        print("Analiz edilecek veri yok.")
        return

    # Modeli eğit veya mevcut modeli yükle
    try:
        model = load_model(MODEL_FILE_PATH)
    except FileNotFoundError:
        model = train_model(sizes)
        save_model(model, MODEL_FILE_PATH)

    # Yeni istek boyutunu simüle et (bu değeri gerçek istek boyutlarıyla değiştirin)
    new_request_size = sizes[-1][0]  # En son boyut
    print(f"Yeni istek boyutu: {new_request_size} bytes")

    if detect_anomalies(model, new_request_size):
        print(f"Uyarı: Yeni istek boyutu {new_request_size} byte anormal.")
    else:
        print(f"Yeni istek boyutu {new_request_size} byte normal aralıkta.")

# Zamanlayıcıyı başlatma
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(analyze_requests, 'interval', minutes=10)  # Her 10 dakikada bir çalışır
    scheduler.start()
    

# # Dosya yolunu tanımlayın
# file_path = r"C:\Users\YAU9BU\Desktop\proje_spyder\sniff.txt"

# # Paketleri işleyen bir fonksiyon
# def packet_callback(packet):
#     with open(file_path, "a") as f:
#         f.write(f"{packet.summary()}\n")

# # Sniffer'ı başlatın
# try:
#     sniff(prn=packet_callback, store=0)
# except KeyboardInterrupt:
#     print("Trafik izleme durduruldu.")
    

if __name__ == '__main__':
    start_scheduler()
    app.run()
