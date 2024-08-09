from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# Log dosyasının yolu
LOG_FILE_PATH = r'C:\Users\YAU9BU\Desktop\proje_spyder\templates\log.txt'

def get_file_size(file_path):
    """Dosyanın boyutunu bayt cinsinden döndürür."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

@app.route('/send-request', methods=['POST'])
def send_request():
    data = request.json
    file_size = get_file_size(LOG_FILE_PATH)
    log_entry = (f"Request received at {datetime.now()}: {data}\n"
                 f"Current log file size: {file_size} bytes\n")

    try:
        # Log dosyasını aç ve log girdisini ekle
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(log_entry)
        return jsonify(data)
    except Exception as e:
        print(f"Failed to write to log file: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    # Sunucuyu localhost'ta çalıştır
    app.run(host='127.0.0.1', port=5000)  
