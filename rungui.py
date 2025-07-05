import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from lib.core import making_video
from lib.shortcore import final_video
from lib.video_texts import read_config_file
from lib.config_utils import update_config_file
from lib.async_core import make_video_async, make_short_video_async, cleanup

class AsyncRunner:
    """Helper class to run async functions from tkinter"""
    
    @staticmethod
    def run_async_in_thread(async_func, *args, **kwargs):
        """Run an async function in a separate thread"""
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                loop.close()
                
        # Start in a thread
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
        return thread

def save_config():
    # Get the current tab
    current_tab = notebook.index(notebook.select())
    
    try:
        # Create a progress window
        progress_window = tk.Toplevel(root)
        progress_window.title("UnQTube - Processing")
        progress_window.geometry("300x150")
        
        # Add a progress message
        progress_label = tk.Label(progress_window, text="Processing your video...", font=("Arial", 12))
        progress_label.pack(pady=20)
        
        # Add a progress bar
        progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()
        
        # Hide main window during processing
        root.withdraw()
        
        # Handle long video tab
        if current_tab == 0:
            # Save config values
            update_config_file('config.txt', 'general_topic', general_topic_entry.get())
            update_config_file('config.txt', 'time', time_entry.get())
            update_config_file('config.txt', 'intro_video', intro_video_var.get())
            update_config_file('config.txt', 'pexels_api', pexels_entry.get())
            update_config_file('config.txt', 'language', language_combobox.get())
            update_config_file('config.txt', 'multi_speaker', multi_speaker_var.get())
            update_config_file('config.txt', 'use_gemini', use_gemini_var.get())
            update_config_file('config.txt', 'text_model', text_model_combobox.get())
            update_config_file('config.txt', 'tts_model', tts_model_combobox.get())
            update_config_file('config.txt', 'tts_voice', tts_voice_combobox.get())
            update_config_file('config.txt', 'use_claude', use_claude_var.get())
            update_config_file('config.txt', 'claude_api', claude_api_entry.get())
            update_config_file('config.txt', 'claude_model', claude_model_combobox.get())
            
            # Check if we should use the async version
            if use_async_var.get() == "yes":
                # Show info and run async version
                progress_label.config(text="Using high-performance processing...\nThis may take a few minutes.")
                AsyncRunner.run_async_in_thread(make_video_async, topic_entry.get(), general_topic_entry.get())
            else:
                # Show info and run legacy version
                progress_label.config(text="Using standard processing...\nThis may take a few minutes.")
                # Use a thread for the synchronous function to avoid blocking the GUI
                threading.Thread(target=making_video, args=(topic_entry.get(),), daemon=True).start()
                
        # Handle short video tab
        elif current_tab == 1:
            # Save config values
            update_config_file('config.txt', 'multi_speaker', multi_speaker_var2.get())
            update_config_file('config.txt', 'pexels_api', pexels_entry2.get())
            update_config_file('config.txt', 'language', language_combobox2.get())
            update_config_file('config.txt', 'use_gemini', use_gemini_var2.get())
            update_config_file('config.txt', 'text_model', text_model_combobox2.get())
            update_config_file('config.txt', 'tts_model', tts_model_combobox2.get())
            update_config_file('config.txt', 'tts_voice', tts_voice_combobox2.get())
            update_config_file('config.txt', 'use_claude', use_claude_var2.get())
            update_config_file('config.txt', 'claude_api', claude_api_entry2.get())
            update_config_file('config.txt', 'claude_model', claude_model_combobox2.get())
            
            # Check if we should use the async version
            if use_async_var2.get() == "yes":
                # Show info and run async version
                progress_label.config(text="Using high-performance processing...\nThis may take a few minutes.")
                AsyncRunner.run_async_in_thread(make_short_video_async, topic_entry2.get(), int(time_entry2.get()))
            else:
                # Show info and run legacy version
                progress_label.config(text="Using standard processing...\nThis may take a few minutes.")
                # Use a thread for the synchronous function to avoid blocking the GUI
                threading.Thread(target=final_video, args=(topic_entry2.get(), time_entry2.get(), 
                                                          language_combobox2.get(), multi_speaker_var2.get()), 
                                 daemon=True).start()
                
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        # Clean up temp files if error occurs
        cleanup()
        # Show main window again
        root.deiconify()

