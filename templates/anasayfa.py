from flask import Flask, request, render_template, redirect, url_for
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Logging ayarları
log_file_path = 'C:/Users/YAU9BU/Desktop/proje_spyder/app.log'
handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Hem app.logger hem de root logger'a handler ekleme
app.logger.addHandler(handler)
logging.getLogger().addHandler(handler)

app.logger.setLevel(logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Test log mesajı
app.logger.info('Flask uygulaması başlatıldı ve loglama çalışıyor.')

@app.route('/anasayfa')
def anasayfa():
    success_message = request.args.get('success_message', '')
    return render_template('anasayfa.html', success_message=success_message)

@app.route('/anasayfa', methods=['POST'])
def log_data():
    user_input = request.form['user_input']
    app.logger.info(f'Kullanıcı girişi: {user_input}')
    return redirect(url_for('anasayfa', success_message='Veri başarıyla gönderildi!'))

if __name__ == '__main__':
    app.run(debug=True)
