# 🎬 UnQTube - Project Overview

## 1. High-level Purpose

**UnQTube** is an automated YouTube video generator that creates professional-quality videos without requiring manual editing. The project solves the problem of **time-consuming video creation** by automatically generating:

- **Top 10 videos** (long-form content, 5+ minutes)
- **Short videos** (30-60 seconds, vertical format)

The system uses AI (ChatGPT/Gemini) to generate scripts, automatically downloads relevant images/videos from stock footage APIs, creates voiceovers in multiple languages, and combines everything into a final video with background music.

**Key Problem Solved**: Enables content creators to produce engaging, professional YouTube videos at scale without manual editing, scripting, or media sourcing.

## 2. Technology Stack

### Core Technologies
- **Python 3.x** - Primary programming language
- **MoviePy** - Video editing and manipulation library
- **OpenCV** - Image processing and computer vision
- **Tkinter** - GUI framework for the desktop application

### AI & Content Generation
- **Google Gemini API** - Enhanced AI script generation and media search
- **ChatGPT Integration** - Alternative AI content generation
- **Edge-TTS** - Text-to-speech for voiceovers in 70+ languages

### Media & APIs
- **Pexels API** - Stock footage and image downloading
- **Requests** - HTTP client for API interactions
- **PIL (Pillow)** - Image processing and manipulation
- **PyDub** - Audio processing and manipulation

### Supporting Libraries
- **NumPy** - Numerical computations
- **Deep-Translator** - Multi-language translation
- **PyYAML** - Configuration management
- **Asyncio** - Asynchronous operations

## 3. Project Structure

```
UnQTube/
├── 📁 lib/                     # Core library modules
│   ├── core.py                 # Main long video creation logic
│   ├── shortcore.py            # Short video creation logic
│   ├── gemini_api.py           # AI integration (Gemini API)
│   ├── video_editor.py         # Video editing and merging
│   ├── voices.py               # Text-to-speech generation
│   ├── image_procces.py        # Image processing and optimization
│   ├── media_api.py            # Stock footage API integration
│   ├── video_texts.py          # Script generation and text processing
│   ├── language.py             # Language code management
│   └── config_utils.py         # Configuration file utilities
├── 📁 download_list/           # Configuration for media downloads
│   ├── background_music.txt    # Background music source URLs
│   └── outro_pic.txt           # Outro image source URLs
├── 📄 rungui.py               # Main GUI application
├── 📄 video.py                # CLI for long video creation
├── 📄 short.py                # CLI for short video creation
├── 📄 create_notebook.py      # Jupyter notebook generator
├── 📄 update_notebook.py      # Notebook maintenance utilities
├── 📄 fix_notebook.py         # Notebook repair utilities
├── 📄 config.txt              # Main configuration file
├── 📄 requirements.txt        # Python dependencies
├── 📄 UnQTube_Colab.ipynb     # Google Colab notebook
└── 📄 README.md               # Documentation
```

### Key Directory Purposes:
- **`lib/`**: Contains all core functionality modules
- **`download_list/`**: Configuration files for media sources
- **Root files**: Entry points for different usage methods (GUI, CLI, Colab)

## 4. How to Run

### Prerequisites
- Python 3.x installed
- Pip package manager
- Pexels API key (free from pexels.com)

### Method 1: GUI Application (Recommended for Beginners)
```bash
# 1. Clone the repository
git clone https://github.com/Sandeepgaddam5432/UnQTube-.git

# 2. Navigate to project directory
cd UnQTube-

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the GUI application
python rungui.py
```

The GUI provides two tabs:
- **Long Video**: For creating 5+ minute top 10 videos
- **Short Video**: For creating 30-60 second vertical videos

### Method 2: Command Line Interface
```bash
# For Long Videos
python video.py -topic "survival video games" -general_topic "video games" -time "5" -language "english" -pexels_api "YOUR_API_KEY"

# For Short Videos
python short.py -topic "cooking secrets" -time "30" -language "english" -pexels_api "YOUR_API_KEY"
```

### Method 3: Google Colab (No Local Setup Required)
1. Open the provided Colab notebook: `UnQTube_Colab.ipynb`
2. Run cells in sequence
3. Choose either long or short video creation

### Configuration
Edit `config.txt` to set default values:
```
general_topic = video game
time = 5
intro_video = no
pexels_api = YOUR_PEXELS_API_KEY
language = english
multi_speaker = no
use_gemini = yes
gemini_api = YOUR_GEMINI_API_KEY
```

## 5. Key Features

### Feature 1: **AI-Powered Script Generation** 
📍 **Location**: `lib/gemini_api.py`, `lib/video_texts.py`

**What it does**: Automatically generates engaging scripts for videos using AI
- Uses Google Gemini API for enhanced content generation
- Supports 70+ languages via translation
- Creates structured content with intro, main segments, and outro
- Generates search terms for relevant stock footage

**Key Functions**:
- `generate_complete_top10_content()` - Single API call for full video content
- `generate_short_video_script()` - Structured short video content
- `get_names()` - Generates top 10 lists for topics

### Feature 2: **Automated Media Processing Pipeline**
📍 **Location**: `lib/video_editor.py`, `lib/image_procces.py`, `lib/media_api.py`

**What it does**: Automatically sources, processes, and optimizes media content
- Downloads relevant images/videos from Pexels API
- Processes images (resizing, cropping, quality optimization)
- Removes invalid/corrupted media files
- Sorts and ranks media by relevance
- Handles multiple video formats and resolutions

**Key Functions**:
- `getim()` - Downloads images based on search terms
- `get_videos()` - Downloads stock footage
- `mergevideo()` - Combines all media into final video
- `resize_and_text()` - Optimizes video dimensions

### Feature 3: **Multi-Language Voice Generation**
📍 **Location**: `lib/voices.py`, `lib/language.py`

**What it does**: Creates professional voiceovers in 70+ languages
- Uses Edge-TTS for natural-sounding voices
- Supports multiple speakers for variety
- Handles long-form content with proper pacing
- Automatically translates content to target language

**Key Functions**:
- `generate_voice()` - Creates audio from text
- `get_language_code()` - Maps language names to codes
- `translateto()` - Translates content to target language

## Additional Notes

### Supported Languages
The project supports 70+ languages including English, Spanish, French, German, Japanese, Chinese, Arabic, Hindi, and many more.

### API Requirements
- **Pexels API**: Required for stock footage (free tier available)
- **Gemini API**: Optional but recommended for better content quality
- **No OpenAI API**: The project has moved away from requiring OpenAI API keys

### Output Formats
- **Long videos**: MP4, 1920x1080, 5+ minutes
- **Short videos**: MP4, 1080x1920 (vertical), 30-60 seconds

### Error Handling
The system includes comprehensive error handling with fallback mechanisms:
- Alternative AI models if primary fails
- Generic content generation if AI fails
- Emergency video creation if media download fails
- Automatic cleanup of temporary files

This project represents a sophisticated automation pipeline that transforms simple text prompts into professional video content, making it an excellent example of AI-powered content creation technology.