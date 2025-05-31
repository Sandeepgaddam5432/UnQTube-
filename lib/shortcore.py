import os
import shutil
import sys
import re
import requests
import traceback
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

from lib.video_texts import getyamll, read_random_line
from lib.config_utils import read_config_file
from lib.media_api import download_file, translateto
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.core import get_temp_dir
from lib.gemini_api import generate_short_video_script

def get_video(prompt, videoname, max_retries=3):
    """Download stock video based on search prompt"""
    for attempt in range(max_retries):
        try:
            url = "https://api.pexels.com/videos/search"
            
            try:
                api_key = read_config_file()["pexels_api"]
                if not api_key or api_key == "pexels_api":
                    print("Warning: Invalid Pexels API key in config. Video downloads may fail.")
            except Exception as e:
                print(f"Error reading Pexels API key: {e}")
                api_key = "pexels_api"  # Default placeholder that will fail
                
            headers = {
                "Authorization": api_key
            }
            params = {
                "query": prompt,
                "per_page": 1
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                if attempt < max_retries - 1:
                    print(f"Pexels API error: {response.status_code}. Retrying ({attempt+1}/{max_retries})...")
                    continue
                else:
                    print(f"Pexels API error: {response.status_code} - {response.text}")
                    raise Exception(f"Pexels API returned status code {response.status_code}")
                
            json_data = response.json()

            try:
                link = json_data['videos'][0]['video_files'][0]['link']
                download_file(link, videoname)
                return True  # Success
            except (KeyError, IndexError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"Error extracting video link: {e}. Retrying with broader search...")
                    # Try a more generic search term on retry
                    terms = prompt.split()
                    if len(terms) > 2:
                        prompt = " ".join(terms[:2])  # Use just the first two words
                    continue
                else:
                    print(f"Error getting video for '{prompt}': {e}")
                    raise Exception(f"Unable to find a suitable video for '{prompt}'")
                
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Network error: {e}. Retrying ({attempt+1}/{max_retries})...")
                continue
            else:
                print(f"Network error downloading video: {e}")
                raise Exception(f"Network error: {e}")
                
    return False  # If we get here, all retries failed


def resize_and_text(videopath, targetwidth=1080, targetheight=1920):
    try:
        # Check if the video and audio files exist
        video_file = f"{videopath}.mp4"
        audio_file = f"{videopath}.mp3"
        
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file not found: {video_file}")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
        # Load video and resize it
        video_clip = VideoFileClip(video_file)
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

        # Load audio and adjust video length if needed
        audio_clip = AudioFileClip(audio_file)
        audioduration = audio_clip.duration

        # If audio is longer than video, loop the video
        while(audioduration > video_clip.duration):
            videos = []
            videos.append(video_clip)
            videos.append(newclip)
            video_clip = concatenate_videoclips(videos)

        # Trim video to match audio length and set audio
        video_clip = video_clip.subclip(0,audioduration)
        video_clip = video_clip.set_audio(audio_clip)

        return video_clip
        
    except Exception as e:
        print(f"Error processing video {videopath}: {e}")
        raise  # Re-raise as this is critical for the video creation


def final_video(title, time, language, multi_speaker):
    """Create a short video using Gemini for script generation"""
    temp_dir = get_temp_dir()
    output_file = "UnQTube_short.mp4"
    if os.path.exists('/content'):
        output_file = os.path.join('/content', output_file)
        
    # Define cleanup function for finally block
    def cleanup():
        try:
            print("Running cleanup...")
            if os.path.exists("temp.txt"):
                os.remove("temp.txt")
                
            try:
                shutil.rmtree(temp_dir)
                print(f"Directory {temp_dir} deleted successfully.")
            except Exception as e:
                print(f"Error deleting directory {temp_dir}: {e}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    try:
        os.makedirs(temp_dir, exist_ok=True)
        
        print("--------------------------------")
        print(f"{title} in {time} seconds, {language}, multi speaker: {multi_speaker}")
        print("--------------------------------")
        
        # Generate the script using Gemini's structured output
        try:
            script_data = generate_short_video_script(title, int(time), language)
            
            if not script_data or "scenes" not in script_data or len(script_data["scenes"]) == 0:
                raise ValueError("Could not generate a valid script structure")
                
            # Display the generated script data
            print(f"Generated script with {len(script_data['scenes'])} scenes")
            if "title" in script_data:
                print(f"Video title: {script_data['title']}")
            print("--------------------------------")
            
        except Exception as e:
            print(f"Error generating short video script: {e}")
            print("Creating fallback script...")
            
            # Create a simple fallback script
            script_data = {
                "title": f"Short video about {title}",
                "scenes": [
                    {
                        "visual_description": "Opening shot",
                        "text": f"Welcome to this short video about {title}",
                        "search_terms": [f"{title} overview", "introduction scene"]
                    },
                    {
                        "visual_description": "Main content",
                        "text": f"Here's what you need to know about {title}",
                        "search_terms": [f"{title} closeup", "detailed view"]
                    },
                    {
                        "visual_description": "Conclusion",
                        "text": "Thanks for watching! Like and subscribe!",
                        "search_terms": ["thank you scene", "conclusion shot"]
                    }
                ]
            }
        
        # Download background music
        song_file = os.path.join(temp_dir, "song.mp3")
        try:
            download_file(read_random_line("download_list/background_music.txt"), song_file)
            print("Background music downloaded")
        except Exception as e:
            print(f"Error downloading background music: {e}")
            # Create empty file as fallback
            try:
                with open(song_file, "wb") as f:
                    f.write(b"")
                print("Created empty music file as fallback")
            except Exception as music_err:
                print(f"Error creating empty music file: {music_err}")
        
        # Process each scene
        videos = []
        i = 0
        failed_scenes = 0
        
        for scene in script_data["scenes"]:
            if failed_scenes >= 2 and len(videos) > 0:
                # If we've had multiple failures but have some successful videos,
                # stop trying to avoid wasting time
                print("Multiple scene creation failures. Using available scenes.")
                break
            
            try:
                video_file = os.path.join(temp_dir, f"{i}.mp4")
                audio_file = os.path.join(temp_dir, f"{i}.mp3")
                
                # Get search terms for video
                if "search_terms" in scene and scene["search_terms"]:
                    search_term = scene["search_terms"][0]
                else:
                    # Fall back to visual description if no search terms
                    search_term = scene.get("visual_description", title)
                    
                print(f"Scene {i+1}: {search_term}")
                print(f"Text: {scene.get('text', '')}")
                
                # Try to get video for this scene
                video_success = False
                try:
                    video_success = get_video(search_term, video_file)
                    if video_success:
                        print("Video downloaded")
                    else:
                        print("Failed to download video, trying fallback search term")
                        # Try with simpler search term
                        simple_term = search_term.split()[0] if len(search_term.split()) > 1 else title
                        video_success = get_video(simple_term, video_file)
                        if video_success:
                            print(f"Video downloaded with fallback term: {simple_term}")
                except Exception as e:
                    print(f"Error downloading video: {e}")
                
                # Generate speech from the text
                audio_success = False
                try:
                    scene_text = scene.get("text", f"Scene {i+1} for {title}")
                    generate_voice(translateto(scene_text, get_language_code(language)), 
                                audio_file, get_language_code(language))
                    print("Speech generated")
                    audio_success = True
                except Exception as e:
                    print(f"Error generating speech: {e}")
                
                # If both video and audio were created successfully, combine them
                if video_success and audio_success and os.path.exists(video_file) and os.path.exists(audio_file):
                    video_base_path = os.path.join(temp_dir, str(i))
                    try:
                        clip = resize_and_text(video_base_path)
                        videos.append(clip)
                        print(f"Scene {i+1} created successfully")
                        i += 1
                    except Exception as e:
                        print(f"Error creating scene {i+1}: {e}")
                        failed_scenes += 1
                else:
                    print(f"Missing video or audio for scene {i+1}. Skipping.")
                    failed_scenes += 1
                    
            except Exception as e:
                print(f"Error processing scene {i+1}: {e}")
                failed_scenes += 1
        
        if not videos:
            print("Error: No valid video segments could be created")
            print("Unable to create video")
            return False
            
        # Combine all videos and audio
        try:
            print(f"Creating final video with {len(videos)} scenes...")
            final_video = concatenate_videoclips(videos)
            
            # Add background music if it exists and has content
            if os.path.exists(song_file) and os.path.getsize(song_file) > 0:
                try:
                    audio_clip = AudioFileClip(song_file)
                    if final_video.duration < audio_clip.duration:
                        audio_clip = audio_clip.subclip(0, final_video.duration)
                    adjusted_audio_clip = CompositeAudioClip([audio_clip.volumex(0.12), final_video.audio])
                    final_video = final_video.set_audio(adjusted_audio_clip)
                except Exception as e:
                    print(f"Error adding background music: {e}")
                    # Continue with existing audio
            
            # Write the final video file
            final_video.write_videofile(output_file, audio_codec='aac')
            print(f"Video successfully saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error creating final video: {e}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"Error in short video creation: {e}")
        traceback.print_exc()
        return False
    finally:
        # Always run cleanup
        cleanup()
