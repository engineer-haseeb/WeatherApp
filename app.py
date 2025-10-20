import streamlit as st
import requests
from gtts import gTTS
import os

# Weather API key
API_KEY = "61a356e45c3c4a375acd2d04114070db"

# Function to get weather data
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()

# Function to convert text to speech using gTTS
def speak_weather(text):
    tts = gTTS(text=text, lang="en")
    filename = "weather.mp3"
    tts.save(filename)
    st.audio(filename, format="audio/mp3")

# Streamlit UI
st.set_page_config(page_title="Weather App", page_icon="⛅", layout="centered")

st.title("🌦️ Weather Forecast App")
st.write("Enter a city to check the weather!")

city = st.text_input("City name:")

if st.button("Get Weather"):
    if city:
        data = get_weather(city)
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            weather_report = f"Hello Mr. Hani! The weather in {city} is {desc}. Temperature is {temp}°C, humidity is {humidity} percent, and wind speed is {wind} meters per second."

            st.success(weather_report)

            # Play sound
            speak_weather(weather_report)

        else:
            st.error("City not found. Please try again.")
    else:
        st.warning("Please enter a city name.")
