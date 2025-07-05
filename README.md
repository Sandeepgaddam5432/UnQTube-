# UnQTube - AI-Powered Video Generator

UnQTube is an advanced AI-powered video generation system that creates high-quality YouTube videos with minimal input. It uses sophisticated AI to generate scripts, narration, and visual content, then compiles everything into a complete video.

## 🌟 Features

- **Intelligent Content Generation**: Multi-step AI prompt chains for sophisticated, factually accurate content
- **Multiple AI Models**: Support for both Google Gemini and Anthropic Claude
- **High-Quality TTS**: Google Gemini TTS integration with 30+ premium voices and context-aware voice selection
- **Parallel Processing**: Asynchronous architecture for 3-5 minute video generation (vs 15-20 minutes previously)
- **Multilingual Support**: Generate videos in multiple languages, including all major Indian languages
- **User-Friendly Interface**: Both GUI and command-line options available
- **Short & Long Video Support**: Create both traditional long-form and short-form vertical videos

## 📊 Performance

- **Speed**: Generate complete videos in 3-5 minutes (vs 15-20 minutes in previous versions)
- **Quality**: Sophisticated multi-step AI prompting creates more engaging, factual content
- **Audio**: Premium voice quality with Gemini TTS and context-aware voice selection

## 🚀 Quick Start with Google Colab

The easiest way to get started is using our ready-to-use Google Colab notebooks:

