import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import requests

# ==========================================
# إعدادات بوت التيليجرام (ضع بياناتك هنا)
# ==========================================
TELEGRAM_TOKEN = "AAEKEGLt3kAxY1eiydBmeoKOHOXdY4tvlJ0BotFather"
TELEGRAM_CHAT_ID = "5216572128userinfobot"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        # هذا السطر سيطبع رد تيليجرام في سجل التطبيق لمعرفة الخطأ
        st.write(f"رد تيليجرام: {response.json()}") 
    except Exception as e:
        st.error(f"فشل الاتصال بتيليجرام: {e}")

# ==========================================
# واجهة التطبيق
# ==========================================
st.set_page_config(page_title="تطبيق التوقعات الذكي", page_icon="📈", layout="centered")
st.title("📈 تطبيق التوقعات الذكي")
st.warning("⚠️ تنبيه: هذا التطبيق تعليمي. لا يوجد توقع بنسبة 100%.")

st.sidebar.header("إعدادات التطبيق")
ticker = st.sidebar.text_input("رمز السهم أو العملة", "BTC-USD")
period = st.sidebar.selectbox("الفترة الزمنية", ["1mo", "3mo", "6mo", "1y"], index=2)
interval = st.sidebar.selectbox("الإطار الزمني", ["1h", "1d"], index=0)

# إعدادات الإشعارات
st.sidebar.subheader("🔔 إعدادات الإشعارات")
alert_threshold = st.sidebar.slider("أرسل إشعار إذا تجاوزت النسبة:", 50, 99, 80)
enable_alerts = st.sidebar.checkbox("تفعيل إشعارات تيليجرام")

if st.button("🚀 تحليل وإعطاء توقع الآن"):
    with st.spinner("جاري جلب البيانات والتحليل..."):
        try:
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if data.empty:
                st.error("لم يتم العثور على بيانات لهذا الرمز.")
            else:
                data['MA_10'] = data['Close'].rolling(window=10).mean()
                data['MA_50'] = data['Close'].rolling(window=50).mean()
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
                data = data.dropna()
                
                features = ['MA_10', 'MA_50', 'RSI']
                X = data[features]
                y = data['Target']
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X, y)
                
                latest_data = X.tail(1)
                prediction = model.predict(latest_data)
                probability = model.predict_proba(latest_data)
                
                st.subheader("نتيجة التحليل:")
                
                if prediction[0] == 1:
                    prob_val = probability[0][1] * 100
                    st.success(f"**الاتجاه المتوقع: صعود (BUY) 📈**")
                    st.write(f"نسبة الاحتمال: **{prob_val:.2f}%**")
                    
                    # إرسال إشعار تيليجرام
                    if enable_alerts and prob_val >= alert_threshold:
                        msg = f"🚨 إشارة قوية!\nالأصل: {ticker}\nالاتجاه: صعود (BUY) 📈\nالاحتمال: {prob_val:.2f}%"
                        send_telegram_alert(msg)
                        st.info("📱 تم إرسال إشعار إلى تيليجرام!")
                        
                else:
                    prob_val = probability[0][0] * 100
                    st.error(f"**الاتجاه المتوقع: هبوط (SELL) 📉**")
                    st.write(f"نسبة الاحتمال: **{prob_val:.2f}%**")
                    
                    # إرسال إشعار تيليجرام
                    if enable_alerts and prob_val >= alert_threshold:
                        msg = f"🚨 إشارة قوية!\nالأصل: {ticker}\nالاتجاه: هبوط (SELL) 📉\nالاحتمال: {prob_val:.2f}%"
                        send_telegram_alert(msg)
                        st.info("📱 تم إرسال إشعار إلى تيليجرام!")
                
                st.subheader("حركة السعر الأخيرة")
                st.line_chart(data['Close'])
                
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
