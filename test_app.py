import unittest
import os
import json
import numpy as np
from flask import Flask
from your_app_file import app, LOG_FILE_PATH, train_model_with_optimization, detect_anomalies, save_model, load_model

class TestAnomalyDetection(unittest.TestCase):
    def setUp(self):
        # Bu metod her testten önce çalışır
        self.sizes = np.array([[100], [200], [150], [300], [120], [450], [320]])
        self.model = train_model_with_optimization(self.sizes)
    
    def test_train_model(self):
        # Modelin eğitildiğini doğrulayın
        self.assertIsNotNone(self.model)

    def test_detect_anomalies(self):
        # Normal bir boyut kontrolü (Normal olmalı)
        normal_size = 200
        result = detect_anomalies(self.model, normal_size)
        self.assertFalse(result, "Bu boyut normal olarak tespit edilmeliydi.")
        
        # Anormal bir boyut kontrolü (Anormal olmalı)
        anomalous_size = 1000  # Büyük bir boyut, model için anormal olabilir
        result = detect_anomalies(self.model, anomalous_size)
        self.assertTrue(result, "Bu boyut anormal olarak tespit edilmeliydi.")

    def test_save_and_load_model(self):
        # Modeli kaydet ve geri yükle
        test_model_path = 'test_model.pkl'
        save_model(self.model, test_model_path)
        loaded_model = load_model(test_model_path)
        self.assertIsNotNone(loaded_model)
        os.remove(test_model_path)

class TestAppIntegration(unittest.TestCase):
    def setUp(self):
        # Flask test istemcisini başlatın
        self.app = app.test_client()
        self.app.testing = True
        
        # Test için temiz bir log dosyası oluşturun
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
    
    def test_login_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Giriş Yap', response.data)
    
    def test_send_request(self):
        # Geçerli bir JSON isteği gönder
        response = self.app.post('/send-request', json={"key": "value"})
        self.assertEqual(response.status_code, 200)
        
        # Log dosyasının doğru şekilde oluşturulduğunu doğrula
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Log dosyasının içeriğini kontrol et
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_content = log_file.read()
            self.assertIn('Request received at', log_content)
            self.assertIn('Data size:', log_content)
    
    def test_logs_endpoint(self):
        # Önce bir istek göndererek log dosyasını doldur
        self.app.post('/send-request', json={"key": "value"})
        
        # Log dosyasını indirmeyi dene
        response = self.app.get('/logs')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
    
    def tearDown(self):
        # Testten sonra log dosyasını sil
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)

if __name__ == '__main__':
    unittest.main()
