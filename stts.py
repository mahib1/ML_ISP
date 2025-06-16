from flask import Flask, request, send_file
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import tempfile
from gtts import gTTS
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize recognizer
recognizer = sr.Recognizer()

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction="Do not use any Markdown or special formatting characters like *, #, -, etc. in your responses. Respond in plain English text only."
)

def process_audio_file(file):
    print("Request files:", request.files)
    print("Request form:", request.form)
    
    if 'file' not in request.files:
        print("No file in request.files")
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    print("Received file:", file.filename)
    
    if file.filename == '':
        print("Empty filename")
        return {'error': 'No file selected'}, 400
    
    if not file.filename.endswith('.wav'):
        print("Invalid file type:", file.filename)
        return {'error': 'Only WAV files are supported'}, 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print("Saving file to:", filepath)
        file.save(filepath)
        
        # Convert speech to text
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print("Recognized text:", text)
        
        # Get response from Gemini
        response = model.generate_content(text)
        gemini_response = response.text
        print("Gemini response:", gemini_response)
        
        # TTS using gTTS
        temp_dir = tempfile.gettempdir()
        mp3_path = os.path.join(temp_dir, 'response.mp3')
        wav_path = os.path.join(temp_dir, 'response.wav')

        print("Saving TTS audio to:", mp3_path)
        tts = gTTS(text=gemini_response, lang='en')
        tts.save(mp3_path)

        # Convert to WAV using pydub
        sound = AudioSegment.from_mp3(mp3_path)
        sound.export(wav_path, format='wav')
        print("WAV file created:", wav_path)

        return send_file(
            wav_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='response.wav'
        )

    except Exception as e:
        print("Error occurred:", str(e))
        return {'error': str(e)}, 500

@app.route('/process-audio', methods=['POST'])
def process_audio():
    return process_audio_file(request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
