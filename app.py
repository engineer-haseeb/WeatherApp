import streamlit as st
import requests
import geocoder
import pandas as pd
import folium
from streamlit_folium import folium_static
import pyttsx3
from io import StringIO

# --- CONFIG ---
API_KEY = "61a356e45c3c4a375acd2d04114070db"

# --- FUNCTIONS ---
def get_location():
    g = geocoder.ip('me')
    if g.ok:
        return g.city, g.latlng
    return None, (0, 0)

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
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
    else:
        return None

def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast_list = data['list']
        df = pd.DataFrame()
        df['datetime'] = [item['dt_txt'] for item in forecast_list]
        df['temperature'] = [item['main']['temp'] for item in forecast_list]
        df['humidity'] = [item['main']['humidity'] for item in forecast_list]
        df['wind_speed'] = [item['wind']['speed'] for item in forecast_list]
        df['condition'] = [item['weather'][0]['description'].title() for item in forecast_list]
        return df
    else:
        return None

def speak_weather(weather):
    engine = pyttsx3.init()
    text = f"Hello Mr. Hani. Today in {weather['city']}, temperature is {weather['temperature']} degrees Celsius, feels like {weather['feels_like']}. Condition: {weather['description']}. Humidity is {weather['humidity']} percent."
    
    engine.say(text)
    engine.runAndWait()

def create_weather_report(weather, forecast_df):
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
st.set_page_config(page_title="🌤 Advanced Weather App", layout="wide", initial_sidebar_state="expanded")
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🌤 Advanced Weather App</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("City Selection")
manual_city = st.sidebar.text_input("Enter city manually")
st.sidebar.markdown("💡 Leave empty to auto-detect your location.")
st.sidebar.markdown("⚡ Advanced Features: Map, Alerts, Voice, Download")

# Detect user location
if manual_city:
    city = manual_city
    weather_lat, weather_lon = 0, 0
else:
    city, coords = get_location()
    weather_lat, weather_lon = coords
    if not city:
        st.error("Location not detected. Please enter city manually.")

# Fetch current weather
if city:
    weather = get_weather(city)
    forecast_df = get_forecast(city)
    if weather:
        # --- Current Weather Card ---
        st.subheader(f"Current Weather in {weather['city']}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="🌡 Temperature (°C)", value=f"{weather['temperature']}°C", delta=f"Feels like {weather['feels_like']}°C")
        col2.metric(label="💧 Humidity (%)", value=f"{weather['humidity']}%")
        col3.metric(label="💨 Wind Speed (m/s)", value=f"{weather['wind_speed']} m/s")
        col4.metric(label="🌥 Condition", value=weather['description'])
        
        st.markdown("---")
        
        # --- Weather Alerts ---
        if weather['temperature'] > 40:
            st.warning("⚠️ Heatwave Alert! Stay hydrated.")
        if "rain" in weather['description'].lower():
            st.info("☔ Rain Alert! Carry an umbrella.")
        
        # --- 5-Day Forecast Charts ---
        if forecast_df is not None:
            st.subheader("📈 5-Day Forecast (3-hour interval)")
            st.markdown("### Temperature Trend")
            st.line_chart(forecast_df[['datetime', 'temperature']].set_index('datetime'), height=300)
            st.markdown("### Humidity Trend")
            st.bar_chart(forecast_df[['datetime', 'humidity']].set_index('datetime'), height=300)
        
        # --- Interactive Map ---
        st.subheader("📍 Location Map")
        map_center = [weather['lat'], weather['lon']]
        m = folium.Map(location=map_center, zoom_start=8)
        folium.Marker(location=map_center, popup=f"{weather['city']}").add_to(m)
        folium_static(m)
        
        # --- Voice Report Button ---
        if st.button("🔊 Speak Weather Report"):
            speak_weather(weather)
        
        # --- Download Weather Report ---
        report_file = create_weather_report(weather, forecast_df)
        st.download_button(
            label="📥 Download Weather Report",
            data=report_file.getvalue(),
            file_name=f"Weather_Report_{weather['city']}.txt",
            mime="text/plain"
        )
        
    else:
        st.error("Weather data not found. Please check city name.")
