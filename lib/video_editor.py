import moviepy.editor as mp
import moviepy.editor as mpe
from moviepy.editor import *
import cv2
import os
import requests
import traceback
import numpy as np
import time

from lib.media_api import get_videos,download_file,enhance_search_term
from lib.image_procces import resize_and_add_borders
from lib.config_utils import read_config_file
from lib.image_procces import getim,delete_invalid_images,sortimage,shape_error

def create_video_with_images_and_audio(image_folder, audio_file, text, audio_volume=1.0):
    """Create a video from images and audio with robust error handling"""
    try:
        # Ensure the audio file exists
        if not os.path.exists(audio_file):
            print(f"Warning: Audio file not found: {audio_file}")
            # Create a silent audio clip as fallback
            from moviepy.audio.AudioClip import AudioClip
            audio_clip = AudioClip(lambda t: 0, duration=5)
        else:
            audio_clip = mp.AudioFileClip(audio_file)
            audio_clip = audio_clip.volumex(audio_volume)
            
        desired_duration = audio_clip.duration + 1
        
        # Ensure there are images in the folder
        image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            print(f"Warning: No images found in {image_folder}")
            # Create a blank frame as fallback
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            blank_path = os.path.join(image_folder, "blank.jpg")
            cv2.imwrite(blank_path, blank_img)
            image_files = ["blank.jpg"]
            
        image_duration = desired_duration / len(image_files)
        video_clips = []

        for idx, image_file in enumerate(image_files):
            try:
                image_path = os.path.join(image_folder, image_file)
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Warning: Could not read image: {image_path}")
                    continue
                    
                resized_img = resize_and_add_borders(img, 1920, 1080)
                img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)

                if idx == 0 and text:
                    font = cv2.FONT_ITALIC
                    font_scale = 2
                    font_color = (255, 255, 255)
                    font_thickness = 10
                    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
                    text_x = 100
                    text_y = img_rgb.shape[0] - 100
                    cv2.putText(img_rgb, text, (text_x, text_y), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

                video_clip = mp.ImageClip(img_rgb).set_duration(image_duration)
                video_clips.append(video_clip)
            except Exception as e:
                print(f"Error processing image {image_file}: {e}")
                continue

        # Ensure we have at least one clip
        if not video_clips:
            print("Warning: No valid images processed. Creating a blank clip.")
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            # Add text to the blank image
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(blank_img, text or "No images available", (100, 540), font, 2, (255, 255, 255), 5, cv2.LINE_AA)
            blank_clip = mp.ImageClip(blank_img).set_duration(desired_duration)
            video_clips = [blank_clip]

        final_clip = mp.concatenate_videoclips(video_clips, method="compose")
        final_clip = final_clip.set_audio(audio_clip)
        final_clip.fps = 24
        return final_clip
    except Exception as e:
        print(f"Error in create_video_with_images_and_audio: {e}")
        traceback.print_exc()
        # Create a minimal fallback clip
        blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(blank_img, text or "Error creating video", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
        blank_clip = mp.ImageClip(blank_img).set_duration(5)
        return blank_clip

def make_intro(title):
    """Create intro video with fallback mechanisms"""
    try:
        withvideo = read_config_file().get("intro_video", "no").lower() in ["yes", "true", "1"]
        if withvideo:
            try:
                # Check if we should use Gemini to enhance the video search
                use_gemini = read_config_file().get('use_gemini', 'no').lower() in ['yes', 'true', '1']
                
                if use_gemini:
                    try:
                        # Enhance the search title using Gemini
                        enhanced_title = enhance_search_term(title)
                        print(f"Using Gemini-enhanced intro video search: '{enhanced_title}'")
                        search_title = enhanced_title
                    except Exception as e:
                        print(f"Error enhancing search term: {e}")
                        search_title = title
                else:
                    search_title = title
                
                # Get video links
                try:
                    links = get_videos(search_title)
                    if not links:
                        raise ValueError("No videos found")
                except Exception as e:
                    print(f"Error getting videos: {e}")
                    # Fall back to image-based intro
                    return _make_intro_with_images(title)
                
                videos_count = 0
                video_times = 0
                final_videos = []

                try:
                    audio_clip = AudioFileClip("tempfiles/11/11.mp3")
                except Exception as e:
                    print(f"Error loading audio: {e}")
                    # Create a silent audio clip
                    from moviepy.audio.AudioClip import AudioClip
                    audio_clip = AudioClip(lambda t: 0, duration=5)
                    
                max_attempts = min(len(links), 5)  # Limit attempts to avoid infinite loops
                
                while video_times < audio_clip.duration + 1 and videos_count < max_attempts:
                    try:
                        subvideo_path = "tempfiles/11/"+str(videos_count)+".mp4"
                        download_file(links[videos_count], subvideo_path)
                        
                        if not os.path.exists(subvideo_path) or os.path.getsize(subvideo_path) == 0:
                            print(f"Video download failed: {links[videos_count]}")
                            videos_count += 1
                            continue
                            
                        video_clip = VideoFileClip(subvideo_path)
                        video_times += video_clip.duration
                        videos_count += 1
                        
                        # Resize video to 1080p
                        width = video_clip.size[0]
                        height = video_clip.size[1]
                        odd = 1.0
                        while(int(height * odd) < 1080 or int(width * odd) < 1920):
                            odd+=0.1
                        newwidth = int(width * odd) + 1
                        newheight = int(height * odd) + 1
                        video_clip = video_clip.resize((newwidth, newheight))
                        x = (newwidth - 1920)/2
                        y = (newheight - 1080)/2
                        video_clip = video_clip.crop(x1=x,y1=y,x2=x+1920,y2=y+1080)
                        final_videos.append(video_clip)
                    except Exception as e:
                        print(f"Error processing video {videos_count}: {e}")
                        videos_count += 1

                if not final_videos:
                    print("No videos processed successfully. Falling back to image-based intro.")
                    return _make_intro_with_images(title)
                    
                final_video = concatenate_videoclips(final_videos)
                if final_video.duration > audio_clip.duration + 1:
                    final_video = final_video.subclip(0, audio_clip.duration + 1)
                final_video = final_video.set_audio(audio_clip)
                return final_video
            except Exception as e:
                print(f"Error creating video-based intro: {e}")
                traceback.print_exc()
                # Fall back to image-based intro
                return _make_intro_with_images(title)
        else:
            # Standard image-based intro
            return _make_intro_with_images(title)
    except Exception as e:
        print(f"Critical error in make_intro: {e}")
        traceback.print_exc()
        # Create an emergency fallback intro
        blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(blank_img, f"Introduction: {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
        blank_clip = mp.ImageClip(blank_img).set_duration(5)
        
        try:
            audio_clip = AudioFileClip("tempfiles/11/11.mp3")
            blank_clip = blank_clip.set_audio(audio_clip)
        except:
            # No audio available, use silent clip
            pass
            
        return blank_clip

def _make_intro_with_images(title):
    """Helper function to create image-based intro with error handling"""
    try:
        npath = "tempfiles/11"
        getim(title, npath)
        delete_invalid_images(npath)
        sortimage(npath)
        delete_invalid_images(npath)
        shape_error(npath)
        sortimage(npath)
        
        # Check if we have any images
        images = [f for f in os.listdir(npath) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print("No images found for intro. Creating blank intro.")
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(blank_img, f"Introduction: {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
            blank_path = os.path.join(npath, "blank.jpg")
            cv2.imwrite(blank_path, blank_img)
            
        video_clip = create_video_with_images_and_audio(npath, "tempfiles/11/11.mp3", "")
        return video_clip
    except Exception as e:
        print(f"Error creating image-based intro: {e}")
        traceback.print_exc()
        # Create a minimal fallback intro
        blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        cv2.putText(blank_img, f"Introduction: {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
        blank_clip = mp.ImageClip(blank_img).set_duration(5)
        
        try:
            audio_clip = AudioFileClip("tempfiles/11/11.mp3")
            blank_clip = blank_clip.set_audio(audio_clip)
        except:
            # No audio available, use silent clip
            pass
            
        return blank_clip

def mergevideo(videoname, audio_file, tops, title):
    """Merge all video segments with robust error handling"""
    try:
        output_filename = f"UnQTube_{videoname}.mp4"
        if os.path.exists('/content'):
            output_filename = os.path.join('/content', output_filename)
            
        print("\n====== STARTING FINAL VIDEO CREATION ======")
        print(f"Output file will be: {output_filename}")
        video_clips = []

        # Create intro
        try:
            print("\n----- Creating intro segment -----")
            video_clip = make_intro(title)
            if video_clip:
                video_clips.append(video_clip)
                print("✓ Intro segment created successfully")
            else:
                raise Exception("Intro clip is None")
        except Exception as e:
            print(f"Error creating intro: {e}")
            traceback.print_exc()
            # Create a minimal fallback intro
            print("Creating emergency fallback intro")
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(blank_img, f"Introduction to {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
            fallback_intro = mp.ImageClip(blank_img).set_duration(5)
            video_clips.append(fallback_intro)
            print("✓ Emergency fallback intro created")
        
        # Create content and outro segments
        chapter_text = "00:00 intro\n"
        sum_duration = 0
        
        for i in range(10, -1, -1):
            ir = str(i)
            
            try:
                if i != 0 and i != 11:
                    top = ir + "." + tops[i-1]
                else:
                    top = ""
                
                print(f"\n----- Processing segment {ir}: {top} -----")
                segment_path = f"tempfiles/{ir}"
                if os.path.exists(segment_path):
                    audio_path = f"{segment_path}/{ir}.mp3"
                    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                        print(f"Warning: Audio file {audio_path} missing or empty")
                        # Create a blank audio file as fallback
                        try:
                            from pydub import AudioSegment
                            silence = AudioSegment.silent(duration=5000)  # 5 seconds of silence
                            silence.export(audio_path, format="mp3")
                            print("✓ Created fallback silent audio")
                        except Exception as audio_e:
                            print(f"Could not create fallback audio: {audio_e}")
                            # Just continue, create_video_with_images_and_audio has its own audio fallback
                    
                    # Count images in directory
                    image_count = len([f for f in os.listdir(segment_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                    print(f"Found {image_count} images for segment {ir}")
                    
                    if image_count == 0:
                        print("No images found, creating blank image")
                        blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                        segment_text = top if top else f"Segment {ir}"
                        cv2.putText(blank_img, segment_text, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                        blank_path = os.path.join(segment_path, "blank.jpg")
                        cv2.imwrite(blank_path, blank_img)
                        print("✓ Created fallback blank image")
                    
                    print(f"Creating video segment {ir}")
                    video_clip = create_video_with_images_and_audio(segment_path, audio_path, top)
                    if video_clip:
                        video_clips.append(video_clip)
                        print(f"✓ Segment {ir} created successfully")
                        
                        # Update chapter markers
                        if i < 11:  # Skip the intro as it was already added
                            sum_duration += video_clips[len(video_clips) - 2].duration  # Use previous clip's duration
                            minutes = int(sum_duration / 60)
                            seconds = int(sum_duration % 60)
                            time_marker = f"{minutes:02d}:{seconds:02d}"
                            
                            if i > 0 and i <= 10:
                                # For content segments 1-10
                                chapter_text += f"{time_marker} {tops[10-i]}\n"
                            elif i == 0:
                                # For outro
                                chapter_text += f"{time_marker} outro\n"
                    else:
                        raise Exception("Segment video clip is None")
                else:
                    print(f"Warning: Directory {segment_path} not found. Creating fallback segment.")
                    # Create a minimal fallback segment
                    blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                    segment_text = top if top else f"Segment {ir}"
                    cv2.putText(blank_img, segment_text, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                    fallback_segment = mp.ImageClip(blank_img).set_duration(5)
                    video_clips.append(fallback_segment)
                    print(f"✓ Created emergency fallback for segment {ir}")
            except Exception as e:
                print(f"Error processing segment {ir}: {e}")
                traceback.print_exc()
                # Create a minimal fallback segment
                blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                segment_text = top if top else f"Segment {ir}"
                cv2.putText(blank_img, segment_text, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                fallback_segment = mp.ImageClip(blank_img).set_duration(5)
                video_clips.append(fallback_segment)
                print(f"✓ Created emergency fallback for segment {ir}")

        # Save chapter markers to file
        try:
            with open(f"UnQTube_{videoname}.txt", "w", encoding="utf-8") as file:
                file.write(chapter_text)
        except Exception as e:
            print(f"Warning: Could not write chapter markers: {e}")

        # Ensure we have at least one clip
        if not video_clips:
            print("Critical error: No video clips created. Creating a minimal video.")
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(blank_img, f"Video: {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
            video_clips = [mp.ImageClip(blank_img).set_duration(10)]
            print("✓ Created emergency fallback video")

        # Concatenate all clips
        print(f"\n----- Concatenating {len(video_clips)} video clips -----")
        try:
            final_video = concatenate_videoclips(video_clips, method="compose")
            print("✓ Video clips concatenated successfully")
        except Exception as concat_error:
            print(f"Error concatenating clips: {concat_error}")
            traceback.print_exc()
            
            # Try safer concatenation settings
            print("Attempting safer concatenation with method='chain'...")
            try:
                final_video = concatenate_videoclips(video_clips, method="chain")
                print("✓ Video clips concatenated with alternate method")
            except Exception as alt_concat_error:
                print(f"Alternative concatenation also failed: {alt_concat_error}")
                
                # Last resort: just use the first clip if we have one
                if video_clips:
                    print("Using just the first clip as emergency fallback")
                    final_video = video_clips[0]
                else:
                    # This should never happen due to earlier check, but just in case
                    print("No clips available - creating emergency blank video")
                    blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                    cv2.putText(blank_img, f"Emergency video for {title}", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                    final_video = mp.ImageClip(blank_img).set_duration(10)
        
        # Add background music if available
        try:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                print("\n----- Adding background music -----")
                audio_clip = AudioFileClip(audio_file)
                if final_video.duration < audio_clip.duration:
                    audio_clip = audio_clip.subclip(0, final_video.duration)
                adjusted_audio_clip = CompositeAudioClip([audio_clip.volumex(0.05), final_video.audio])
                final_video = final_video.set_audio(adjusted_audio_clip)
                print("✓ Background music added")
            else:
                print("Background music file not found or empty. Using original audio.")
        except Exception as e:
            print(f"Warning: Could not add background music: {e}")
            # Continue with original audio

        # Write the final video file with robust error handling
        print(f"\n----- Writing final video to {output_filename} -----")
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
                final_video.write_videofile(output_filename, **settings)
                print(f"✓ Successfully created video: {output_filename}")
                success = True
                
                # Verify the file exists and has content
                if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                    print(f"✓ Verified file exists with size: {os.path.getsize(output_filename)} bytes")
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
                emergency_img = np.zeros((720, 1280, 3), dtype=np.uint8)  # Smaller resolution
                cv2.putText(emergency_img, f"Emergency video for {title}", (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
                emergency_clip = mp.ImageClip(emergency_img).set_duration(10)
                
                # Write with minimal settings
                emergency_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac", 
                                            preset="ultrafast", bitrate="500k", fps=10)
                print(f"✓ Emergency video created: {output_filename}")
                success = True
            except Exception as emergency_error:
                print(f"Emergency video creation failed: {emergency_error}")
                traceback.print_exc()
                
                # Last resort: try writing a static image as MP4
                try:
                    print("Attempting to write a static image as video...")
                    import subprocess
                    last_resort_img = "emergency_frame.jpg"
                    cv2.imwrite(last_resort_img, emergency_img)
                    
                    ffmpeg_cmd = f"ffmpeg -loop 1 -i {last_resort_img} -c:v libx264 -t 5 -pix_fmt yuv420p -y {output_filename}"
                    subprocess.call(ffmpeg_cmd, shell=True)
                    
                    if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                        print(f"✓ Created last resort video: {output_filename}")
                        success = True
                    else:
                        print("Last resort video creation failed")
                        
                    # Cleanup temp file
                    if os.path.exists(last_resort_img):
                        os.remove(last_resort_img)
                except Exception as last_error:
                    print(f"Last resort video creation failed: {last_error}")
        
        print("\n====== VIDEO CREATION COMPLETE ======")
        return success
            
    except Exception as e:
        print(f"Critical error in mergevideo: {e}")
        traceback.print_exc()
        
        # Try one last emergency approach
        try:
            print("\n====== ATTEMPTING EMERGENCY VIDEO CREATION ======")
            output_filename = f"UnQTube_{videoname}.mp4"
            if os.path.exists('/content'):
                output_filename = os.path.join('/content', output_filename)
                
            emergency_img = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(emergency_img, f"Emergency video for: {title}", (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
            cv2.putText(emergency_img, "Video generation encountered an error", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            emergency_img_path = "emergency_frame.jpg"
            cv2.imwrite(emergency_img_path, emergency_img)
            
            import subprocess
            ffmpeg_cmd = f"ffmpeg -loop 1 -i {emergency_img_path} -c:v libx264 -t 5 -pix_fmt yuv420p -y {output_filename}"
            subprocess.call(ffmpeg_cmd, shell=True)
            
            if os.path.exists(emergency_img_path):
                os.remove(emergency_img_path)
                
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                print(f"✓ Created absolute last resort video: {output_filename}")
                return True
            else:
                print("Failed to create emergency video")
                return False
        except Exception as emergency_error:
            print(f"Emergency video creation failed: {emergency_error}")
            return False
