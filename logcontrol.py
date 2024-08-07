import pandas as pd
from sklearn.ensemble import IsolationForest
import logging

log_file = 'YAU9BU/Desktop/proje_spyder/app.log'

log_df = pd.read_csv(log_file, sep=' - ', header=None, engine='python', names=['timestamp', 'level', 'message'])


log_df['length'] = log_df['message'].apply(len)

# burada model oluşturma ve eğitme yaptım %10 daki farklı kısım anormal veri olarak girdim.
model = IsolationForest(contamination=0.1)
log_df['anomaly'] = model.fit_predict(log_df[['length']])

# Anormal kayıtları filtreleme
anomalies = log_df[log_df['anomaly'] == -1]

if not anomalies.empty:
    print("Anormal Kayıtlar Tespit Edildi:")
    print(anomalies)
else:
    print("Anormal Kayıt Tespit Edilmedi.")
 