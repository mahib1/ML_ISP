import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import os

# === CONFIGURATION ===
GEMINI_API_KEY = os.environ["API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

r = sr.Recognizer()
tts = pyttsx3.init()

def speak(text):
    print("Speaking:", text)
    tts.say(text)
    tts.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("Listening... (10s max)")
        try:
            audio = r.listen(source, phrase_time_limit=10)
            print("Processing input...")
            text = r.recognize_google(audio)
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            speak("Sorry, I could not understand that.")
        except sr.RequestError:
            print("Could not reach the recognition service.")
            speak("There was an error connecting to the speech service.")
        return None

def ask_gemini(question):
    print("Asking Gemini:", question)
    response = model.generate_content(question)
    answer = response.text.strip()
    print("Gemini says:", answer)
    return answer

# === MAIN ===
if __name__ == "__main__":
    question = listen()
    if question:
        answer = ask_gemini(question)
        speak(answer)
