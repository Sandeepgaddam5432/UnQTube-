import os
import shutil
import sys
import re
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

from lib.video_texts import getyamll, read_random_line
from lib.config_utils import read_config_file
from lib.APIss import download_file, chatgpt, translateto, enhance_search_term
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.core import get_temp_dir

def get_video(prompt,videoname):
    # Check if we should use Gemini to enhance the video search
    use_gemini = read_config_file().get('use_gemini', 'no').lower() in ['yes', 'true', '1']
    
    if use_gemini:
        # Enhance the search prompt using Gemini
        enhanced_prompt = enhance_search_term(prompt)
        print(f"Using Gemini-enhanced video search: '{enhanced_prompt}'")
        search_prompt = enhanced_prompt
    else:
        search_prompt = prompt
    
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": read_config_file()["pexels_api"]
    }
    params = {
        "query": search_prompt,
        "per_page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()


    link = json_data['videos'][0]['video_files'][0]['link']

    download_file(link,videoname)


def resize_and_text(videopath,targetwidth=1080,targetheight=1920):
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


def final_video(title,time,language,multi_speaker):
    temp_dir = get_temp_dir()
    os.makedirs(temp_dir, exist_ok=True)
    
    print("--------------------------------")
    print(title + " in " + time + " second"+", "+language+", multi speaker : "+multi_speaker)
    print("--------------------------------")
    original_text = chatgpt(getyamll("short_prompt")).format(title=title,time=time)
    print(original_text)
    print("--------------------------------")
    
    # Use absolute paths for temp directory
    song_file = os.path.join(temp_dir, "song.mp3")
    download_file(read_random_line("download_list/background_music.txt"), song_file)
    
    videoprompts = re.findall(r'\[([^\]]+)\]', original_text)
    if "Text" in original_text:
        texts = re.findall(r'Text:\s+"([^"]+)"', original_text)
    else:
        texts = re.findall(r'text:\s+"([^"]+)"', original_text)
    print(videoprompts)
    print(texts)
    print("--------------------------------")
    
    videos = []
    i = 0
    
    for text,prompt in zip(texts,videoprompts):
        video_file = os.path.join(temp_dir, f"{i}.mp4")
        audio_file = os.path.join(temp_dir, f"{i}.mp3")
        
        get_video(prompt, video_file)
        print("video download")
        
        generate_voice(translateto(text,get_language_code(language)), audio_file, get_language_code(language))
        print("speech make")
        
        # Pass just the base path without extension to resize_and_text
        video_base_path = os.path.join(temp_dir, str(i))
        videos.append(resize_and_text(video_base_path))
        i+=1

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
