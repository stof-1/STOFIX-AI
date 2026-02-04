import customtkinter as ctk
import speech_recognition as sr
import pyttsx3
import pyautogui
import subprocess
import keyboard
import threading
import time
import os
import json
from tkinter import filedialog

# === CONFIGURATION ===
FONT_FAMILY = "Arial"  
BUTTON_RADIUS = 30      
FRAME_RADIUS = 20       

# === Initialize TTS ===
engine = pyttsx3.init()
engine.setProperty('rate', 160) 
listening_active = False  # Controls Listening Animation
recognizer = sr.Recognizer()

# === Animation Variables ===
is_speaking = False     # Controls Speaking Animation
animation_step = 0

# === Data File ===
DATA_FILE = "custom_apps.json"
custom_commands = {}

# === Setup CustomTkinter ===
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("🧠 AI Assistant STOFIX")
app.geometry("550x820")
app.configure(fg_color="#66A5AD")

# === SET ICON ===
if os.path.exists("ai-assistant.ico"):
    try:
        app.iconbitmap("ai-assistant.ico")
    except Exception:
        print("Icon not found or invalid format.")

# === Global Variables ===
status_text = ctk.StringVar(value="Status: Ready")

# === UI Components ===
scroll_frame = ctk.CTkScrollableFrame(app, label_text="My Custom Apps", width=450, height=300, corner_radius=FRAME_RADIUS)
scroll_frame.pack(pady=15)

# === Speech & Animation Functions ===

def speak(text):
    """
    Speaks text. 
    FIX: Waits for previous speech to finish to prevent "run loop already started" error.
    """
    global is_speaking
    
    # Wait until current speech is finished
    while is_speaking:
        time.sleep(0.1)
    
    def run_speech():
        global is_speaking
        is_speaking = True
        try:
            engine.say(text)
            engine.runAndWait()
        except RuntimeError as e:
            print(f"Speech Error: {e}")
        finally:
            is_speaking = False

    # Start speech in thread
    threading.Thread(target=run_speech, daemon=True).start()

def wait_for_speech():
    """Keeps UI alive while speaking."""
    # FIX: Added small sleep to ensure speech thread has started
    time.sleep(0.1)
    while is_speaking:
        try:
            app.update() 
        except RuntimeError:
            break
        time.sleep(0.05)

def animate_logo():
    """
    Animates logo when SPEAKING OR LISTENING.
    """
    global is_speaking, listening_active, animation_step
    
    if is_speaking or listening_active:
        try:
            patterns = [
                "|   |   |",
                "||  |   |",
                "||  ||  |",
                "||  ||  ||",
                "||| ||| |||"
            ]
            current_pattern = patterns[animation_step % len(patterns)]
            title.configure(text=current_pattern, fg_color="#4a6fa5", text_color="white")
            
            animation_step += 1
            app.after(100, animate_logo)
        except RuntimeError:
            pass # App is closing
    else:
        try:
            title.configure(text="🧠 STOFIX AI", fg_color="#66A5AD", text_color="white")
        except RuntimeError:
            pass

def start_animation_loop():
    """FIX: Checks if app is valid before looping."""
    try:
        if is_speaking or listening_active:
            animate_logo()
        app.after(100, start_animation_loop)
    except RuntimeError:
        pass

# === Persistence Functions (Save/Load) ===

def save_apps_to_file():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(custom_commands, f)
    except Exception as e:
        print(f"Error saving: {e}")

def load_apps_from_file():
    global custom_commands
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                custom_commands = json.load(f)
                for name, path in custom_commands.items():
                    create_app_entry_ui(name, path)
        except Exception as e:
            print(f"Error loading: {e}")
            custom_commands = {}

def create_app_entry_ui(name, path):
    row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    row.pack(pady=4, fill="x", padx=5)

    def run_app():
        status_text.set(f"Status: Opening {name}...")
        if os.path.exists(path):
            os.startfile(path)
        else:
            speak("Application file not found")

    btn_run = ctk.CTkButton(row, text=f"🚀 {name}", command=run_app, 
                            fg_color="#4a6fa5", hover_color="#3a5c8a", text_color="white",
                            corner_radius=15, height=35, font=(FONT_FAMILY, 13))
    btn_run.pack(side="left", expand=True, fill="x", padx=(0, 8))

    def delete_app():
        if name in custom_commands:
            del custom_commands[name]
            save_apps_to_file()
            row.destroy()
            status_text.set(f"Status: Removed {name}")

    btn_del = ctk.CTkButton(row, text="✖", command=delete_app, 
                            fg_color="#d9534f", hover_color="#c9302c", text_color="white",
                            width=35, height=35, corner_radius=17, font=(FONT_FAMILY, 12, "bold"))
    btn_del.pack(side="right")

