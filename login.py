from flask import Flask, request, render_template_string, redirect, url_for, jsonify, render_template
import csv
import os
from datetime import datetime
import re
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GridSearchCV
import joblib
from apscheduler.schedulers.background import BackgroundScheduler
from collections import defaultdict
import time

app = Flask(__name__)
banned_ips = {}

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

# Kullanıcı doğrulama
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
MODEL_FILE_PATH = r'C:\Users\YAU9BU\Desktop\proje_spyder\anomaly_model.pkl'  # Model dosya yolu

# Kullanıcı isteklerini izlemek için veri yapısı
request_times = defaultdict(list)
TIME_WINDOW = 60  # Zaman penceresi (saniye cinsinden)

def update_request_times(ip_address):
    now = time.time()
    if ip_address not in request_times:
        request_times[ip_address] = []
    
    # Zaman damgalarını güncelle
    request_times[ip_address] = [timestamp for timestamp in request_times[ip_address] if now - timestamp < TIME_WINDOW]
    request_times[ip_address].append(now)

def prepare_data_for_model():
    now = time.time()
    data = []
    for ip, timestamps in request_times.items():
        request_count = len(timestamps)
        time_since_last_request = now - timestamps[-1] if timestamps else TIME_WINDOW
        
        data.append([request_count, time_since_last_request])
    
    return np.array(data)

def train_model_with_optimization(data):
    model = IsolationForest(random_state=42)
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_samples': ['auto', 0.6, 0.8],
        'contamination': [0.05, 0.1, 0.15],
        'max_features': [1, 2],
        'bootstrap': [False, True]
    }

    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    grid_search.fit(data, np.ones(data.shape[0]))
    print("En iyi hiperparametreler:", grid_search.best_params_)
    return grid_search.best_estimator_

def save_model(model, filename):
    try:
        joblib.dump(model, filename)
        print(f"Model başarıyla kaydedildi: {filename}")
    except Exception as e:
        print(f"Model kaydedilirken bir hata oluştu: {e}")

def load_model(filename):
    try:
        return joblib.load(filename)
    except Exception as e:
        print(f"Model yüklenirken bir hata oluştu: {e}")
        raise

def detect_anomalies(model, request_features):
    prediction = model.predict([request_features])
    return prediction == -1

@app.route('/send-request', methods=['POST'])
def send_request():
    data = request.json
    ip_address = request.remote_addr

    update_request_times(ip_address)
    
    # Verileri hazırlayın ve modeli yükleyin
    data_for_model = prepare_data_for_model()
    model = load_model(MODEL_FILE_PATH) if os.path.exists(MODEL_FILE_PATH) else None

    if model is None:
        # Eğer model mevcut değilse, verileri kullanarak yeni model eğitin
        if len(data_for_model) > 0:
            model = train_model_with_optimization(data_for_model)
            save_model(model, MODEL_FILE_PATH)
        else:
            model = IsolationForest(random_state=42)  # Varsayılan model

    # Yeni istek özelliklerini hesaplayın
    request_count = len(request_times[ip_address])
    time_since_last_request = time.time() - request_times[ip_address][-1] if request_times[ip_address] else TIME_WINDOW
    
    features = [request_count, time_since_last_request]
    
    # Anomali tespiti yapın
    if detect_anomalies(model, features):
        return jsonify({'error': 'Brute force attack detected'}), 403
    
    # JSON verisinin byte cinsinden boyutu
    data_size = len(str(data).encode('utf-8'))
    
    log_entry = (f"Request received at {datetime.now()}: {data}\n"
                 f"Data size: {data_size} bytes\n")

    try:
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(log_entry)
        return jsonify(data)
    except Exception as e:
        print(f"Failed to write to log file: {e}")
        return "Internal Server Error", 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open(LOG_FILE_PATH, 'r') as log_file:
            logs = log_file.readlines()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

def analyze_requests():
    sizes = read_log_file(LOG_FILE_PATH)
    
    if sizes.size == 0:
        print("Analiz edilecek veri yok.")
        return

    try:
        model = load_model(MODEL_FILE_PATH)
    except FileNotFoundError:
        model = train_model_with_optimization(sizes)
        save_model(model, MODEL_FILE_PATH)

    new_request_size = sizes[-1][0]  # En son boyut
    print(f"Yeni istek boyutu: {new_request_size} bytes")

    if detect_anomalies(model, [new_request_size]):
        print(f"Uyarı: Yeni istek boyutu {new_request_size} byte anormal. Kullanıcı IP'si uzaklaştırıldı.")
    else:
        print(f"Yeni istek boyutu {new_request_size} byte normal aralıkta.")

# Zamanlayıcıyı başlatma
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(analyze_requests, 'interval', minutes=10)
    scheduler.start()

if __name__ == '__main__':
    start_scheduler()
    app.run()

@app.route('/profil')
def profil():
    return render_template('profil.html')



