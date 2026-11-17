import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# إعداد عنوان الصفحة والأيقونة
st.set_page_config(page_title="تطبيق التوقعات الذكي", page_icon="📈", layout="centered")

st.title("📈 تطبيق التوقعات الذكي")
st.markdown("هذا التطبيق يستخدم الذكاء الاصطناعي (Random Forest) لتحليل الأسواق الحقيقية وإعطاء احتمالية للاتجاه القادم.")
st.warning("⚠️ تنبيه: هذا التطبيق تعليمي. الأسواق المالية خطرة، ولا يوجد توقع بنسبة 100%.")

# القائمة الجانبية للتحكم
st.sidebar.header("إعدادات التطبيق")
ticker = st.sidebar.text_input("رمز السهم أو العملة (مثال: BTC-USD, AAPL, EURUSD=X)", "BTC-USD")
period = st.sidebar.selectbox("الفترة الزمنية للبيانات", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
interval = st.sidebar.selectbox("الإطار الزمني للشموع", ["1h", "1d", "1wk"], index=0)

if st.button("🚀 تحليل وإعطاء توقع الآن"):
    with st.spinner("جاري جلب البيانات وتدريب الذكاء الاصطناعي..."):
        try:
            # 1. جلب البيانات
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if data.empty:
                st.error("لم يتم العثور على بيانات لهذا الرمز. تأكد من الرمز وحاول مرة أخرى.")
            else:
                # 2. حساب المؤشرات
                data['MA_10'] = data['Close'].rolling(window=10).mean()
                data['MA_50'] = data['Close'].rolling(window=50).mean()
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                # 3. تحديد الهدف
                data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
                data = data.dropna()
                
                # 4. التدريب
                features = ['MA_10', 'MA_50', 'RSI']
                X = data[features]
                y = data['Target']
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X, y) # التدريب على كل البيانات المتاحة لآخر توقع
                
                # 5. التوقع
                latest_data = X.tail(1)
                prediction = model.predict(latest_data)
                probability = model.predict_proba(latest_data)
                
                # 6. عرض النتائج
                st.subheader("نتيجة التحليل:")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="الأصل المالي", value=ticker)
                
                if prediction[0] == 1:
                    st.success(f"**الاتجاه المتوقع: صعود (BUY) 📈**")
                    st.write(f"نسبة الاحتمال: **{probability[0][1] * 100:.2f}%**")
                else:
                    st.error(f"**الاتجاه المتوقع: هبوط (SELL) 📉**")
                    st.write(f"نسبة الاحتمال: **{probability[0][0] * 100:.2f}%**")
                
                # رسم الشارت
                st.subheader("حركة السعر الأخيرة")
                st.line_chart(data['Close'])
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحليل: {e}")