[![Open Long Video Generator In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Sandeepgaddam5432/UnQTube/blob/main/UnQTube_Long_Video_Generator.ipynb) 
[![Open Short Video Generator In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Sandeepgaddam5432/UnQTube/blob/main/UnQTube_Short_Video_Generator.ipynb)

## 🖥️ Local Installation

1. Clone the repository:
<<<<<<< HEAD
```bash
git clone https://github.com/Sandeepgaddam5432/UnQTube.git
cd UnQTube
```
=======
  ```bash
  git clone https://github.com/Sandeepgaddam5432/UnQTube.git
  cd UnQTube
  ```
>>>>>>> 669c038 (feat: Integrate Claude AI, fix Gemini TTS, and add advanced features)

2. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

3. Set up your API keys in `config.txt`:
  ```
  gemini_api = YOUR_GEMINI_API_KEY
  pexels_api = YOUR_PEXELS_API_KEY
  use_gemini = yes
  claude_api = YOUR_CLAUDE_API_KEY  # Optional
  use_claude = no  # Set to 'yes' to use Claude instead of Gemini
  ```

## 🎮 Usage

### GUI Mode

Run the graphical interface:
```bash
python rungui.py
```

### Command Line Mode

Generate a long-form video:
```bash
python video.py "your video topic"
```

Generate a short-form video:
```bash
python short.py "your short video topic"
```

## 🔧 Configuration

Edit `config.txt` to customize your settings:

```
general_topic = video game  # General category for context
time = 5                    # Video length in minutes (for long videos)
intro_video = no            # Use video for intro instead of photos
pexels_api = YOUR_API_KEY   # Pexels API key for visuals
language = english          # Video language
multi_speaker = no          # Use multiple speakers
use_gemini = yes            # Use Gemini for TTS
gemini_api = YOUR_API_KEY   # Gemini API key
text_model = gemini-1.5-flash-latest  # Text generation model
tts_model = gemini-2.5-flash-preview-tts  # TTS model
tts_voice = Kore            # TTS voice name
use_claude = no             # Use Claude for content generation
claude_api = YOUR_API_KEY   # Claude API key
claude_model = claude-3-haiku-20240307  # Claude model
```

## 🤖 AI Model Options

### Gemini Models
UnQTube supports Google's Gemini AI for script generation and TTS:

- **Text Generation Models**:
  - `gemini-1.5-flash-latest` - Fast, efficient text generation
  - `gemini-1.5-pro-latest` - Higher quality, more detailed content

- **TTS Models**:
  - `gemini-2.5-flash-preview-tts` - Fast TTS generation
  - `gemini-2.5-pro-preview-tts` - Higher quality voice synthesis

### Claude Models
UnQTube now supports Anthropic's Claude AI as an alternative for content generation:

- **Available Models**:
  - `claude-3-haiku-20240307` - Fast, efficient text generation
  - `claude-3-sonnet-20240229` - Balanced speed and quality
  - `claude-3-opus-20240229` - Highest quality, most detailed content

To use Claude, set `use_claude = yes` in your config.txt file and provide your Claude API key.

## 🗣️ Supported Languages

UnQTube now supports all major Indian languages, including:
- Hindi, Bengali, Telugu, Marathi, Tamil
- Urdu, Gujarati, Kannada, Malayalam, Punjabi
- Assamese, Odia, and many more

Plus dozens of other international languages.

## 🎙️ Voice Options

The Gemini TTS integration includes 30 premium voices with different characteristics:
- **Kore** - Firm, authoritative
- **Puck** - Upbeat, energetic
- **Charon** - Informative, educational
- **Fenrir** - Excitable, enthusiastic
- **Enceladus** - Breathy, intimate
- And many more to suit different content styles

## 🛠️ Advanced Features

- **Intelligent Rate Limiting**: Exponential backoff for API rate limits
- **Caching System**: Improved performance through strategic caching
- **JSON Validation**: Robust parsing with fallback mechanisms
- **Parallel Processing**: Asynchronous architecture for faster generation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Pexels](https://www.pexels.com/) for providing the visual content API
- [Google Gemini](https://ai.google.dev/) for the advanced AI capabilities
- [Edge-TTS](https://github.com/rany2/edge-tts) for the fallback TTS system

# 🎬UnQTube
⚡Automating top 10 and short YouTube video maker with ChatGPT without API⚡

Created by: Sandeep Gaddam

## Sample Top 10 video

<div align="center">
Top 10 "survival video games"
</div>

https://github.com/amirreza1307/YouTube-video-maker/assets/135555619/e688192a-e7bc-426e-98d2-c48a6a3a0535

## Sample short video
<div align="center">
"Cooking secrets"
</div>



https://github.com/amirreza1307/YouTube-video-maker/assets/135555619/3b48b592-b1c6-4454-b1e1-ff4dfa539d58


# 🚀Run on Google Colab (Recommended)

The easiest way to use UnQTube is directly in Google Colab without any local installation:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Sandeepgaddam5432/UnQTube-/blob/main/UnQTube_Colab.ipynb)

1. Click the "Open In Colab" button above to open the UnQTube notebook in Google Colab
2. Run the cells in sequence:
   - First cell: Installs system requirements
   - Second cell: Clones the repository and installs dependencies
   - Choose either "Long Video" or "Short Video" cell to run

Important: For videos with intro videos or short videos, you'll need a Pexels API key. You can get one for free from [pexels.com](pexels.com).

### Alternative Manual Setup in Colab

If you prefer to set up manually in your own Colab notebook:

1. Open a new Google Colab notebook at [colab.research.google.com](https://colab.research.google.com)

2. Install required system packages:
   ```
   !apt-get update
   !apt-get install -y python3-tk
   ```

3. Clone the repository:
   ```
   !git clone https://github.com/Sandeepgaddam5432/UnQTube-.git
   ```

4. Change to the project directory:
   ```
   %cd UnQTube-
   ```

5. Install the required dependencies:
   ```
   !pip install -r requirements.txt
   ```

6. Run the tool (command-line method for Colab):
   
   For long videos:
   ```
   !python video.py -topic "your topic here" -general_topic "general topic" -time "5" -language "english"
   ```
   
   For short videos:
   ```
   !python short.py -topic "your topic here" -time "30" -language "english"
   ```

# 🎥Run on local system
## Prerequisites

Before you begin, ensure that you have the following prerequisites installed on your system:
- Python 3.x
- Pip (Python package installer)

## Installation Steps
### Step 1: Clone Repository
   ```
   git clone https://github.com/Sandeepgaddam5432/UnQTube-.git
   ```
### Step 2: install Requirements

   ```
   cd UnQTube-
   ```
   ```
   pip install -r requirements.txt
   ```
### Step 3: Run

1. You can run `rungui.py` set config and run to make video. 

   ```
   python rungui.py
   ```
2. If you don't want run with gui, you can use this commands
   #### For Long Video
   ```
   python video.py -topic "$topic" -general_topic "$general_topic" -time "$time" -intro_video "$intro_video" -pexels_api "$pexels_api" -language "$language" -multi_speaker "$multi_speaker"
   ```
   #### For Short Video
   ```
   python short.py -topic "$topic" -time "$time" -language "$language" -multi_speaker "$multi_speaker" -pexels_api "$pexels_api"
   ```
   Replace variables with desired settings

## 🎞️Custom background music and outro pic

for use your custom background music and outro pic in video put this download link on `download_list\background_music.txt` and `download_list\outro_pic.txt`

# Required APIs

- **Openai**: There is no need now
- **pexels API**: get from [pexels.com](pexels.com) for free
- **Gemini API (Optional)**: For enhanced script generation and media search, get API key from [Google AI Studio](https://aistudio.google.com/)

# 🤖 Gemini Integration

UnQTube now supports Google's Gemini AI for enhanced script generation and media search:

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
2. Add your API key to config.txt:
   ```
   gemini_api = YOUR_GEMINI_API_KEY
   use_gemini = yes
   ```

Benefits of using Gemini:
- Better script generation for more engaging content
- Enhanced search terms for finding more relevant images and videos
- Higher quality visuals that match your script content

To disable Gemini and use the original ChatGPT integration, set `use_gemini = no` in config.txt.
