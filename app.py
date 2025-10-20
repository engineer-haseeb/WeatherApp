# --- IMPORTS ---
import streamlit as st
import requests
import geocoder
import pandas as pd
import folium
from streamlit_folium import folium_static
from io import StringIO
import pyttsx3
from gtts import gTTS
import os
import base64

# --- CONFIG ---
API_KEY = "61a356e45c3c4a375acd2d04114070db"

# --- FUNCTIONS ---
def get_location():
    """Detect user location using IP"""
    g = geocoder.ip('me')
    if g.ok:
        return g.city, g.latlng
    return None, (0, 0)

def get_weather(city):
    """Fetch current weather data"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            weather = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"].title(),
                "lat": data["coord"]["lat"],
                "lon": data["coord"]["lon"]
            }
            return weather
    except Exception as e:
        st.error(f"Error fetching weather: {e}")
    return None

def get_forecast(city):
    """Fetch 5-day forecast"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame({
                'datetime': [item['dt_txt'] for item in data['list']],
                'temperature': [item['main']['temp'] for item in data['list']],
                'humidity': [item['main']['humidity'] for item in data['list']],
                'wind_speed': [item['wind']['speed'] for item in data['list']],
                'condition': [item['weather'][0]['description'].title() for item in data['list']]
            })
            return df
    except Exception as e:
        st.error(f"Error fetching forecast: {e}")
    return None

def speak_weather(weather, use_offline=True):
    """Speak weather report"""
    text = f"Hello Mr.Hani! Today in {weather['city']}, temperature is {weather['temperature']}°C, feels like {weather['feels_like']}°C. Condition: {weather['description']}. Humidity is {weather['humidity']}%."
    try:
        if use_offline:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        else:
            tts = gTTS(text=text, lang='en')
            filename = "weather.mp3"
            tts.save(filename)
            st.audio(filename, format="audio/mp3")
            os.remove(filename)
    except Exception as e:
        st.warning(f"Text-to-speech error: {e}")

def create_weather_report(weather, forecast_df):
    """Generate a downloadable report"""
    output = StringIO()
    output.write(f"Weather Report for {weather['city']}\n")
    output.write(f"Temperature: {weather['temperature']}°C (Feels like {weather['feels_like']}°C)\n")
    output.write(f"Humidity: {weather['humidity']}%\n")
    output.write(f"Wind Speed: {weather['wind_speed']} m/s\n")
    output.write(f"Condition: {weather['description']}\n\n")
    output.write("Forecast:\n")
    output.write(forecast_df.to_csv(index=False))
    return output

# --- STREAMLIT UI ---
st.set_page_config(page_title="🌤 Weather Forecast by Hani-汉哈尼", layout="wide")

# --- LOGO AND TITLE ---
logo_path = "logo.png"

# Convert logo to base64 for HTML embedding
with open(logo_path, "rb") as image_file:
    encoded_logo = base64.b64encode(image_file.read()).decode()

st.markdown(
    f"""
    <div style="display:flex; align-items:center;">
        <img src="data:image/png;base64,{encoded_logo}" 
             style="width:35mm; height:45mm; margin-right:15px;">
        <h1 style='color: #1E90FF; margin:0;'>🌤 Weather Forecast by Hani-汉哈尼</h1>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR ---
st.sidebar.header("City Selection-城市选择")
manual_city = st.sidebar.text_input("Enter City Name-输入城市名称")
use_tts = st.sidebar.radio("Select anyone for better voice results(选择任何人以获得更好的语音效果)", ["(pyttsx3)", "(gTTS)"])
st.sidebar.markdown("Leave empty to auto-detect your location (如果留空则自动检测您的当前位置).")
st.sidebar.markdown("We have Features: Map, Alerts, Voice, Download (我们有以下功能：地图、警报、语音、下载)")

# --- DETERMINE CITY ---
if manual_city:
    city = manual_city
    coords = (0,0)
else:
    city, coords = get_location()
    if not city:
        st.warning("Location not detected. Please enter city manually.")

# --- FETCH DATA ---
if city:
    weather = get_weather(city)
    forecast_df = get_forecast(city)
    if weather:
        # Current Weather
        st.subheader(f"当前天气-Current Weather in {weather['city']}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🌡 Temperature (温度) (°C)", f"{weather['temperature']}°C", f"Feels like {weather['feels_like']}°C")
        col2.metric("💧 Humidity (湿度) (%)", f"{weather['humidity']}%")
        col3.metric("💨 Wind Speed (风速) (m/s)", f"{weather['wind_speed']} m/s")
        col4.metric("🌥 Condition", weather['description'])
        st.markdown("---")

        # Alerts
        if weather['temperature'] > 35:
            st.warning("⚠️ Heatwave Alert! Stay hydrated (热浪警报！注意补水).")
        if "rain" in weather['description'].lower():
            st.info("☔ Rain Alert! Carry an umbrella (下雨警报！带伞).")

        # Forecast Charts
        if forecast_df is not None:
            st.subheader("📈 5-Day Forecast (五天预测)")
            st.line_chart(forecast_df[['datetime','temperature']].set_index('datetime'))
            st.bar_chart(forecast_df[['datetime','humidity']].set_index('datetime'))

        # Map
        st.subheader("📍 Location Map")
        map_center = [weather['lat'], weather['lon']]
        m = folium.Map(location=map_center, zoom_start=8)
        folium.Marker(location=map_center, popup=f"{weather['city']}").add_to(m)
        folium_static(m)

        # Voice
        if st.button("🔊 Click to Speak-点击发言"):
            speak_weather(weather, use_offline=(use_tts=="(pyttsx3)"))

        # Download report
        report_file = create_weather_report(weather, forecast_df)
        st.download_button(
            "📥 Download Weather Report-下载天气预报",
            data=report_file.getvalue(),
            file_name=f"Weather_Report_{weather['city']}.txt",
            mime="text/plain"
        )
    else:
        st.error("Weather data not found. Please check city name.")
