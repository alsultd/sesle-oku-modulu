from flask import Flask, request, render_template_string
import speech_recognition as sr
import io
import base64

app = Flask(__name__)

@app.route("/sesle-oku", methods=["GET", "POST"])
@app.route('/')
def index():
    return "Merhaba, Sesle Oku uygulamasına hoş geldiniz!"
def sesle_oku():
    # Ana programdan gelen paragrafı al
    paragraph = request.args.get("paragraph", "This is a test paragraph. Please read it aloud.")
    return_url = request.args.get("return_url", "/")  # Ana programa geri dönüş URL'si

    if request.method == "POST":
        audio_data = request.form.get("audio_data")
        if audio_data:
            # Ses dosyasını işle
            audio_bytes = base64.b64decode(audio_data)
            audio_file = io.BytesIO(audio_bytes)

            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio, language="en-US")
                    # Tanınan metni ana programa geri gönder
                    return_url_with_text = f"{return_url}?spoken_text={text.replace(' ', '%20')}"
                    return f"""
                        <script>
                            window.location.href = "{return_url_with_text}";
                        </script>
                    """
                except sr.UnknownValueError:
                    return "Ses anlaşılamadı."
                except sr.RequestError as e:
                    return f"Hata: {e}"

    # GET isteği: Ses kaydı ekranını göster
    return render_template_string("""
        <h1>Sesle Oku</h1>
        <p><b>Paragraf:</b> {{ paragraph }}</p>
        <script>
            setTimeout(function() {{
                document.getElementById("konus").style.display = "block";
                document.getElementById("buttons").style.display = "block";
            }}, 3000);
        </script>
        <div id="konus" style="display:none;">
            <p>🎙️ <b>Konuş</b></p>
        </div>
        <div id="buttons" style="display:none;">
            <button onclick="startRecording()">Kaydı Başlat</button>
            <button onclick="stopRecording()" disabled id="stopButton">Kaydı Durdur</button>
        </div>
        <audio id="audioPlayback" controls style="display:none;"></audio>
        <script>
            let mediaRecorder;
            let audioChunks = [];
            
            async function startRecording() {{
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    audioChunks = [];
                    
                    mediaRecorder.addEventListener("dataavailable", event => {{
                        audioChunks.push(event.data);
                    }});
                    
                    mediaRecorder.addEventListener("stop", () => {{
                        const audioBlob = new Blob(audioChunks, {{ type: "audio/wav" }});
                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = () => {{
                            const base64data = reader.result.split(',')[1];
                            const form = document.createElement("form");
                            form.method = "POST";
                            form.action = "/sesle-oku?paragraph={{ paragraph }}&return_url={{ return_url }}";
                            const input = document.createElement("input");
                            input.type = "hidden";
                            input.name = "audio_data";
                            input.value = base64data;
                            form.appendChild(input);
                            document.body.appendChild(form);
                            form.submit();
                        }};
                    }});
                    
                    document.getElementById("stopButton").disabled = false;
                }} catch (err) {{
                    alert("Mikrofon erişimi engellendi: " + err);
                }}
            }}
            
            function stopRecording() {{
                mediaRecorder.stop();
                document.getElementById("stopButton").disabled = true;
            }}
        </script>
    """, paragraph=paragraph, return_url=return_url)

if __name__ == "__main__":
    app.run(debug=True)
