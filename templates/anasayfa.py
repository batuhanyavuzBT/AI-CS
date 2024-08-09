from flask import Flask, request, render_template, redirect, url_for, jsonify
import logging
from logging.handlers import RotatingFileHandler
import re

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

# Telefon numarası doğrulama regex (Güncellenmiş)
phone_number_regex = re.compile(r'^\+?(\d{1,3})?[-.\s]?(\(?\d{1,4}\)?)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$')

@app.route('/anasayfa')
def anasayfa():
    success_message = request.args.get('success_message', '')
    return render_template('anasayfa.html', success_message=success_message)

@app.route('/anasayfa', methods=['POST'])
def log_data():
    user_input = request.form['user_input']
    
    # Telefon numarasını doğrula
    if phone_number_regex.match(user_input):
        app.logger.info(f'Kullanıcı girişi: {user_input}')
        return redirect(url_for('anasayfa', success_message='Veri başarıyla gönderildi!'))
    else:
        return redirect(url_for('anasayfa', success_message='Geçersiz telefon numarası!'))


if __name__ == '__main__':
    app.run()
    