import moviepy.editor as mp
import moviepy.editor as mpe
from moviepy.editor import *
import cv2
import os
import requests
import traceback
import numpy as np

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
        print("Starting final video creation...")
        video_clips = []

        # Create intro
        try:
            print("Creating intro segment...")
            video_clip = make_intro(title)
            video_clips.append(video_clip)
        except Exception as e:
            print(f"Error creating intro: {e}")
            traceback.print_exc()
            # Create a minimal fallback intro
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(blank_img, "Introduction", (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
            fallback_intro = mp.ImageClip(blank_img).set_duration(5)
            video_clips.append(fallback_intro)
        
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
                
                print(f"Processing segment {ir}: {top}")
                if os.path.exists(f"tempfiles/{ir}"):
                    video_clip = create_video_with_images_and_audio(f"tempfiles/{ir}", f"tempfiles/{ir}/{ir}.mp3", top)
                    video_clips.append(video_clip)
                    
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
                    print(f"Warning: Directory tempfiles/{ir} not found. Skipping segment.")
            except Exception as e:
                print(f"Error processing segment {ir}: {e}")
                traceback.print_exc()
                # Create a minimal fallback segment
                blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
                segment_text = top if top else f"Segment {ir}"
                cv2.putText(blank_img, segment_text, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)
                fallback_segment = mp.ImageClip(blank_img).set_duration(5)
                video_clips.append(fallback_segment)

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

        # Concatenate all clips
        print(f"Concatenating {len(video_clips)} video clips...")
        final_video = concatenate_videoclips(video_clips)
        
        # Add background music if available
        try:
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                print("Adding background music...")
                audio_clip = AudioFileClip(audio_file)
                if final_video.duration < audio_clip.duration:
                    audio_clip = audio_clip.subclip(0, final_video.duration)
                adjusted_audio_clip = CompositeAudioClip([audio_clip.volumex(0.05), final_video.audio])
                final_video = final_video.set_audio(adjusted_audio_clip)
            else:
                print("Background music file not found or empty. Using original audio.")
        except Exception as e:
            print(f"Warning: Could not add background music: {e}")
            # Continue with original audio

        # Write the final video file with robust error handling
        output_filename = f"UnQTube_{videoname}.mp4"
        print(f"Writing final video to {output_filename}...")
        try:
            final_video.write_videofile(output_filename, audio_codec='aac', threads=4)
            print(f"Successfully created video: {output_filename}")
        except Exception as write_error:
            print(f"Error writing video file: {write_error}")
            traceback.print_exc()
            
            # Try with different codec settings
            try:
                print("Retrying with different codec settings...")
                final_video.write_videofile(output_filename, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4)
                print(f"Successfully created video with alternative settings: {output_filename}")
            except Exception as retry_error:
                print(f"Failed to write video even with alternative settings: {retry_error}")
                traceback.print_exc()
                raise  # Re-raise to inform the caller about the failure
    except Exception as e:
        print(f"Critical error in mergevideo: {e}")
        traceback.print_exc()
        raise  # Re-raise to inform the caller about the failure
