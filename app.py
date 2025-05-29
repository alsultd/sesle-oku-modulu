from flask import Flask, request, render_template_string
import speech_recognition as sr
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return "Merhaba, Sesle Oku uygulamasına hoş geldiniz! Ses tanıma için <a href='/sesle-oku'>buraya tıklayın</a>."

@app.route("/sesle-oku", methods=["GET", "POST"])
def sesle_oku():
    return "Sesle oku testi, çalışıyor!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
