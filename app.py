from flask import Flask, request, render_template_string, redirect
import speech_recognition as sr
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return "Merhaba, Sesle Oku uygulamasına hoş geldiniz! Ses tanıma için <a href='/sesle-oku'>Sor</a>"

@app.route("/sesle-oku", methods=["GET", "POST"])
def sesle_oku():
    try:
        paragraph = request.args.get("paragraph", "This is a test paragraph. Please read it aloud.")
        return_url = request.args.get("return_url", "/")

        if request.method == "POST":
            audio_data = request.form.get("audio_data")
            if audio_data:
                audio_bytes = base64.b64decode(audio_data)
                audio_file = io.BytesIO(audio_bytes)

                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio, language="en-US")
                        return_url_with_text = f"{return_url}?spoken_text={text.replace(' ', '%20')}"
                        return redirect(return_url_with_text)  # JavaScript yerine redirect
                    except sr.UnknownValueError:
                        return "Ses anlaşılamadı."
                    except sr.RequestError as e:
                        return f"Hata: {e}"

        return render_template_string("""
            <h1>Sesle Oku</h1>
            <p><b>Paragraf:</b> {{ paragraph }}</p>
            {% raw %}
            <script>
                setTimeout(function() {
                    document.getElementById("konus").style.display = "block";
                    document.getElementById("buttons").style.display = "block";
                }, 3000);
            </script>
            <div id="konus" style="display:none;">
                <p><b>Konuş</b></p>
            </div>
            <div id="buttons" style="display:none;">
                <button onclick="startRecording()">Kaydı Başlat</button>
                <button onclick="stopRecording()" disabled id="stopButton">Kaydet</button>
            </div>
            <audio id="audioPlayback" controls style="display:none;"></audio>
            <script>
                let mediaRecorder;
                let audioChunks = [];
                
                async function startRecording() {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();
                        audioChunks = [];
                        mediaRecorder.addEventListener("dataavailable", event => {{
                            audioChunks.push(event.data);
                        });
                        mediaRecorder.addEventListener("stop", () => {
                            const audioBlob = new Blob(audioChunks, { type: "audio/wav" }});
                            const reader = new FileReader();
                            reader.readAsDataURL(audioBlob);
                            reader.onloadend = () => {
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
                            };
                        });
                        document.getElementById("stopButton").disabled = false;
                    } catch (err) {
                        alert("Hata oluştu: " + err);
                    }
                }
                function stopRecording() {
                    mediaRecorder.stop();
                    document.getElementById("stopButton").disabled = true;
                }
            </script>
            {% endraw %}		
        """, paragraph=paragraph, return_url=return_url)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)