# Create the root window
root = tk.Tk()
root.title("UnQTube")
root.geometry("600x850")  # Increased height to accommodate new options

# Create notebook for tabs
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Create frames for tabs
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)

notebook.add(frame1, text='Long Video')
notebook.add(frame2, text='Short Video')

# Helper function for creating labeled fields
def add_label_with_description(frame, row, text, description):
    ttk.Label(frame, text=f"{text}: {description}", wraplength=400, justify='left').grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky='w')

# Define language list with Indian languages prominently included
LANGUAGES = [
    # Indian languages first
    "english", "hindi", "bengali", "telugu", "marathi", 
    "tamil", "urdu", "gujarati", "kannada", "malayalam", 
    "punjabi", "assamese", "odia",
    # Other languages
    "persian", "arabic", "vietnamese", "zulu", "afrikaans", 
    "amharic", "azerbaijani", "bulgarian", "bosnian", "catalan", 
    "czech", "welsh", "danish", "german", "greek", "spanish", 
    "estonian", "filipino", "finnish", "french", "irish", 
    "galician", "hebrew", "croatian", "hungarian", "indonesian", 
    "icelandic", "italian", "japanese", "javanese", "georgian", 
    "kazakh", "khmer", "korean", "lao", "lithuanian", "latvian", 
    "macedonian", "mongolian", "malay", "maltese", "burmese", 
    "norwegian", "nepali", "dutch", "polish", "pashto", 
    "portuguese", "romanian", "russian", "sinhala", "slovak", 
    "slovenian", "somali", "albanian", "serbian", "sundanese", 
    "swedish", "swahili", "thai", "turkish", "ukrainian", "uzbek"
]

# Define Gemini text generation models
TEXT_MODELS = [
    "gemini-1.5-flash-latest", 
    "gemini-1.5-pro-latest"
]

# Define Gemini TTS models
TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts"
]

# Define Gemini TTS voices
TTS_VOICES = [
    "Kore", "Puck", "Charon", "Leda", "Orus", 
    "Aoede", "Callirrhoe", "Iapetus", "Umbriel", 
    "Algieba", "Despina", "Erinome", "Algenib", 
    "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", 
    "Schedar", "Gacrux", "Pulcherrima", "Achird", 
    "Zubenelgenubi", "Vindemiatrix", "Sadachbia", 
    "Sadaltager", "Sulafat", "Zephyr", "Fenrir", 
    "Autonoe", "Enceladus"
]

# Define Claude models
CLAUDE_MODELS = [
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229"
]

# ----- Frame 1 (Long Video) Widgets -----
add_label_with_description(frame1, 0, "Topic", "Enter video topic. Example: survival video game")
add_label_with_description(frame1, 1, "General Topic", "General category like: video game, food, city, person, etc.")
add_label_with_description(frame1, 2, "Time", "Video time in minutes")
add_label_with_description(frame1, 3, "Intro Video", "Do you want intro with video instead of photos?")
add_label_with_description(frame1, 4, "Pexels API", "Get API from www.pexels.com")
add_label_with_description(frame1, 5, "Language", "Video language")
add_label_with_description(frame1, 6, "Multi Speaker", "Use multiple speakers in video")
add_label_with_description(frame1, 7, "Use Gemini", "Use Gemini AI for TTS")
add_label_with_description(frame1, 8, "Text Model", "Gemini text generation model")
add_label_with_description(frame1, 9, "TTS Model", "Gemini TTS model")
add_label_with_description(frame1, 10, "TTS Voice", "Gemini TTS voice")
add_label_with_description(frame1, 11, "Use Claude", "Use Claude AI for content generation")
add_label_with_description(frame1, 12, "Claude API", "Claude API key from Anthropic")
add_label_with_description(frame1, 13, "Claude Model", "Claude model to use")
add_label_with_description(frame1, 14, "High Performance", "Use new high-performance processing")

topic_entry = tk.Entry(frame1)
topic_entry.grid(row=0, column=2, padx=5, pady=5)

general_topic_entry = tk.Entry(frame1)
general_topic_entry.grid(row=1, column=2, padx=5, pady=5)

time_entry = tk.Entry(frame1)
time_entry.grid(row=2, column=2, padx=5, pady=5)

