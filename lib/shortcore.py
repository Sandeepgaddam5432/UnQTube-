import os
import shutil
import sys
import re
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

from lib.video_texts import getyamll, read_random_line
from lib.config_utils import read_config_file
from lib.media_api import download_file, translateto
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.core import get_temp_dir
from lib.gemini_api import generate_short_video_script

def get_video(prompt, videoname):
    """Download stock video based on search prompt"""
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": read_config_file()["pexels_api"]
    }
    params = {
        "query": prompt,
        "per_page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()

    try:
        link = json_data['videos'][0]['video_files'][0]['link']
        download_file(link, videoname)
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error getting video for '{prompt}': {e}")
        raise Exception(f"Unable to find a suitable video for '{prompt}'")


def resize_and_text(videopath, targetwidth=1080, targetheight=1920):
    video_clip = VideoFileClip(videopath+".mp4")
    width = video_clip.size[0]
    height = video_clip.size[1]
    odd = 1.0

    while(int(height * odd) < targetheight or int(width * odd) < targetwidth):
        odd+=0.1

    newwidth = int(width * odd) + 1
    newheight = int(height * odd) + 1

    video_clip = video_clip.resize((newwidth, newheight))

    x = (newwidth - targetwidth)/2
    y = (newheight - targetheight)/2

    video_clip = video_clip.crop(x1=x,y1=y,x2=x+targetwidth,y2=y+targetheight)
    newclip = video_clip

    audio_clip = AudioFileClip(videopath+".mp3")
    audioduration = audio_clip.duration

    while(audioduration > video_clip.duration):
        videos = []
        videos.append(video_clip)
        videos.append(newclip)
        video_clip = concatenate_videoclips(videos)

    video_clip = video_clip.subclip(0,audioduration)
    video_clip = video_clip.set_audio(audio_clip)

    return video_clip


def final_video(title, time, language, multi_speaker):
    """Create a short video using Gemini for script generation"""
    temp_dir = get_temp_dir()
    os.makedirs(temp_dir, exist_ok=True)
    
    print("--------------------------------")
    print(f"{title} in {time} seconds, {language}, multi speaker: {multi_speaker}")
    print("--------------------------------")
    
    # Generate the script using Gemini's structured output
    script_data = generate_short_video_script(title, int(time), language)
    
    if not script_data or not "scenes" in script_data or len(script_data["scenes"]) == 0:
        print("Error: Could not generate a valid script structure")
        return
    
    # Display the generated script data
    print(f"Generated script with {len(script_data['scenes'])} scenes")
    if "title" in script_data:
        print(f"Video title: {script_data['title']}")
    print("--------------------------------")
    
    # Download background music
    song_file = os.path.join(temp_dir, "song.mp3")
    download_file(read_random_line("download_list/background_music.txt"), song_file)
    
    # Process each scene
    videos = []
    i = 0
    
    for scene in script_data["scenes"]:
        video_file = os.path.join(temp_dir, f"{i}.mp4")
        audio_file = os.path.join(temp_dir, f"{i}.mp3")
        
        # Get search terms for video
        if "search_terms" in scene and scene["search_terms"]:
            search_term = scene["search_terms"][0]
        else:
            # Fall back to visual description if no search terms
            search_term = scene["visual_description"] if "visual_description" in scene else title
            
        print(f"Scene {i+1}: {search_term}")
        print(f"Text: {scene.get('text', '')}")
        
        try:
            get_video(search_term, video_file)
            print("Video downloaded")
            
            # Generate speech from the text
            scene_text = scene.get("text", f"Scene {i+1} for {title}")
            generate_voice(translateto(scene_text, get_language_code(language)), 
                          audio_file, get_language_code(language))
            print("Speech generated")
            
            # Pass just the base path without extension to resize_and_text
            video_base_path = os.path.join(temp_dir, str(i))
            videos.append(resize_and_text(video_base_path))
            i+=1
        except Exception as e:
            print(f"Error processing scene {i+1}: {e}")
            # Continue to next scene if one fails

    if not videos:
        print("Error: No valid video segments could be created")
        return
        
    # Combine all videos
    final_video = concatenate_videoclips(videos)
    audio_clip = AudioFileClip(song_file)
    if final_video.duration < audio_clip.duration:
        audio_clip = audio_clip.subclip(0, final_video.duration)

    adjusted_audio_clip = CompositeAudioClip([audio_clip.volumex(0.12),final_video.audio])
    final_video = final_video.set_audio(adjusted_audio_clip)
    
    # Save to a consistent location whether in Colab or local
    output_file = "UnQTube_short.mp4"
    if os.path.exists('/content'):
        output_file = os.path.join('/content', output_file)
    
    final_video.write_videofile(output_file, audio_codec='aac')

    # Clean up
    if os.path.exists("temp.txt"):
        os.remove("temp.txt")
    
    try:
        shutil.rmtree(temp_dir)
        print(f"Directory {temp_dir} deleted successfully.")
    except Exception as e:
        print(f"Error deleting directory {temp_dir}: {e}")
    
    sys.exit()
