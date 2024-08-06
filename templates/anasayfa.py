from flask import Flask, request, render_template, redirect, url_for
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)


handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)


app.logger.setLevel(logging.INFO)

@app.route('/anasayfa')
def anasayfa():
    return render_template('anasayfa.html')

@app.route('/log', methods=['POST'])
def log_data():
    user_input = request.form['user_input']
    app.logger.info(f'Kullanıcı girişi: {user_input}')
    return redirect(url_for('anasayfa'))

if __name__ == '__main__':
    app.run() 
