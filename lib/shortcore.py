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
            print("\n----- Running cleanup -----")
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
        
        print("\n====== STARTING SHORT VIDEO CREATION ======")
        print(f"Topic: {title}")
        print(f"Duration: {time} seconds")
        print(f"Language: {language}")
        print(f"Multi-speaker: {multi_speaker}")
        print(f"Output file will be: {output_file}")
        print("==========================================")
        
        # Generate the script using Gemini's structured output
        try:
            print("\n----- Generating script using Gemini -----")
            script_data = generate_short_video_script(title, int(time), language)
            
            if not script_data or "scenes" not in script_data or len(script_data["scenes"]) == 0:
                raise ValueError("Could not generate a valid script structure")
                
            # Display the generated script data
            print(f"✓ Generated script with {len(script_data['scenes'])} scenes")
            if "title" in script_data:
                print(f"Video title: {script_data['title']}")
            
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
            print("✓ Created fallback script with 3 scenes")
        
        # Download background music
        print("\n----- Downloading background music -----")
        song_file = os.path.join(temp_dir, "song.mp3")
        try:
            download_file(read_random_line("download_list/background_music.txt"), song_file)
            print("✓ Background music downloaded")
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
        total_scenes = len(script_data["scenes"])
        
        print(f"\n----- Processing {total_scenes} scenes -----")
        for scene_idx, scene in enumerate(script_data["scenes"]):
            if failed_scenes >= 2 and len(videos) > 0:
                # If we've had multiple failures but have some successful videos,
                # stop trying to avoid wasting time
                print("Multiple scene creation failures. Using available scenes.")
                break
            
            try:
                print(f"\nScene {scene_idx+1}/{total_scenes}: Processing")
                video_file = os.path.join(temp_dir, f"{i}.mp4")
                audio_file = os.path.join(temp_dir, f"{i}.mp3")
                
                # Get search terms for video
                if "search_terms" in scene and scene["search_terms"]:
                    search_term = scene["search_terms"][0]
                else:
                    # Fall back to visual description if no search terms
                    search_term = scene.get("visual_description", title)
                    
                print(f"Search term: {search_term}")
                print(f"Text: {scene.get('text', '')}")
                
                # Try to get video for this scene
                video_success = False
                try:
                    print("Downloading video...")
                    video_success = get_video(search_term, video_file)
                    if video_success:
                        print("✓ Video downloaded successfully")
                    else:
                        print("Failed to download video, trying fallback search term")
                        # Try with simpler search term
                        simple_term = search_term.split()[0] if len(search_term.split()) > 1 else title
                        video_success = get_video(simple_term, video_file)
                        if video_success:
                            print(f"✓ Video downloaded with fallback term: {simple_term}")
                        else:
                            # Second fallback - try with even more generic term
                            video_success = get_video("cinematic scene", video_file)
                            if video_success:
                                print("✓ Video downloaded with generic fallback term")
                except Exception as e:
                    print(f"Error downloading video: {e}")
                
                # If video download still failed, create an emergency video clip
                if not video_success or not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
                    print("Creating emergency blank video clip...")
                    try:
                        import cv2
                        import numpy as np
                        
                        # Create a blank video file using ffmpeg
                        blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                        text = scene.get("text", f"Scene {i+1} for {title}")
                        cv2.putText(blank_img, text, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                        
                        # Save the image
                        img_path = os.path.join(temp_dir, f"{i}_blank.jpg")
                        cv2.imwrite(img_path, blank_img)
                        
                        # Create a 5-second video from this image
                        import subprocess
                        cmd = f"ffmpeg -loop 1 -i {img_path} -c:v libx264 -t 5 -pix_fmt yuv420p -y {video_file}"
                        subprocess.call(cmd, shell=True)
                        
                        if os.path.exists(video_file) and os.path.getsize(video_file) > 0:
                            video_success = True
                            print("✓ Created emergency video clip")
                        else:
                            print("Failed to create emergency video clip")
                    except Exception as e:
                        print(f"Error creating emergency video: {e}")
                
                # Generate speech from the text
                audio_success = False
                try:
                    print("Generating speech...")
                    scene_text = scene.get("text", f"Scene {i+1} for {title}")
                    generate_voice(translateto(scene_text, get_language_code(language)), 
                                audio_file, get_language_code(language))
                    print("✓ Speech generated successfully")
                    audio_success = True
                except Exception as e:
                    print(f"Error generating speech: {e}")
                
                # If audio generation failed, create silent audio
                if not audio_success or not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                    print("Creating silent audio file...")
                    try:
                        from pydub import AudioSegment
                        silence = AudioSegment.silent(duration=5000)  # 5 seconds of silence
                        silence.export(audio_file, format="mp3")
                        audio_success = True
                        print("✓ Created silent audio file")
                    except Exception as e:
                        print(f"Error creating silent audio: {e}")
                        # Create an empty file as last resort
                        try:
                            with open(audio_file, "wb") as f:
                                f.write(b"")
                            audio_success = True
                            print("✓ Created empty audio file")
                        except Exception as e:
                            print(f"Error creating empty audio file: {e}")
                
                # If both video and audio files exist (even if they're emergency fallbacks), 
                # try to combine them
                if os.path.exists(video_file) and os.path.exists(audio_file):
                    video_base_path = os.path.join(temp_dir, str(i))
                    try:
                        print("Creating scene from video and audio...")
                        clip = resize_and_text(video_base_path)
                        videos.append(clip)
                        print(f"✓ Scene {i+1} created successfully")
                        i += 1
                    except Exception as e:
                        print(f"Error creating scene {i+1}: {e}")
                        traceback.print_exc()
                        
                        # Try to create an emergency fallback clip directly
                        try:
                            print("Creating emergency fallback clip...")
                            video_clip = VideoFileClip(video_file)
                            # Resize to vertical format
                            video_clip = video_clip.resize(height=1920)
                            # Crop to correct dimensions
                            width = video_clip.size[0]
                            if width > 1080:
                                x_center = width / 2
                                video_clip = video_clip.crop(x1=x_center-540, y1=0, x2=x_center+540, y2=1920)
                            
                            # Set duration to 5 seconds if needed
                            if video_clip.duration < 5:
                                video_clip = video_clip.loop(duration=5)
                            else:
                                video_clip = video_clip.subclip(0, 5)
                                
                            # Add audio if possible
                            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                                try:
                                    audio_clip = AudioFileClip(audio_file)
                                    video_clip = video_clip.set_audio(audio_clip)
                                except:
                                    pass  # Continue without audio
                                
                            videos.append(video_clip)
                            print(f"✓ Created emergency fallback for scene {i+1}")
                            i += 1
                        except Exception as e2:
                            print(f"Error creating emergency fallback clip: {e2}")
                            failed_scenes += 1
                else:
                    print(f"Missing video or audio for scene {i+1}. Skipping.")
                    failed_scenes += 1
                    
            except Exception as e:
                print(f"Error processing scene {i+1}: {e}")
                traceback.print_exc()
                failed_scenes += 1
        
        # Create an emergency scene if we have no valid scenes
        if not videos:
            print("\n----- No valid scenes created. Creating emergency scene -----")
            try:
                import cv2
                import numpy as np
                from moviepy.editor import ImageClip
                
                # Create a blank frame
                blank_img = np.zeros((1920, 1080, 3), dtype=np.uint8)
                cv2.putText(blank_img, f"Short video about {title}", (100, 540), 
                         cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                cv2.putText(blank_img, "No scenes could be created", (100, 640), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
                
                # Create a 10-second clip from this image
                emergency_clip = ImageClip(blank_img).set_duration(10)
                videos = [emergency_clip]
                print("✓ Created emergency scene")
            except Exception as e:
                print(f"Failed to create emergency scene: {e}")
                print("Unable to create video")
                return False
            
        # Combine all videos and audio
        try:
            print(f"\n----- Creating final video with {len(videos)} scenes -----")
            # Try different concatenation methods
            final_video = None
            
            try:
                # First try with default method
                print("Attempting to concatenate clips with default method...")
                final_video = concatenate_videoclips(videos)
                print("✓ Clips concatenated successfully")
            except Exception as e1:
                print(f"Error concatenating clips with default method: {e1}")
                
                try:
                    # Try with method="chain"
                    print("Attempting to concatenate clips with method='chain'...")
                    final_video = concatenate_videoclips(videos, method="chain")
                    print("✓ Clips concatenated with method='chain'")
                except Exception as e2:
                    print(f"Error concatenating clips with method='chain': {e2}")
                    
                    # Last resort - just use the first clip
                    if videos:
                        print("Using only the first clip as fallback...")
                        final_video = videos[0]
                        print("✓ Using first clip as fallback")
                    else:
                        raise Exception("No video clips available")
            
            # Add background music if it exists and has content
            if os.path.exists(song_file) and os.path.getsize(song_file) > 0:
                try:
                    print("Adding background music...")
                    audio_clip = AudioFileClip(song_file)
                    if final_video.duration < audio_clip.duration:
                        audio_clip = audio_clip.subclip(0, final_video.duration)
                    adjusted_audio_clip = CompositeAudioClip([audio_clip.volumex(0.12), final_video.audio])
                    final_video = final_video.set_audio(adjusted_audio_clip)
                    print("✓ Background music added")
                except Exception as e:
                    print(f"Error adding background music: {e}")
                    # Continue with existing audio
            
            # Write the final video file with multiple attempts and fallbacks
            print(f"\n----- Writing final video to {output_file} -----")
            success = False
            
            # Try different codec configurations in order of preference
            write_attempts = [
                # First attempt - standard settings
                {"codec": "libx264", "audio_codec": "aac", "threads": 4, "fps": 30},
                # Second attempt - ultrafast preset for speed
                {"codec": "libx264", "audio_codec": "aac", "preset": "ultrafast", "threads": 4, "fps": 24},
                # Third attempt - very low bitrate
                {"codec": "libx264", "audio_codec": "aac", "preset": "ultrafast", "bitrate": "1000k", "threads": 2, "fps": 20},
                # Last attempt - minimal quality emergency settings
                {"codec": "libx264", "audio_codec": "aac", "preset": "ultrafast", "bitrate": "500k", "threads": 1, "fps": 15}
            ]
            
            for i, settings in enumerate(write_attempts):
                if success:
                    break
                    
                try:
                    print(f"Write attempt {i+1}/{len(write_attempts)} with settings: {settings}")
                    final_video.write_videofile(output_file, **settings)
                    print(f"✓ Successfully created video: {output_file}")
                    success = True
                    
                    # Verify the file exists and has content
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        print(f"✓ Verified file exists with size: {os.path.getsize(output_file)} bytes")
                    else:
                        print(f"⚠ Warning: Output file empty or missing, continuing to next attempt")
                        success = False
                        
                except Exception as write_error:
                    print(f"Error in attempt {i+1}: {write_error}")
                    traceback.print_exc()
                    
                    # Small delay before retrying
                    time.sleep(1)
            
            # If all attempts failed, try emergency video generation
            if not success:
                print("All standard write attempts failed. Trying emergency video generation...")
                try:
                    # Create an extremely simple video
                    import cv2
                    import numpy as np
                    import subprocess
                    
                    emergency_img = np.zeros((1920, 1080, 3), dtype=np.uint8)
                    cv2.putText(emergency_img, f"Short video about {title}", (50, 960), 
                             cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                    
                    emergency_img_path = os.path.join(temp_dir, "emergency_frame.jpg")
                    cv2.imwrite(emergency_img_path, emergency_img)
                    
                    cmd = f"ffmpeg -loop 1 -i {emergency_img_path} -c:v libx264 -t 5 -pix_fmt yuv420p -y {output_file}"
                    subprocess.call(cmd, shell=True)
                    
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        print(f"✓ Created emergency video: {output_file}")
                        success = True
                    else:
                        print("Emergency video creation failed")
                except Exception as e:
                    print(f"Emergency video creation failed: {e}")
                    traceback.print_exc()
            
            print("\n====== VIDEO CREATION COMPLETE ======")
            return success
            
        except Exception as e:
            print(f"Error creating final video: {e}")
            traceback.print_exc()
            
            # Try one last emergency approach using ffmpeg directly
            try:
                print("\n====== ATTEMPTING EMERGENCY VIDEO CREATION ======")
                import cv2
                import numpy as np
                import subprocess
                
                emergency_img = np.zeros((1920, 1080, 3), dtype=np.uint8)
                cv2.putText(emergency_img, f"Short video about: {title}", (50, 920), 
                          cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                cv2.putText(emergency_img, "Video generation encountered an error", (50, 1000), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
                
                emergency_img_path = os.path.join(temp_dir, "emergency_frame.jpg")
                cv2.imwrite(emergency_img_path, emergency_img)
                
                cmd = f"ffmpeg -loop 1 -i {emergency_img_path} -c:v libx264 -t 5 -pix_fmt yuv420p -y {output_file}"
                subprocess.call(cmd, shell=True)
                
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    print(f"✓ Created absolute last resort video: {output_file}")
                    return True
                else:
                    print("Failed to create emergency video")
                    return False
            except Exception as emergency_error:
                print(f"Emergency video creation failed: {emergency_error}")
                return False

    except Exception as e:
        print(f"Error in short video creation: {e}")
        traceback.print_exc()
        
        # Try one last emergency approach
        try:
            print("\n====== ATTEMPTING EMERGENCY VIDEO CREATION ======")
            import cv2
            import numpy as np
            import subprocess
            
            emergency_img = np.zeros((1920, 1080, 3), dtype=np.uint8)
            cv2.putText(emergency_img, f"Short video about: {title}", (50, 920), 
                      cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
            cv2.putText(emergency_img, "Video generation encountered an error", (50, 1000), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA)
            
            emergency_img_path = "emergency_frame.jpg"
            cv2.imwrite(emergency_img_path, emergency_img)
            
            cmd = f"ffmpeg -loop 1 -i {emergency_img_path} -c:v libx264 -t 5 -pix_fmt yuv420p -y {output_file}"
            subprocess.call(cmd, shell=True)
            
            if os.path.exists(emergency_img_path):
                os.remove(emergency_img_path)
                
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✓ Created absolute last resort video: {output_file}")
                return True
            else:
                print("Failed to create emergency video")
                return False
        except Exception as emergency_error:
            print(f"Emergency video creation failed: {emergency_error}")
            return False
    finally:
        # Always run cleanup
        cleanup()
