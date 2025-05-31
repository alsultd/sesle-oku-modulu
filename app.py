import docx
import re
import difflib
import random
import streamlit as st
import os
from deep_translator import GoogleTranslator
import pronouncing
from gtts import gTTS
import base64
from streamlit_speech_to_text import speech_to_text

# Sabitler
ERROR_THRESHOLD = 0.3
TOTAL_TOPICS = 152
DOCX_FILE_NAME = "OCR_Ana_Cikti_Guncel.docx"

# --- Yardımcı Fonksiyonlar ---

def get_text_from_docx(doc_path, topic_no):
    try:
        doc = docx.Document(doc_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        topics = []
        current_topic = ""
        current_number = None
        for p in paragraphs:
            match = re.match(r'^Konu\s*:\s*(\d+)', p)
            if match:
                if current_topic and current_number is not None:
                    topics.append({"number": current_number, "text": current_topic})
                current_number = int(match.group(1))
                current_topic = ""
            else:
                if current_number is not None:
                    current_topic += p + "\n"
        if current_topic and current_number is not None:
            topics.append({"number": current_number, "text": current_topic})
        for topic in topics:
            if topic["number"] == topic_no:
                topic["text"] = topic["text"].replace("=== KONU SONU ===", "").strip()
                return topic["text"]
        return None
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
        return None

def split_into_paragraphs(text):
    return [p.strip() for p in text.split('\n') if p.strip()]

def preprocess_text(text):
    return re.findall(r"\b\w+\b", text.lower())

def evaluate_speech(original, spoken):
    original_words = preprocess_text(original)
    spoken_words = preprocess_text(spoken)
    diff = difflib.SequenceMatcher(None, original_words, spoken_words)
    similarity = diff.ratio()
    error_rate = 1 - similarity
    extra_words = [word for word in spoken_words if word not in original_words]
    missing_words = [word for word in original_words if word not in spoken_words]
    return error_rate, extra_words, missing_words

def read_paragraph(paragraph):
    clean_text = " ".join(paragraph.splitlines()).replace('\"', '').replace("'", "").replace('{', '').replace('}', '')
    try:
        tts = gTTS(text=clean_text, lang='en', slow=False)
        audio_file = "temp_audio.mp3"
        tts.save(audio_file)
        with open(audio_file, "rb") as audio_file_obj:
            audio_base64 = base64.b64encode(audio_file_obj.read()).decode('utf-8')
        os.remove(audio_file)
        audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Tarayıcınız ses oynatmayı desteklemiyor.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Paragraf oynatılamadı: {e}")

def play_word(word):
    try:
        tts = gTTS(text=word, lang='en', slow=True)
        audio_file = "temp_word_audio.mp3"
        tts.save(audio_file)
        with open(audio_file, "rb") as audio_file_obj:
            audio_base64 = base64.b64encode(audio_file_obj.read()).decode('utf-8')
        os.remove(audio_file)
        audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Tarayıcınız ses oynatmayı desteklemiyor.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Telaffuz oynatılamadı: {e}")

def translate_word(word):
    try:
        return GoogleTranslator(source='en', target='tr').translate(word)
    except Exception:
        return "Çeviri yapılamadı"

def translate_paragraph(paragraph):
    try:
        return GoogleTranslator(source='en', target='tr').translate(paragraph)
    except Exception as e:
        return f"Paragraf çevirisi yapılamadı: {e}"

def report_errors(error_rate, extra_words, missing_words):
    error_rate_percent = round(error_rate * 100)
    st.write(f"**Hata Oranı:** {error_rate_percent}%")
    if extra_words:
        st.write("**Fazladan söylenen kelimeler:**")
        st.write(", ".join(extra_words))
    else:
        st.write("**Harika!** Fazladan kelime yok.")
    if missing_words:
        st.write("**Eksik kelimeler:**")
        missing_data = []
        for word in missing_words:
            phonetics = pronouncing.phones_for_word(word)
            phonetic = phonetics[0] if phonetics else "Telaffuz bulunamadı"
            translation = translate_word(word)
            missing_data.append({"Kelime": word, "Telaffuz": phonetic, "Türkçe": translation})
        st.table(missing_data)

def main():
    st.title("Sesle Okuma Çalışması")
    st.write(f"**Toplam Konu Sayısı:** {TOTAL_TOPICS}")

    if "paragraphs" not in st.session_state:
        st.session_state["paragraphs"] = []
        st.session_state["current_index"] = 0
        st.session_state["selected_word"] = None
        st.session_state["translation"] = ""
        st.session_state["doc_text"] = {}
        st.session_state["translated_paragraph"] = ""
        st.session_state["spoken_text"] = ""

    current_script_dir = os.path.dirname(__file__)
    doc_path = os.path.join(current_script_dir, DOCX_FILE_NAME)

    if not os.path.exists(doc_path):
        st.error(f"Hata: '{DOCX_FILE_NAME}' dosyası bulunamadı.")
        return

    topic_no = st.number_input("Konu No giriniz:", min_value=1, max_value=TOTAL_TOPICS, step=1,
                               value=random.randint(1, TOTAL_TOPICS))

    if st.button("Metni Yükle"):
        cache_key = f"{DOCX_FILE_NAME}_{topic_no}"
        if cache_key not in st.session_state["doc_text"]:
            text = get_text_from_docx(doc_path, topic_no)
            if text:
                st.session_state["doc_text"][cache_key] = text
                st.session_state["paragraphs"] = split_into_paragraphs(text)
                st.session_state["current_index"] = 0
            else:
                st.error("Konu bulunamadı veya dosya okunamadı.")
        else:
            st.session_state["paragraphs"] = split_into_paragraphs(st.session_state["doc_text"][cache_key])
            st.session_state["current_index"] = 0

    if st.session_state["paragraphs"]:
        paragraphs = st.session_state["paragraphs"]
        current_index = st.session_state["current_index"]

        st.subheader(f"Paragraf {current_index + 1}/{len(paragraphs)}")
        st.write(paragraphs[current_index])

        if st.button("Paragrafı Çevir"):
            st.session_state["translated_paragraph"] = translate_paragraph(paragraphs[current_index])

        if st.session_state["translated_paragraph"]:
            st.write("**Çevrilmiş Paragraf (Türkçe):**")
            st.info(st.session_state["translated_paragraph"])

        st.write("**Kelime çevirisi için kelimelere tıklayın:**")
        cols = st.columns(5)
        for i, word in enumerate(paragraphs[current_index].split()):
            with cols[i % 5]:
                if st.button(word, key=f"word_{i}_{current_index}"):
                    st.session_state["selected_word"] = word
                    st.session_state["translation"] = translate_word(word)
                    play_word(word)

        if st.session_state["selected_word"]:
            st.info(f"'{st.session_state['selected_word']}' çevirisi: {st.session_state['translation']}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Paragrafı Oku"):
                read_paragraph(paragraphs[current_index])

        st.markdown("### 🎤 Şimdi bu paragrafı sesli okuyun")
        spoken_text = speech_to_text(language="en-US", use_container_width=True)

        if spoken_text:
            st.session_state["spoken_text"] = spoken_text
            st.success("🔍 Konuşmanız metne dönüştürüldü!")
            st.write(f"🗣️ **Siz söylediniz:** {spoken_text}")

            if st.button("Analizi Yap"):
                error_rate, extra_words, missing_words = evaluate_speech(paragraphs[current_index], spoken_text)
                if error_rate < ERROR_THRESHOLD:
                    st.balloons()
                    st.success("Harika! Okumanız oldukça iyi.")
                else:
                    st.warning("Bazı hatalar var. Aşağıdaki raporu inceleyin.")
                report_errors(error_rate, extra_words, missing_words)
                st.write("**Karşılaştırma:**")
                st.markdown(f"**Orijinal Paragraf:** `{paragraphs[current_index]}`")
                st.markdown(f"**Sizin Okumanız:** `{spoken_text}`")

        with col3:
            if st.button("Önceki"):
                if current_index > 0:
                    st.session_state["current_index"] -= 1
                    st.session_state["translated_paragraph"] = ""
                    st.session_state["spoken_text"] = ""
                    st.session_state["selected_word"] = None
                    st.session_state["translation"] = ""
                    st.rerun()
                else:
                    st.warning("Bu ilk paragraf.")
        with col4:
            if st.button("Sonraki"):
                if current_index < len(paragraphs) - 1:
                    st.session_state["current_index"] += 1
                    st.session_state["translated_paragraph"] = ""
                    st.session_state["spoken_text"] = ""
                    st.session_state["selected_word"] = None
                    st.session_state["translation"] = ""
                    st.rerun()
                else:
                    st.warning("Bu son paragraf.")

if __name__ == "__main__":
    main()
