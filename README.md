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

If you prefer not to install the prerequisites on your local system, you can use the Google Colab notebook. This option is free and requires no installation setup.

1. Click on the link to the Google Colab notebook: [https://colab.research.google.com/drive/1Z0Scppdihf2csuUJF20UiuRrHCoCNqIr?usp=sharing](https://colab.research.google.com/drive/1Z0Scppdihf2csuUJF20UiuRrHCoCNqIr?usp=sharing)
   
2. First, run "Run Frist" cell to install prerequisites

3. Now set "Short Video" or "Long Video" cell settings and run it

Important : For make short video or intro with video in long video,you need set pexels API (get pexels API from [pexels.com](pexels.com) for free)

# 🖥️Running UnQTube on Google Colab

Follow these steps to run UnQTube directly on Google Colab:

1. Open a new Google Colab notebook at [colab.research.google.com](https://colab.research.google.com)

2. Install required system packages (for tkinter support):
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

6. Run the tool (command-line method recommended for Colab):
   
   For long videos:
   ```
   !python video.py -topic "your topic here" -general_topic "general topic" -time "5" -language "english"
   ```
   
   For short videos:
   ```
   !python short.py -topic "your topic here" -time "30" -language "english"
   ```

   **Note**: GUI version (`rungui.py`) is not recommended for Colab as tkinter interfaces cannot display directly in the notebook environment.

7. Important: For videos with intro videos or short videos, you'll need a Pexels API key. You can get one for free from [pexels.com](https://pexels.com)

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
