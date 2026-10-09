import os
import sys
import time
from pathlib import Path
import speech_recognition as sr
from gtts import gTTS

# Setup Hailo environment paths
repo_root = Path("/home/atei/ProjectSM/hailo-apps")
sys.path.insert(0, str(repo_root))

try:
    from hailo_platform import VDevice
    from hailo_platform.genai import LLM
    from hailo_apps.python.core.common.defines import SHARED_VDEVICE_GROUP_ID
    HAILO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: hailo_platform package not found ({e}). NPU won't work.")
    HAILO_AVAILABLE = False

MODEL_PATH = "/home/atei/ProjectSM/Llama3.2-1B-Instruct.hef"

class Assistant:
    def __init__(self, model_path):
        print(f"[{time.strftime('%H:%M:%S')}] Inițializare asistent...")
        self.recognizer = sr.Recognizer()
        
        # Căutăm microfonul USB
        self.mic_index = None
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if "USB" in name:
                self.mic_index = index
                print(f"[{time.strftime('%H:%M:%S')}] Microfon USB detectat la indexul {index}: {name}")
                break
        if self.mic_index is None:
            print(f"[{time.strftime('%H:%M:%S')}] Nu s-a detectat un microfon USB, se va folosi cel default.")
        
        if HAILO_AVAILABLE and os.path.exists(model_path):
            try:
                print(f"[{time.strftime('%H:%M:%S')}] Se încarcă modelul pe NPU: {model_path}")
                params = VDevice.create_params()
                params.group_id = SHARED_VDEVICE_GROUP_ID
                self.vdevice = VDevice(params)
                self.llm = LLM(self.vdevice, model_path)
                print(f"[{time.strftime('%H:%M:%S')}] Model încărcat cu succes!")
            except Exception as e:
                print(f"Eroare la încărcarea modelului pe NPU: {e}")
                self.llm = None
        else:
            print("Modelul nu a fost găsit sau Hailo API nu este disponibil.")
            self.llm = None

    def listen(self):
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                print(f"\n[{time.strftime('%H:%M:%S')}] Ajustare pentru zgomot de fond...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"[{time.strftime('%H:%M:%S')}] 🎤 Vorbește acum! (sau apasă Ctrl+C pentru a ieși)")
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    print(f"[{time.strftime('%H:%M:%S')}] Procesare audio...")
                    text = self.recognizer.recognize_google(audio, language="ro-RO")
                    print(f"👤 Utilizator (Voce): {text}")
                    return text
                except sr.WaitTimeoutError:
                    print("Nu s-a auzit nimic.")
                    return None
                except sr.UnknownValueError:
                    print("Nu am înțeles ce ai spus.")
                    return None
                except sr.RequestError as e:
                    print(f"Eroare la serviciul de recunoaștere a vocii: {e}")
                    return None
        except Exception as e:
            print(f"Eroare neașteptată la inițializarea microfonului: {e}")
            raise e

    def get_input(self):
        try:
            print("\n" + "="*50)
            text = self.listen()
            if not text:
                print("Fallback la tastatură. Scrie ceva (sau 'exit'):")
                text = input("👤 Utilizator (Tastatură): ")
                if text.lower().strip() in ['exit', 'quit']:
                    return None
            return text
        except KeyboardInterrupt:
            return None
        except Exception as e:
            print(f"Fallback la tastatură (Eroare microfon). Scrie ceva (sau 'exit'):")
            try:
                text = input("👤 Utilizator (Tastatură): ")
                if text.lower().strip() in ['exit', 'quit']:
                    return None
                return text
            except (KeyboardInterrupt, EOFError):
                return None

    def generate_response(self, prompt):
        if not self.llm:
            return "Îmi pare rău, creierul meu NPU nu este disponibil momentan."
        
        system_prompt = "Ești un asistent virtual inteligent integrat într-o oglindă inteligentă. Răspunzi scurt, la obiect și prietenos, exclusiv în limba română."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Generare răspuns (NPU)...")
            start_time = time.time()
            response = self.llm.generate_all(prompt=messages, temperature=0.7, max_generated_tokens=200)
            end_time = time.time()
            duration = end_time - start_time
            print(f"[{time.strftime('%H:%M:%S')}] Generare finalizată în {duration:.2f} secunde.")
            
            clean_response = str(response).split(". [{'type'")[0].replace("<|im_end|>", "").strip()
            return clean_response
        except Exception as e:
            print(f"Eroare la generarea răspunsului: {e}")
            return "Îmi pare rău, am întâmpinat o eroare la generarea răspunsului."

    def speak(self, text):
        if not text:
            return
        print(f"🤖 Asistent: {text}")
        try:
            tts = gTTS(text=text, lang='ro')
            tts.save("response.mp3")
            # Splitter-ul HDMI necesita 48000Hz Stereo WAV, asa ca facem conversie rapida cu ffmpeg si play cu aplay
            os.system("ffmpeg -y -i response.mp3 -ar 48000 -ac 2 response.wav 2>/dev/null && aplay -q -D plughw:0,0 response.wav")
        except Exception as e:
            print(f"Eroare la redarea audio (TTS): {e}")

    def run(self):
        print("\n--- Sistemul Asistent Oglindă Inteligentă a Pornit ---")
        try:
            while True:
                user_text = self.get_input()
                if not user_text:
                    if user_text is None:
                        break # exit requested or ctrl+c
                    continue # empty input, continue
                
                response_text = self.generate_response(user_text)
                self.speak(response_text)
        except KeyboardInterrupt:
            pass
        finally:
            print("\nÎnchidere sistem...")
            if self.llm:
                try:
                    self.llm.clear_context()
                    self.vdevice.release()
                except:
                    pass

if __name__ == "__main__":
    assistant = Assistant(MODEL_PATH)
    assistant.run()
