from flask import Flask, request, send_file
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import tempfile
from gtts import gTTS
from pydub import AudioSegment
from dotenv import load_dotenv
import traceback

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

recognizer = sr.Recognizer()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@app.route('/process-audio', methods=['POST'])
def process_audio():
    try:
        print("Request files:", request.files)
        print("Request form:", request.form)

        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400

        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400

        if not file.filename.endswith('.wav'):
            return {'error': 'Only WAV files are supported'}, 400

        lang = request.form.get("lang", "hi-IN")
        print("Detected language:", lang)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print("Saving file to:", filepath)
        file.save(filepath)

        if os.path.getsize(filepath) < 100:
            raise Exception("Uploaded WAV is too small or empty.")

        # Speech to text
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=lang)
            print("Recognized text:", text)

        # Gemini response
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction="Respond in Hindi using plain text. Avoid Markdown or symbols."
        )
        response = model.generate_content(text)
        reply_text = response.text
        print("Gemini reply:", reply_text)

        # TTS
        temp_dir = tempfile.gettempdir()
        mp3_path = os.path.join(temp_dir, 'response.mp3')
        wav_path = os.path.join(temp_dir, 'response.wav')

        tts = gTTS(text=reply_text, lang='hi')
        tts.save(mp3_path)

        sound = AudioSegment.from_mp3(mp3_path)
        sound.export(wav_path, format='wav')
        print("Final WAV file:", wav_path)

        return send_file(
            wav_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='response.wav'
        )

    except Exception as e:
        traceback.print_exc()
        print("Render Error:", repr(e))
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