intro_video_var = tk.StringVar(value="no")
intro_video_checkbox = ttk.Checkbutton(frame1, variable=intro_video_var, onvalue="yes", offvalue="no")
intro_video_checkbox.grid(row=3, column=2, padx=5, pady=5)

pexels_entry = tk.Entry(frame1)
pexels_entry.grid(row=4, column=2, padx=5, pady=5)

language_combobox = ttk.Combobox(frame1, values=LANGUAGES)
language_combobox.grid(row=5, column=2, padx=5, pady=5)

multi_speaker_var = tk.StringVar(value="no")
multi_speaker_checkbox = ttk.Checkbutton(frame1, variable=multi_speaker_var, onvalue="yes", offvalue="no")
multi_speaker_checkbox.grid(row=6, column=2, padx=5, pady=5)

use_gemini_var = tk.StringVar(value="yes")
use_gemini_checkbox = ttk.Checkbutton(frame1, variable=use_gemini_var, onvalue="yes", offvalue="no")
use_gemini_checkbox.grid(row=7, column=2, padx=5, pady=5)

text_model_combobox = ttk.Combobox(frame1, values=TEXT_MODELS)
text_model_combobox.grid(row=8, column=2, padx=5, pady=5)

tts_model_combobox = ttk.Combobox(frame1, values=TTS_MODELS)
tts_model_combobox.grid(row=9, column=2, padx=5, pady=5)

tts_voice_combobox = ttk.Combobox(frame1, values=TTS_VOICES)
tts_voice_combobox.grid(row=10, column=2, padx=5, pady=5)

use_claude_var = tk.StringVar(value="no")
use_claude_checkbox = ttk.Checkbutton(frame1, variable=use_claude_var, onvalue="yes", offvalue="no")
use_claude_checkbox.grid(row=11, column=2, padx=5, pady=5)

claude_api_entry = tk.Entry(frame1)
claude_api_entry.grid(row=12, column=2, padx=5, pady=5)

claude_model_combobox = ttk.Combobox(frame1, values=CLAUDE_MODELS)
claude_model_combobox.grid(row=13, column=2, padx=5, pady=5)

use_async_var = tk.StringVar(value="yes")
use_async_checkbox = ttk.Checkbutton(frame1, variable=use_async_var, onvalue="yes", offvalue="no")
use_async_checkbox.grid(row=14, column=2, padx=5, pady=5)

# ----- Frame 2 (Short Video) Widgets -----
add_label_with_description(frame2, 0, "Topic", "Enter video topic. Example: cooking secrets")
add_label_with_description(frame2, 1, "Time", "Video time in seconds")
add_label_with_description(frame2, 2, "Language", "Video language")
add_label_with_description(frame2, 3, "Multi Speaker", "Use multiple speakers in video")
add_label_with_description(frame2, 4, "Pexels API", "Get API from www.pexels.com")
add_label_with_description(frame2, 5, "Use Gemini", "Use Gemini AI for TTS")
add_label_with_description(frame2, 6, "Text Model", "Gemini text generation model")
add_label_with_description(frame2, 7, "TTS Model", "Gemini TTS model")
add_label_with_description(frame2, 8, "TTS Voice", "Gemini TTS voice")
add_label_with_description(frame2, 9, "Use Claude", "Use Claude AI for content generation")
add_label_with_description(frame2, 10, "Claude API", "Claude API key from Anthropic")
add_label_with_description(frame2, 11, "Claude Model", "Claude model to use")
add_label_with_description(frame2, 12, "High Performance", "Use new high-performance processing")

topic_entry2 = tk.Entry(frame2)
topic_entry2.grid(row=0, column=2, padx=5, pady=5)

time_entry2 = tk.Entry(frame2)
time_entry2.grid(row=1, column=2, padx=5, pady=5)

language_combobox2 = ttk.Combobox(frame2, values=LANGUAGES)
language_combobox2.grid(row=2, column=2, padx=5, pady=5)

multi_speaker_var2 = tk.StringVar(value="no")
multi_speaker_checkbox2 = ttk.Checkbutton(frame2, variable=multi_speaker_var2, onvalue="yes", offvalue="no")
multi_speaker_checkbox2.grid(row=3, column=2, padx=5, pady=5)

pexels_entry2 = tk.Entry(frame2)
pexels_entry2.grid(row=4, column=2, padx=5, pady=5)

