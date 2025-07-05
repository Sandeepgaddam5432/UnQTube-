import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import sys
import io
from contextlib import redirect_stdout
from lib.core import making_video
from lib.shortcore import final_video
from lib.video_texts import read_config_file
from lib.config_utils import update_config_file
from lib.async_core import make_video_async, make_short_video_async, cleanup

# Dynamic model loading
from lib.gemini_api import list_available_gemini_models, get_default_models

class ModernUnQTubeGUI:
    """Modern redesigned GUI for UnQTube with advanced features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UnQTube - AI Video Generator")
        self.root.geometry("900x800")
        self.root.configure(bg='#2b2b2b')
        
        # Configure modern styling
        self.setup_styling()
        
        # Initialize variables
        self.init_variables()
        
        # Create the main interface
        self.create_main_interface()
        
        # Load models if API key exists
        self.load_initial_models()
        
    def setup_styling(self):
        """Setup modern dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure dark theme colors
        style.configure('TNotebook', background='#2b2b2b', borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], background='#404040', foreground='white')
        style.map('TNotebook.Tab', background=[('selected', '#0078d4'), ('active', '#555555')])
        
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Segoe UI', 9))
        style.configure('TButton', padding=[10, 5], font=('Segoe UI', 9, 'bold'))
        style.configure('Modern.TButton', padding=[15, 8], font=('Segoe UI', 10, 'bold'))
        style.configure('TEntry', fieldbackground='#404040', foreground='white', borderwidth=1)
        style.configure('TCombobox', fieldbackground='#404040', foreground='white', borderwidth=1)
        style.configure('TCheckbutton', background='#2b2b2b', foreground='white', font=('Segoe UI', 9))
        
        # Progress bar styling
        style.configure("Modern.Horizontal.TProgressbar", background='#0078d4', troughcolor='#404040', borderwidth=0)
        
    def init_variables(self):
        """Initialize all tkinter variables"""
        # Tab 1 variables
        self.topic_var = tk.StringVar()
        self.general_topic_var = tk.StringVar(value="video game")
        self.time_var = tk.StringVar(value="5")
        self.intro_video_var = tk.StringVar(value="no")
        self.pexels_api_var = tk.StringVar()
        self.language_var = tk.StringVar(value="english")
        self.multi_speaker_var = tk.StringVar(value="no")
        self.use_gemini_var = tk.StringVar(value="yes")
        self.text_model_var = tk.StringVar()
        self.tts_model_var = tk.StringVar()
        self.tts_voice_var = tk.StringVar()
        self.gemini_api_var = tk.StringVar()
        self.use_async_var = tk.StringVar(value="yes")
        
        # Tab 2 variables
        self.topic2_var = tk.StringVar()
        self.time2_var = tk.StringVar(value="30")
        self.language2_var = tk.StringVar(value="english")
        self.multi_speaker2_var = tk.StringVar(value="no")
        self.pexels_api2_var = tk.StringVar()
        self.use_gemini2_var = tk.StringVar(value="yes")
        self.text_model2_var = tk.StringVar()
        self.tts_model2_var = tk.StringVar()
        self.tts_voice2_var = tk.StringVar()
        self.gemini_api2_var = tk.StringVar()
        self.use_async2_var = tk.StringVar(value="yes")
        
        # Language options
        self.languages = [
            "english", "hindi", "bengali", "telugu", "marathi", "tamil", "urdu",
            "gujarati", "kannada", "malayalam", "punjabi", "assamese", "odia",
            "persian", "arabic", "vietnamese", "zulu", "afrikaans", "amharic",
            "azerbaijani", "bulgarian", "bosnian", "catalan", "czech", "welsh",
            "danish", "german", "greek", "spanish", "estonian", "filipino",
            "finnish", "french", "irish", "galician", "hebrew", "croatian",
            "hungarian", "indonesian", "icelandic", "italian", "japanese",
            "javanese", "georgian", "kazakh", "khmer", "korean", "lao",
            "lithuanian", "latvian", "macedonian", "mongolian", "malay", "maltese",
            "burmese", "norwegian", "nepali", "dutch", "polish", "pashto",
            "portuguese", "romanian", "russian", "sinhala", "slovak", "slovenian",
            "somali", "albanian", "serbian", "sundanese", "swedish", "swahili",
            "thai", "turkish", "ukrainian", "uzbek"
        ]
        
        # Initial model loading
        initial_models = get_default_models()
        self.text_models = initial_models.get("text_models", [])
        self.tts_models = initial_models.get("tts_models", [])
        self.tts_voices = initial_models.get("all_voices", [])
        
    def create_main_interface(self):
        """Create the main interface with modern design"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, pady=(20, 0))
        
        # Create tabs
        self.create_long_video_tab()
        self.create_short_video_tab()
        
        # Progress and status section
        self.create_progress_section(main_container)
        
    def create_header(self, parent):
        """Create modern header section"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="🎬 UnQTube", font=('Segoe UI', 24, 'bold'), foreground='#0078d4')
        title_label.pack(side='left')
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="AI-Powered Video Generator", font=('Segoe UI', 12), foreground='#888888')
        subtitle_label.pack(side='left', padx=(10, 0))
        
        # Status indicator
        self.status_label = ttk.Label(header_frame, text="● Ready", font=('Segoe UI', 10), foreground='#00d400')
        self.status_label.pack(side='right')
        
    def create_long_video_tab(self):
        """Create the long video generation tab with modern layout"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text='📹 Long Video (5-10 min)')
        
        # Create scrollable frame
        canvas = tk.Canvas(tab_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content sections
        self.create_content_section(scrollable_frame, "Content Settings", [
            ("Topic:", self.topic_var, "Enter your video topic (e.g., 'survival video games')"),
            ("General Topic:", self.general_topic_var, "Category (e.g., 'video game', 'food', 'travel')"),
            ("Duration (min):", self.time_var, "Video length in minutes (recommended: 5-10)"),
            ("Language:", self.language_var, "Select video language", "combobox", self.languages)
        ])
        
        self.create_ai_section(scrollable_frame, 1)
        
        self.create_options_section(scrollable_frame, "Additional Options", [
            ("Use intro video:", self.intro_video_var, "Use video clips in intro instead of images", "checkbox"),
            ("Multiple speakers:", self.multi_speaker_var, "Use different voices for variety", "checkbox"),
            ("High-performance mode:", self.use_async_var, "Use optimized async processing (recommended)", "checkbox")
        ])
        
        self.create_api_section(scrollable_frame, 1)
        
        # Generate button
        self.create_generate_button(scrollable_frame, "🎬 Generate Long Video", lambda: self.generate_video(1))
        
    def create_short_video_tab(self):
        """Create the short video generation tab with modern layout"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text='📱 Short Video (30-60 sec)')
        
        # Create scrollable frame
        canvas = tk.Canvas(tab_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content sections
        self.create_content_section(scrollable_frame, "Content Settings", [
            ("Topic:", self.topic2_var, "Enter your short video topic (e.g., 'cooking tips')"),
            ("Duration (sec):", self.time2_var, "Video length in seconds (recommended: 30-60)"),
            ("Language:", self.language2_var, "Select video language", "combobox", self.languages)
        ])
        
        self.create_ai_section(scrollable_frame, 2)
        
        self.create_options_section(scrollable_frame, "Additional Options", [
            ("Multiple speakers:", self.multi_speaker2_var, "Use different voices for variety", "checkbox"),
            ("High-performance mode:", self.use_async2_var, "Use optimized async processing (recommended)", "checkbox")
        ])
        
        self.create_api_section(scrollable_frame, 2)
        
        # Generate button
        self.create_generate_button(scrollable_frame, "🎬 Generate Short Video", lambda: self.generate_video(2))
        
    def create_section_header(self, parent, title):
        """Create a modern section header"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(20, 10))
        
        header_label = ttk.Label(header_frame, text=title, font=('Segoe UI', 14, 'bold'), foreground='#0078d4')
        header_label.pack(side='left')
        
        # Separator line
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
    def create_content_section(self, parent, title, fields):
        """Create a content section with fields"""
        self.create_section_header(parent, title)
        
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        for i, field in enumerate(fields):
            self.create_field(content_frame, field, i)
            
    def create_field(self, parent, field_config, row):
        """Create a modern input field"""
        label_text, variable, description = field_config[:3]
        field_type = field_config[3] if len(field_config) > 3 else "entry"
        options = field_config[4] if len(field_config) > 4 else None
        
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill='x', pady=5)
        
        # Label
        label = ttk.Label(field_frame, text=label_text, font=('Segoe UI', 9, 'bold'), width=15, anchor='w')
        label.pack(side='left', padx=(0, 10))
        
        # Input widget
        if field_type == "combobox":
            widget = ttk.Combobox(field_frame, textvariable=variable, values=options, state="readonly", width=30)
        elif field_type == "checkbox":
            widget = ttk.Checkbutton(field_frame, variable=variable, onvalue="yes", offvalue="no")
        else:
            widget = ttk.Entry(field_frame, textvariable=variable, width=35)
            
        widget.pack(side='left', padx=(0, 10))
        
        # Description
        desc_label = ttk.Label(field_frame, text=description, font=('Segoe UI', 8), foreground='#888888')
        desc_label.pack(side='left', fill='x', expand=True)
        
        return widget
        
    def create_ai_section(self, parent, tab_num):
        """Create AI model configuration section"""
        self.create_section_header(parent, "🤖 AI Model Settings")
        
        ai_frame = ttk.Frame(parent)
        ai_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        variables = (self.text_model_var, self.tts_model_var, self.tts_voice_var) if tab_num == 1 else (self.text_model2_var, self.tts_model2_var, self.tts_voice2_var)
        
        # Text model
        text_widget = self.create_field(ai_frame, ("Text Model:", variables[0], "AI model for script generation", "combobox", self.text_models), 0)
        setattr(self, f'text_model_combobox{tab_num if tab_num > 1 else ""}', text_widget)
        
        # TTS model
        tts_widget = self.create_field(ai_frame, ("TTS Model:", variables[1], "AI model for voice synthesis", "combobox", self.tts_models), 1)
        setattr(self, f'tts_model_combobox{tab_num if tab_num > 1 else ""}', tts_widget)
        
        # TTS voice
        voice_widget = self.create_field(ai_frame, ("Voice:", variables[2], "Voice character for narration", "combobox", self.tts_voices), 2)
        setattr(self, f'tts_voice_combobox{tab_num if tab_num > 1 else ""}', voice_widget)
        
    def create_options_section(self, parent, title, options):
        """Create options section with checkboxes"""
        self.create_section_header(parent, title)
        
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        for i, option in enumerate(options):
            self.create_field(options_frame, option, i)
            
    def create_api_section(self, parent, tab_num):
        """Create API keys section"""
        self.create_section_header(parent, "🔑 API Configuration")
        
        api_frame = ttk.Frame(parent)
        api_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Gemini API
        gemini_var = self.gemini_api_var if tab_num == 1 else self.gemini_api2_var
        gemini_widget = self.create_field(api_frame, ("Gemini API Key:", gemini_var, "Get your free API key from Google AI Studio"), 0)
        setattr(self, f'gemini_api_entry{tab_num if tab_num > 1 else ""}', gemini_widget)
        
        # Bind API key change event
        gemini_widget.bind('<KeyRelease>', self.on_api_key_change if tab_num == 1 else self.on_api_key_change2)
        
        # Pexels API
        pexels_var = self.pexels_api_var if tab_num == 1 else self.pexels_api2_var
        self.create_field(api_frame, ("Pexels API Key:", pexels_var, "Get your free API key from Pexels.com for stock footage"), 1)
        
        # Info frame
        info_frame = ttk.Frame(api_frame)
        info_frame.pack(fill='x', pady=10)
        
        info_text = "💡 Get Gemini API: https://ai.google.dev/ | Get Pexels API: https://www.pexels.com/api/"
        info_label = ttk.Label(info_frame, text=info_text, font=('Segoe UI', 8), foreground='#0078d4')
        info_label.pack()
        
    def create_generate_button(self, parent, text, command):
        """Create a modern generate button"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=20)
        
        button = ttk.Button(button_frame, text=text, command=command, style='Modern.TButton')
        button.pack(pady=20)
        
    def create_progress_section(self, parent):
        """Create progress and status section"""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill='x', pady=(20, 0))
        
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="Ready to generate videos", font=('Segoe UI', 10))
        self.progress_label.pack(fill='x')
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', style="Modern.Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=(5, 10))
        
        # Status log
        log_label = ttk.Label(progress_frame, text="📋 Status Log:", font=('Segoe UI', 10, 'bold'))
        log_label.pack(anchor='w')
        
        self.status_log = scrolledtext.ScrolledText(progress_frame, height=8, bg='#1e1e1e', fg='#ffffff', 
                                                   font=('Consolas', 9), wrap=tk.WORD)
        self.status_log.pack(fill='both', expand=True, pady=(5, 0))
        self.status_log.insert(tk.END, "UnQTube AI Video Generator ready.\n")
        self.status_log.insert(tk.END, "Enter your API keys and video topic to get started.\n")
        
    def log_message(self, message):
        """Add a message to the status log"""
        self.status_log.insert(tk.END, f"{message}\n")
        self.status_log.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, status, color='#00d400'):
        """Update the status indicator"""
        self.status_label.configure(text=f"● {status}", foreground=color)
        
    def update_progress(self, message):
        """Update progress message and log"""
        self.progress_label.configure(text=message)
        self.log_message(message)
        
    def start_progress(self):
        """Start progress bar animation"""
        self.progress_bar.start(10)
        
    def stop_progress(self):
        """Stop progress bar animation"""
        self.progress_bar.stop()
        
    def load_available_models(self, api_key=None):
        """Load available models from Google AI API"""
        try:
            models = list_available_gemini_models(api_key)
            return models
        except Exception as e:
            self.log_message(f"Error loading models: {e}")
            return get_default_models()

    def update_model_dropdowns(self, api_key=None):
        """Update model dropdowns with available models from API"""
        try:
            models = self.load_available_models(api_key)
            
            # Update text model dropdowns
            text_models = models.get("text_models", [])
            if text_models:
                self.text_model_combobox['values'] = text_models
                self.text_model_combobox2['values'] = text_models
                if self.text_model_combobox.get() not in text_models:
                    self.text_model_combobox.set(text_models[0] if text_models else "")
                if self.text_model_combobox2.get() not in text_models:
                    self.text_model_combobox2.set(text_models[0] if text_models else "")
            
            # Update TTS model dropdowns
            tts_models = models.get("tts_models", [])
            if tts_models:
                self.tts_model_combobox['values'] = tts_models
                self.tts_model_combobox2['values'] = tts_models
                if self.tts_model_combobox.get() not in tts_models:
                    self.tts_model_combobox.set(tts_models[0] if tts_models else "")
                if self.tts_model_combobox2.get() not in tts_models:
                    self.tts_model_combobox2.set(tts_models[0] if tts_models else "")
            
            # Update TTS voice dropdowns
            voices = models.get("all_voices", [])
            if voices:
                self.tts_voice_combobox['values'] = voices
                self.tts_voice_combobox2['values'] = voices
                if self.tts_voice_combobox.get() not in voices:
                    self.tts_voice_combobox.set(voices[0] if voices else "")
                if self.tts_voice_combobox2.get() not in voices:
                    self.tts_voice_combobox2.set(voices[0] if voices else "")
            
            self.log_message(f"✅ Updated dropdowns with {len(text_models)} text models, {len(tts_models)} TTS models, and {len(voices)} voices")
            
        except Exception as e:
            self.log_message(f"Error updating model dropdowns: {e}")

    def on_api_key_change(self, event=None):
        """Called when API key field changes in tab 1"""
        api_key = self.gemini_api_var.get().strip()
        if api_key and len(api_key) > 10:
            self.log_message("🔄 Loading available models...")
            self.update_model_dropdowns(api_key)

    def on_api_key_change2(self, event=None):
        """Called when API key field changes in tab 2"""
        api_key = self.gemini_api2_var.get().strip()
        if api_key and len(api_key) > 10:
            self.log_message("🔄 Loading available models...")
            self.update_model_dropdowns(api_key)

    def load_initial_models(self):
        """Load models on startup if API key exists"""
        config = read_config_file()
        existing_api_key = config.get('gemini_api', '').strip()
        
        # Set initial values
        self.topic_var.set("")
        self.general_topic_var.set(config.get('general_topic', 'video game'))
        self.time_var.set(config.get('time', '5'))
        self.intro_video_var.set(config.get('intro_video', 'no'))
        self.pexels_api_var.set(config.get('pexels_api', ''))
        self.language_var.set(config.get('language', 'english'))
        self.multi_speaker_var.set(config.get('multi_speaker', 'no'))
        self.use_gemini_var.set(config.get('use_gemini', 'yes'))
        self.text_model_var.set(config.get('text_model', self.text_models[0] if self.text_models else ''))
        self.tts_model_var.set(config.get('tts_model', self.tts_models[0] if self.tts_models else ''))
        self.tts_voice_var.set(config.get('tts_voice', self.tts_voices[0] if self.tts_voices else ''))
        self.gemini_api_var.set(existing_api_key)
        
        # Set values for tab 2
        self.topic2_var.set("")
        self.time2_var.set("30")
        self.language2_var.set(config.get('language', 'english'))
        self.multi_speaker2_var.set(config.get('multi_speaker', 'no'))
        self.pexels_api2_var.set(config.get('pexels_api', ''))
        self.use_gemini2_var.set(config.get('use_gemini', 'yes'))
        self.text_model2_var.set(config.get('text_model', self.text_models[0] if self.text_models else ''))
        self.tts_model2_var.set(config.get('tts_model', self.tts_models[0] if self.tts_models else ''))
        self.tts_voice2_var.set(config.get('tts_voice', 'Puck'))  # More upbeat for shorts
        self.gemini_api2_var.set(existing_api_key)
        
        if existing_api_key and len(existing_api_key) > 10:
            self.log_message("🔄 Loading models from existing API key...")
            self.update_model_dropdowns(existing_api_key)
            
    def save_config(self, tab_num):
        """Save configuration for the specified tab"""
        try:
            if tab_num == 1:
                # Long video configuration
                update_config_file('config.txt', 'general_topic', self.general_topic_var.get())
                update_config_file('config.txt', 'time', self.time_var.get())
                update_config_file('config.txt', 'intro_video', self.intro_video_var.get())
                update_config_file('config.txt', 'pexels_api', self.pexels_api_var.get())
                update_config_file('config.txt', 'language', self.language_var.get())
                update_config_file('config.txt', 'multi_speaker', self.multi_speaker_var.get())
                update_config_file('config.txt', 'use_gemini', self.use_gemini_var.get())
                update_config_file('config.txt', 'text_model', self.text_model_var.get())
                update_config_file('config.txt', 'tts_model', self.tts_model_var.get())
                update_config_file('config.txt', 'tts_voice', self.tts_voice_var.get())
                update_config_file('config.txt', 'gemini_api', self.gemini_api_var.get())
            else:
                # Short video configuration
                update_config_file('config.txt', 'time', self.time2_var.get())
                update_config_file('config.txt', 'language', self.language2_var.get())
                update_config_file('config.txt', 'multi_speaker', self.multi_speaker2_var.get())
                update_config_file('config.txt', 'pexels_api', self.pexels_api2_var.get())
                update_config_file('config.txt', 'use_gemini', self.use_gemini2_var.get())
                update_config_file('config.txt', 'text_model', self.text_model2_var.get())
                update_config_file('config.txt', 'tts_model', self.tts_model2_var.get())
                update_config_file('config.txt', 'tts_voice', self.tts_voice2_var.get())
                update_config_file('config.txt', 'gemini_api', self.gemini_api2_var.get())
                
            self.log_message("✅ Configuration saved successfully")
        except Exception as e:
            self.log_message(f"❌ Error saving configuration: {e}")
            
    def generate_video(self, tab_num):
        """Generate video based on tab selection"""
        try:
            # Validation
            topic = self.topic_var.get().strip() if tab_num == 1 else self.topic2_var.get().strip()
            if not topic:
                messagebox.showerror("Error", "Please enter a video topic")
                return
                
            api_key = self.gemini_api_var.get().strip() if tab_num == 1 else self.gemini_api2_var.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter your Gemini API key")
                return
                
            # Save configuration
            self.save_config(tab_num)
            
            # Start generation
            self.update_status("Generating...", '#ff8c00')
            self.start_progress()
            
            if tab_num == 1:
                self.update_progress(f"🎬 Starting long video generation for: {topic}")
                general_topic = self.general_topic_var.get().strip()
                
                if self.use_async_var.get() == "yes":
                    self.run_async_generation(make_video_async, topic, general_topic)
                else:
                    self.run_sync_generation(making_video, topic)
            else:
                self.update_progress(f"📱 Starting short video generation for: {topic}")
                time_seconds = self.time2_var.get().strip()
                
                if self.use_async2_var.get() == "yes":
                    self.run_async_generation(make_short_video_async, topic, int(time_seconds))
                else:
                    language = self.language2_var.get()
                    multi_speaker = self.multi_speaker2_var.get()
                    self.run_sync_generation(final_video, topic, time_seconds, language, multi_speaker)
                    
        except Exception as e:
            self.stop_progress()
            self.update_status("Error", '#ff0000')
            self.log_message(f"❌ Error: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
            
    def run_async_generation(self, func, *args):
        """Run async video generation in a separate thread"""
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Capture output
                output_capture = io.StringIO()
                with redirect_stdout(output_capture):
                    loop.run_until_complete(func(*args))
                
                # Process captured output
                output = output_capture.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log_message(line.strip())
                        
                self.generation_complete()
            except Exception as e:
                self.generation_error(str(e))
            finally:
                loop.close()
                
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        
    def run_sync_generation(self, func, *args):
        """Run sync video generation in a separate thread"""
        def run_sync():
            try:
                # Capture output
                output_capture = io.StringIO()
                with redirect_stdout(output_capture):
                    func(*args)
                
                # Process captured output
                output = output_capture.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log_message(line.strip())
                        
                self.generation_complete()
            except Exception as e:
                self.generation_error(str(e))
                
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
        
    def generation_complete(self):
        """Called when video generation completes successfully"""
        self.root.after(0, lambda: [
            self.stop_progress(),
            self.update_status("Complete", '#00d400'),
            self.update_progress("✅ Video generation completed successfully!"),
            messagebox.showinfo("Success", "Video generated successfully! Check your output folder.")
        ])
        
    def generation_error(self, error_msg):
        """Called when video generation encounters an error"""
        self.root.after(0, lambda: [
            self.stop_progress(),
            self.update_status("Error", '#ff0000'),
            self.update_progress(f"❌ Generation failed: {error_msg}"),
            messagebox.showerror("Error", f"Video generation failed: {error_msg}")
        ])
        
    def run(self):
        """Start the GUI application"""
        self.log_message("🚀 UnQTube started successfully!")
        self.root.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = ModernUnQTubeGUI()
    app.run()
