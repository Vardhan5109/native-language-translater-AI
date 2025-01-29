from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import pyttsx3
import threading
from googletrans import Translator

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"

# Initialize translator
translator = Translator()

# Supported languages and their codes
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "French": "fr",
    "Spanish":"es",
    "Italian":"it",
    "Portuguese":"pt-br",
    "Arabic": "ar",
    # Add more languages as needed
}

# Speech recognition function
def recognize_speech(language="en-US"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio, language=language)
            print(f"Recognized Text ({language}): {text}")
            return text
        except Exception as e:
            print("Speech Recognition Error:", str(e))
            return None

# Text translation function
def translate_text(text, target_language="en"):
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print("Translation Error:", str(e))
        return "Error: Could not translate text."

# Text-to-speech function with a dedicated engine per thread
def speak_text(text, language="en"):
    try:
        def tts_worker():
            # Create a new instance of the engine for this thread
            local_engine = pyttsx3.init()
            voices = local_engine.getProperty("voices")

            # Attempt to select a voice matching the target language
            selected_voice = None
            for voice in voices:
                # Match language code in the voice.languages attribute
                if language in voice.languages or language in voice.id.lower():
                    selected_voice = voice.id
                    break

            if selected_voice:
                local_engine.setProperty("voice", selected_voice)
            else:
                print(f"No voice found for language '{language}', using default.")

            local_engine.say(text)
            local_engine.runAndWait()
            local_engine.stop()  # Ensure the engine stops completely

        # Run TTS in a separate thread
        tts_thread = threading.Thread(target=tts_worker)
        tts_thread.start()
    except Exception as e:
        print("TTS Error:", str(e))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        source_language = request.form.get("source_lang")
        target_language = request.form.get("target_lang")

        if action == "speak_to_user":
            # User speaks in the source language
            user_speech = recognize_speech(language=LANGUAGES[source_language])
            if user_speech:
                translated_text = translate_text(user_speech, target_language=LANGUAGES[target_language])
                speak_text(translated_text, language=LANGUAGES[target_language])
                return jsonify({"recognized_text": user_speech, "translated_text": translated_text})

        elif action == "speak_to_user_response":
            # Other person responds in the target language
            response_speech = recognize_speech(language=LANGUAGES[target_language])
            if response_speech:
                translated_text = translate_text(response_speech, target_language=LANGUAGES[source_language])
                speak_text(translated_text, language=LANGUAGES[source_language])
                return jsonify({"recognized_text": response_speech, "translated_text": translated_text})

    return render_template("index.html", languages=LANGUAGES.keys())

if __name__ == "__main__":
    app.run(debug=True)