use_gemini_var2 = tk.StringVar(value="yes")
use_gemini_checkbox2 = ttk.Checkbutton(frame2, variable=use_gemini_var2, onvalue="yes", offvalue="no")
use_gemini_checkbox2.grid(row=5, column=2, padx=5, pady=5)

text_model_combobox2 = ttk.Combobox(frame2, values=TEXT_MODELS)
text_model_combobox2.grid(row=6, column=2, padx=5, pady=5)

tts_model_combobox2 = ttk.Combobox(frame2, values=TTS_MODELS)
tts_model_combobox2.grid(row=7, column=2, padx=5, pady=5)

tts_voice_combobox2 = ttk.Combobox(frame2, values=TTS_VOICES)
tts_voice_combobox2.grid(row=8, column=2, padx=5, pady=5)

use_claude_var2 = tk.StringVar(value="no")
use_claude_checkbox2 = ttk.Checkbutton(frame2, variable=use_claude_var2, onvalue="yes", offvalue="no")
use_claude_checkbox2.grid(row=9, column=2, padx=5, pady=5)

claude_api_entry2 = tk.Entry(frame2)
claude_api_entry2.grid(row=10, column=2, padx=5, pady=5)

claude_model_combobox2 = ttk.Combobox(frame2, values=CLAUDE_MODELS)
claude_model_combobox2.grid(row=11, column=2, padx=5, pady=5)

use_async_var2 = tk.StringVar(value="yes")
use_async_checkbox2 = ttk.Checkbutton(frame2, variable=use_async_var2, onvalue="yes", offvalue="no")
use_async_checkbox2.grid(row=12, column=2, padx=5, pady=5)

# Add buttons at the bottom of both frames
button_frame1 = ttk.Frame(frame1)
button_frame1.grid(row=15, column=0, columnspan=3, pady=20)

run_button1 = ttk.Button(button_frame1, text="Generate Video", command=save_config)
run_button1.pack(pady=10)

button_frame2 = ttk.Frame(frame2)
button_frame2.grid(row=13, column=0, columnspan=3, pady=20)

run_button2 = ttk.Button(button_frame2, text="Generate Short Video", command=save_config)
run_button2.pack(pady=10)

# Load existing config values
config = read_config_file()

# Set default values for Long Video tab
general_topic_entry.insert(0, config.get('general_topic', 'video game'))
time_entry.insert(0, config.get('time', '5'))
intro_video_var.set(config.get('intro_video', 'no'))
pexels_entry.insert(0, config.get('pexels_api', ''))
language_combobox.set(config.get('language', 'english'))
multi_speaker_var.set(config.get('multi_speaker', 'no'))
use_gemini_var.set(config.get('use_gemini', 'yes'))
text_model_combobox.set(config.get('text_model', 'gemini-1.5-flash-latest'))
tts_model_combobox.set(config.get('tts_model', 'gemini-2.5-flash-preview-tts'))
tts_voice_combobox.set(config.get('tts_voice', 'Kore'))
use_claude_var.set(config.get('use_claude', 'no'))
claude_api_entry.insert(0, config.get('claude_api', ''))
claude_model_combobox.set(config.get('claude_model', 'claude-3-haiku-20240307'))
use_async_var.set('yes')  # Always use async by default for better performance

# Set default values for Short Video tab
time_entry2.insert(0, '30')  # Default 30 seconds for short videos
language_combobox2.set(config.get('language', 'english'))
multi_speaker_var2.set(config.get('multi_speaker', 'no'))
pexels_entry2.insert(0, config.get('pexels_api', ''))
use_gemini_var2.set(config.get('use_gemini', 'yes'))
text_model_combobox2.set(config.get('text_model', 'gemini-1.5-flash-latest'))
tts_model_combobox2.set(config.get('tts_model', 'gemini-2.5-flash-preview-tts'))
tts_voice_combobox2.set(config.get('tts_voice', 'Puck'))  # More upbeat voice for shorts
use_claude_var2.set(config.get('use_claude', 'no'))
claude_api_entry2.insert(0, config.get('claude_api', ''))
claude_model_combobox2.set(config.get('claude_model', 'claude-3-haiku-20240307'))
use_async_var2.set('yes')  # Always use async by default for better performance

# Start the main event loop
root.mainloop()