# === Helper Functions ===

def create_button_row(btn1_text, btn1_cmd, btn2_text, btn2_cmd):
    row = ctk.CTkFrame(app, fg_color="transparent")
    row.pack(pady=6)
    b1 = ctk.CTkButton(row, text=btn1_text, command=btn1_cmd, corner_radius=BUTTON_RADIUS,
                       width=220, height=45, font=(FONT_FAMILY, 14, "bold"))
    b2 = ctk.CTkButton(row, text=btn2_text, command=btn2_cmd, corner_radius=BUTTON_RADIUS,
                       width=220, height=45, font=(FONT_FAMILY, 14, "bold"))
    b1.pack(side="left", padx=6)
    b2.pack(side="left", padx=6)

# === Add Custom App Logic ===

def open_add_custom_window():
    popup = ctk.CTkToplevel(app)
    popup.title("Add New App")
    popup.geometry("420x320")
    popup.configure(fg_color="#66A5AD")

    def browse_file():
        file_path = filedialog.askopenfilename(
            title="Select Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            entry_path.delete(0, "end")
            entry_path.insert(0, file_path)

    def save_custom_app():
        name = entry_name.get().strip().lower()
        path = entry_path.get().strip()

        if not name or not path:
            status_text.set("Status: Fill all fields!")
            return

        if name in custom_commands:
            status_text.set("Status: App already exists!")
            return

        custom_commands[name] = path
        save_apps_to_file()
        create_app_entry_ui(name, path)

        status_text.set(f"Status: Added {name}")
        speak(f"Added {name} to the list")
        time.sleep(0.5) # Wait time
        wait_for_speech()
        popup.destroy()

    ctk.CTkLabel(popup, text="App Name (Voice Command):", font=(FONT_FAMILY, 14, "bold")).pack(pady=(20, 5))
    entry_name = ctk.CTkEntry(popup, placeholder_text="e.g. spotify", width=300, corner_radius=10)
    entry_name.pack(pady=5)

    ctk.CTkLabel(popup, text="File Path:", font=(FONT_FAMILY, 14, "bold")).pack(pady=(20, 5))
    entry_path = ctk.CTkEntry(popup, placeholder_text="C:\\Program Files\\...", width=300, corner_radius=10)
    entry_path.pack(pady=5)

    btn_browse = ctk.CTkButton(popup, text="Browse File...", command=browse_file, width=150, corner_radius=20, font=(FONT_FAMILY, 12))
    btn_browse.pack(pady=10)
    
    btn_save = ctk.CTkButton(popup, text="➕ Create Button", command=save_custom_app, 
                  fg_color="#5cb85c", hover_color="#449d44", width=200, corner_radius=25, font=(FONT_FAMILY, 14, "bold"))
    btn_save.pack(pady=10)

# === Email Workflow ===

def start_email_flow():
    global listening_active
    
    speak("Opening Gmail")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    status_text.set("Status: Waiting for Gmail to open...")
    
    os.startfile("https://mail.google.com/mail/u/0/#inbox?compose=new")

    time.sleep(4)

    speak("Who do you want to send the email to?")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    status_text.set("Status: Listening for email...")
    
    recipient_email = ""
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower()
                recipient_email += text + " "
                status_text.set(f"Status: {recipient_email}")
                if ".com" in text:
                    status_text.set("Status: Email captured.")
                    break
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"Error: {e}")

    recipient_clean = recipient_email.replace(" at ", "@").replace(" dot ", ".")
    recipient_clean = ' '.join(recipient_clean.split())

    pyautogui.write(recipient_clean)
    pyautogui.press('tab') # Changed to 1 Tab as requested

    speak("What is the subject? Say next when done.")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    status_text.set("Status: Listening for subject...")

    subject_text = ""
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower()
                if "next" in text:
                    subject_text += text.replace("next", "") + " "
                    break
                else:
                    subject_text += text + " "
                    pyautogui.write(text + " ") 
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue

    pyautogui.write(subject_text)
    speak(f"Subject is {subject_text}")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    pyautogui.press('tab') 

    speak("What is the message? Say send when done.")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    status_text.set("Status: Recording message...")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                text = recognizer.recognize_google(audio).lower()
                
                print(f"DEBUG: Heard '{text}'")
                
                if "send" in text:
                    body_text = text.replace("send", "")
                    pyautogui.write(body_text + " ")
                    
                    time.sleep(0.2) 
                    
                    speak("Sending now")
                    wait_for_speech()
                    
                    pyautogui.hotkey('ctrl', 'enter')
                    break
                else:
                    pyautogui.write(text + " ")
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                pass 

    status_text.set("Status: Ready")

