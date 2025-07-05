# 🎬UnQTube
⚡Automating top 10 and short YouTube video maker with ChatGPT without API⚡

UnQTube is an automated video creation tool that generates professional YouTube videos with minimal human input. It uses AI to generate scripts, download relevant stock media, create voiceovers, and combine everything into a final video.

## 🚀 Major New Features

### High-Performance Video Generation
The latest version features a drastically improved video generation pipeline that reduces creation time to under 5 minutes through:
- **Parallel Processing**: Simultaneous media downloading, script generation, and voice synthesis
- **Asynchronous Architecture**: Built with asyncio for maximum performance
- **Content Caching**: Smart caching system to avoid redundant operations

### Enhanced Content Quality
- **Sophisticated Content Generation**: Multi-step prompt chain for highly detailed, engaging scripts
- **Advanced Media Search**: More precise visual search terms for better stock footage
- **Dynamic Hooks**: Auto-generation of compelling hooks for various parts of the video

### Premium Audio with Gemini TTS
- **High-Quality Voices**: Integration with Google's Gemini TTS models for realistic voiceovers
- **Intelligent Voice Selection**: Context-aware voice parameter selection based on content
- **Fallback System**: Graceful fallback to edge-tts if Gemini is unavailable

## Types of Videos
UnQTube can generate two main types of videos:
1. **Long-form "Top 10" videos** (5+ minutes in duration)
2. **Short vertical videos** (30-60 seconds, designed for platforms like YouTube Shorts)

## Getting Started

### Prerequisites
- Python 3.8 or higher
- FFmpeg for video processing
- Pexels API key (free)
- Gemini API key (optional, for enhanced TTS)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/Sandeepgaddam5432/UnQTube.git
cd UnQTube
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Configure the application by editing the `config.txt` file or using the command-line options.

### Usage

#### Command Line Interface
Generate a long-form video:
```bash
python video.py -topic "Best Travel Destinations in Europe" -general_topic "travel" -use_async yes
```

Generate a short video:
```bash
python short.py -topic "Amazing Travel Facts" -time 30 -use_async yes
```

#### Graphical User Interface
Run the GUI application:
```bash
python rungui.py
```

## Configuration Options
- **topic**: The main subject of your video
- **general_topic**: The general category (e.g., travel, food, technology)
- **time**: Duration in minutes for long videos or seconds for short videos
- **intro_video**: Whether to use video (yes) or images (no) for the intro
- **pexels_api**: Your Pexels API key for downloading stock media
- **language**: Language for the video content and voiceover
- **multi_speaker**: Use multiple voices in the video
- **gemini_api**: Your Gemini API key for enhanced TTS (optional)
- **use_gemini**: Enable/disable Gemini TTS (yes/no)
- **use_async**: Use the high-performance async processing (yes/no)

## Performance Comparison
| Processing Mode | Average Video Generation Time |
|-----------------|-------------------------------|
| Legacy (Sync)   | 15-20 minutes                 |
| New (Async)     | 3-5 minutes                   |

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Thanks to Pexels for providing the stock media API
- Special thanks to all contributors and testers

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
