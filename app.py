import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- خادم ويب بسيط لإبقاء Render نشطاً ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# تشغيل خادم الويب في خيط منفصل
threading.Thread(target=run_health_server, daemon=True).start()
# ---------------------------------------------
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import requests
import time
from datetime import datetime

# ==========================================
# 1. الإعدادات (عدلها حسب رغبتك)
# ==========================================
TELEGRAM_TOKEN = "9226715244:AAEeCy1VXbcTEBR_C_ZjtS8h85-sISzAMAc"
TELEGRAM_CHAT_ID = "5216572128"

# قائمة الأصول التي تريد مراقبتها
TICKERS = ["BTC-USD", "ETH-USD", "EURUSD=X", "GC=F"] 

# نسبة الاحتمال المطلوبة لإرسال الإشعار
THRESHOLD = 80 

# الوقت بين كل فحص (بالثواني). 900 ثانية = 15 دقيقة
SLEEP_TIME = 900 

# ==========================================
# 2. دالة إرسال الرسائل
# ==========================================
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except:
        print("فشل إرسال الإشعار")

# ==========================================
# 3. دالة التحليل
# ==========================================
def analyze_ticker(ticker):
    try:
        # جلب البيانات (آخر شهر، شموع ساعة)
        data = yf.download(ticker, period="1mo", interval="1h", progress=False)
        if data.empty:
            return None, None

        # حساب المؤشرات
        data['MA_10'] = data['Close'].rolling(window=10).mean()
        data['MA_50'] = data['Close'].rolling(window=50).mean()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
        data = data.dropna()

        if len(data) < 50: return None, None

        # تدريب النموذج
        features = ['MA_10', 'MA_50', 'RSI']
        X = data[features]
        y = data['Target']
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        # التوقع لآخر شمعة
        latest_data = X.tail(1)
        prediction = model.predict(latest_data)
        probability = model.predict_proba(latest_data)
        
        prob = 0
        direction = ""
        
        if prediction[0] == 1:
            prob = probability[0][1] * 100
            direction = "صعود (BUY) 📈"
        else:
            prob = probability[0][0] * 100
            direction = "هبوط (SELL) 📉"
            
        return prob, direction

    except Exception as e:
        print(f"خطأ في تحليل {ticker}: {e}")
        return None, None

# ==========================================
# 4. حلقة التشغيل المستمرة (24/7)
# ==========================================
print("🤖 بدأ البوت العمل... جاري المراقبة.")

while True:
    print(f"\n⏰ جاري الفحص: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for ticker in TICKERS:
        prob, direction = analyze_ticker(ticker)
        
        if prob is not None:
            print(f"{ticker}: {direction} بنسبة {prob:.2f}%")
            
            # إذا تجاوزت النسبة الحد المطلوب
            if prob >= THRESHOLD:
                msg = f"🚨 إشارة تلقائية قوية!\n\nالأصل: {ticker}\nالاتجاه: {direction}\nالاحتمال: {prob:.2f}%\nالوقت: {datetime.now().strftime('%H:%M')}"
                send_telegram_alert(msg)
                print("✅ تم إرسال إشعار تيليجرام!")
                
    print(f"😴 البوت سينام لمدة {SLEEP_TIME // 60} دقيقة قبل الفحص القادم...")
    time.sleep(SLEEP_TIME)