# === LinkedIn Logic ===
def open_linkedin():
    os.startfile("https://www.linkedin.com")

# === Core Logic ===

def recognize_speech():
    global listening_active
    
    if listening_active: return
    listening_active = True
    speak("Listening started")
    wait_for_speech()
    time.sleep(0.5) # Extra wait
    status_text.set("Status: Listening...")

    with sr.Microphone() as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            while listening_active:
                try:
                    audio = recognizer.listen(source, timeout=1)
                    command = recognizer.recognize_google(audio).lower()
                    
                    if command in custom_commands:
                        status_text.set(f"Status: Opening {command}")
                        speak(f"Opening {command}")
                        wait_for_speech()
                        time.sleep(0.5) # Extra wait
                        subprocess.Popen(custom_commands[command], shell=True)
                        break
                    elif "notepad" in command:
                        open_notepad()
                    elif "linkedin" in command: # Changed from mouse to linkedin
                        open_linkedin()
                    elif "email" in command or "send mail" in command:
                        start_email_flow()
                        break
                    elif "hello" in command or "stofix" in command:
                        say_hello()
                    elif "stop" in command:
                        stop_listening()
                    
                    else:
                        status_text.set(f"Status: Heard '{command}'")
                        speak(f"You said {command}, but I don't know that app yet.")
                        wait_for_speech()
                        time.sleep(0.5) # Extra wait
                        break 

                except sr.WaitTimeoutError:
                    continue
                    
        except sr.UnknownValueError:
            status_text.set("Status: Didn't understand")
            speak("Sorry, I did not understand.")
            wait_for_speech()
        except sr.RequestError as e:
            status_text.set(f"Status: Network Error")
            speak("I cannot reach the speech service.")
            wait_for_speech()
        except Exception as e:
            status_text.set(f"Status: Mic Error: {e}")
            speak("I cannot access your microphone.")
            wait_for_speech()

    listening_active = False
    status_text.set("Status: Ready")

def stop_listening():
    global listening_active
    listening_active = False
    speak("Stopping")
    wait_for_speech()
    status_text.set("Status: Stopped")

def open_notepad():
    subprocess.Popen(["notepad.exe"])

def say_hello():
    speak("Hello Stof")

def set_volume(val):
    engine.setProperty('volume', val)

def exit_app():
    global listening_active
    listening_active = False
    app.destroy()

# === Main UI Layout ===

title = ctk.CTkLabel(app, text="🧠 STOFIX AI", font=(FONT_FAMILY, 28, "bold"), text_color="white")
title.pack(pady=20)

create_button_row("🎤 Speak", recognize_speech, "🛑 Stop", stop_listening)
create_button_row("📂 Notepad", open_notepad, "🔗 LinkedIn", open_linkedin)
create_button_row("🔊 Hello Stof", say_hello, "📧 Email", lambda: threading.Thread(target=start_email_flow).start())

add_custom_btn = ctk.CTkButton(app, text="➕ Add Custom App", command=open_add_custom_window, 
                               fg_color="#8e44ad", hover_color="#732d91", height=45, width=300, corner_radius=25, font=(FONT_FAMILY, 14, "bold"))
add_custom_btn.pack(pady=15)

slider_frame = ctk.CTkFrame(app, fg_color="transparent")
slider_frame.pack(pady=10)
vol_label = ctk.CTkLabel(slider_frame, text="Volume", font=(FONT_FAMILY, 12))
vol_label.pack(side="left", padx=10)
vol_slider = ctk.CTkSlider(slider_frame, from_=0, to=1, command=set_volume, width=200)
vol_slider.set(0.9)
vol_slider.pack(side="left", padx=10)

exit_btn = ctk.CTkButton(app, text="❌ Exit", command=exit_app, fg_color="#c0392b", hover_color="#a93226", width=300, height=45, corner_radius=25, font=(FONT_FAMILY, 14, "bold"))
exit_btn.pack(pady=15)

status_bar = ctk.CTkLabel(app, textvariable=status_text, font=("Consolas", 12), fg_color="white", corner_radius=15, text_color="black", padx=15, pady=5)
status_bar.pack(side="bottom", pady=20)

# === Startup ===
load_apps_from_file()
start_animation_loop()

# === Hotkeys ===
def listen_for_hotkeys():
    time.sleep(1)
    keyboard.add_hotkey("F9", recognize_speech)
    keyboard.add_hotkey("F10", stop_listening)

threading.Thread(target=listen_for_hotkeys, daemon=True).start()

app.bind("<F9>", lambda event: recognize_speech())
app.bind("<F10>", lambda event: stop_listening())

app.mainloop()