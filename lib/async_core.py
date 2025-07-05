"""
Asynchronous Core Module for UnQTube

This module provides asynchronous video generation capabilities
to drastically improve performance and parallelism.
"""

import os
import asyncio
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
import traceback

from lib.content_generation import generate_top10_content, generate_short_content
from lib.config_utils import read_config_file
from lib.image_procces import getim, delete_invalid_images, sortimage, shape_error
from lib.media_api import download_file, get_videos
from lib.video_editor import mergevideo
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.core import get_temp_dir

class AsyncVideoGenerator:
    """Asynchronous video generation pipeline
    
    This class orchestrates the parallel execution of all components
    needed to generate a video, optimizing the workflow for performance.
    """
    
    def __init__(self, title, genre="", language="english"):
        """Initialize the async video generator
        
        Args:
            title (str): The main topic title
            genre (str): The general genre/category
            language (str): The target language
        """
        self.title = title
        self.genre = genre
        self.language = language
        self.language_code = get_language_code(language)
        self.temp_dir = get_temp_dir()
        self.content = None
        self.max_workers = min(os.cpu_count() or 4, 8)  # Limit based on available CPU cores
        
    async def generate_video(self):
        """Generate a complete video with all components running in parallel
        
        This is the main entry point for asynchronous video generation.
        
        Returns:
            str: Path to the generated video file
        """
        try:
            start_time = time.time()
            print(f"\n==== Starting asynchronous video generation for '{self.title}' ====")
            
            # Ensure temp directory exists
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # First generate content (needed before we can start other tasks)
            print("Generating content...")
            self.content = await generate_top10_content(self.title, self.genre, self.language)
            
            if not self.content or not self.content.get("top10"):
                raise ValueError("Failed to generate content structure")
                
            print(f"✓ Content generated with {len(self.content['top10'])} items")
            
            # Create intro in parallel with item processing
            intro_task = asyncio.create_task(self._process_intro())
            
            # Process all items in parallel
            print("Processing all segments in parallel...")
            top10_tasks = []
            for i, item in enumerate(self.content["top10"]):
                task = asyncio.create_task(self._process_item(item, i + 1))
                top10_tasks.append(task)
                
            # Create outro in parallel
            outro_task = asyncio.create_task(self._process_outro())
            
            # Wait for all tasks to complete
            await asyncio.gather(intro_task, outro_task, *top10_tasks)
            
            # Merge everything into final video
            print("\nAll components ready. Merging final video...")
            output_file = await self._merge_video()
            
            elapsed = time.time() - start_time
            print(f"==== Video generation completed in {elapsed:.2f} seconds ====\n")
            print(f"Output file: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"Error during async video generation: {e}")
            traceback.print_exc()
            raise
            
    async def generate_short_video(self, duration=30):
        """Generate a short-form vertical video
        
        Args:
            duration (int): Desired duration in seconds
            
        Returns:
            str: Path to the generated short video
        """
        try:
            start_time = time.time()
            print(f"\n==== Starting asynchronous short video generation for '{self.title}' ====")
            
            # Ensure temp directory exists
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Generate content for short video
            print("Generating short video content...")
            self.content = await generate_short_content(self.title, self.language)
            
            if not self.content or not self.content.get("scenes"):
                raise ValueError("Failed to generate short video content structure")
                
            print(f"✓ Content generated with {len(self.content['scenes'])} scenes")
            
            # Process all scenes in parallel
            print("Processing all scenes in parallel...")
            scene_tasks = []
            for i, scene in enumerate(self.content["scenes"]):
                task = asyncio.create_task(self._process_scene(scene, i + 1))
                scene_tasks.append(task)
                
            # Wait for all scenes to be processed
            await asyncio.gather(*scene_tasks)
            
            # Merge everything into final video
            print("\nAll scenes ready. Merging final short video...")
            output_file = await self._merge_short_video()
            
            elapsed = time.time() - start_time
            print(f"==== Short video generation completed in {elapsed:.2f} seconds ====\n")
            print(f"Output file: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"Error during async short video generation: {e}")
            traceback.print_exc()
            raise
            
    async def _process_intro(self):
        """Process intro segment with text and media
        
        Returns:
            bool: True if successful, False otherwise
        """
        intro_dir = os.path.join(self.temp_dir, "11")
        os.makedirs(intro_dir, exist_ok=True)
        
        try:
            # Extract intro text
            intro_text = self.content.get("intro_text", f"Welcome to our top ten video about {self.title}.")
            
            # Check for hooks if available
            if "hooks" in self.content:
                try:
                    hooks = self.content["hooks"]
                    if isinstance(hooks, dict) and "opening_hook" in hooks:
                        intro_text = hooks["opening_hook"]
                except Exception as e:
                    print(f"Error using hooks for intro: {e}")
                    
            print(f"Generating intro: '{intro_text[:50]}...'")
            
            # Generate audio
            audio_file = os.path.join(intro_dir, "11.mp3")
            audio_task = asyncio.create_task(self._generate_audio(intro_text, audio_file))
            
            # Get intro media (images or video) in parallel
            media_task = asyncio.create_task(self._get_intro_media(intro_dir))
            
            # Wait for both tasks to complete
            await asyncio.gather(audio_task, media_task)
            
            return True
        except Exception as e:
            print(f"Error processing intro: {e}")
            return False
            
    async def _process_item(self, item, num):
        """Process a single top 10 item with text and media
        
        Args:
            item (dict): Item data including name, script, search_terms
            num (int): Item number (1-10)
            
        Returns:
            bool: True if successful, False otherwise
        """
        item_dir = os.path.join(self.temp_dir, str(num))
        os.makedirs(item_dir, exist_ok=True)
        
        try:
            # Extract item info
            name = item.get("name", f"Item {num}")
            script = item.get("script", f"This is item {num} in our list of {self.title}.")
            search_terms = item.get("search_terms", [f"{self.title} {num}"])
            
            print(f"Processing item #{num}: '{name}'")
            
            # Add the item number prefix
            try:
                item_prefix = f"number {num} {name}"
                full_text = f"{item_prefix},,..,{script}"
            except Exception as e:
                print(f"Error creating item prefix: {e}")
                full_text = f"Item {num}: {name}. {script}"
            
            # Generate audio and get media in parallel
            audio_file = os.path.join(item_dir, f"{num}.mp3")
            audio_task = asyncio.create_task(self._generate_audio(full_text, audio_file))
            
            # Get images with the first search term
            search_term = search_terms[0] if search_terms else f"{name} {self.genre}"
            media_task = asyncio.create_task(self._get_images(search_term, item_dir))
            
            # Wait for both tasks to complete
            await asyncio.gather(audio_task, media_task)
            
            return True
        except Exception as e:
            print(f"Error processing item {num}: {e}")
            return False
            
    async def _process_outro(self):
        """Process outro segment with text and media
        
        Returns:
            bool: True if successful, False otherwise
        """
        outro_dir = os.path.join(self.temp_dir, "0")
        os.makedirs(outro_dir, exist_ok=True)
        
        try:
            # Extract outro text
            outro_text = self.content.get("conclusion", f"Thanks for watching our video about {self.title}. If you enjoyed this content, please like and subscribe!")
            
            # Check for subscription hook if available
            if "hooks" in self.content:
                try:
                    hooks = self.content["hooks"]
                    if isinstance(hooks, dict) and "subscription_hook" in hooks:
                        outro_text += " " + hooks["subscription_hook"]
                except Exception as e:
                    print(f"Error using hooks for outro: {e}")
            
            print(f"Generating outro: '{outro_text[:50]}...'")
            
            # Generate audio
            audio_file = os.path.join(outro_dir, "0.mp3")
            audio_task = asyncio.create_task(self._generate_audio(outro_text, audio_file))
            
            # Get outro image
            media_task = asyncio.create_task(self._get_outro_image(outro_dir))
            
            # Wait for both tasks to complete
            await asyncio.gather(audio_task, media_task)
            
            return True
        except Exception as e:
            print(f"Error processing outro: {e}")
            return False
            
    async def _process_scene(self, scene, num):
        """Process a single scene for short videos
        
        Args:
            scene (dict): Scene data including text and search_terms
            num (int): Scene number
            
        Returns:
            bool: True if successful, False otherwise
        """
        scene_dir = os.path.join(self.temp_dir, f"scene_{num}")
        os.makedirs(scene_dir, exist_ok=True)
        
        try:
            # Extract scene info
            text = scene.get("text", f"Scene {num} about {self.title}")
            visual_desc = scene.get("visual_description", f"Scene {num}")
            search_terms = scene.get("search_terms", [f"{self.title} {visual_desc}"])
            
            print(f"Processing scene #{num}: '{visual_desc}'")
            
            # Generate audio and get video in parallel
            audio_file = os.path.join(scene_dir, f"audio_{num}.mp3")
            audio_task = asyncio.create_task(self._generate_audio(text, audio_file))
            
            # Get video for scene with the first search term
            search_term = search_terms[0] if search_terms else visual_desc
            video_file = os.path.join(scene_dir, f"video_{num}.mp4")
            video_task = asyncio.create_task(self._get_video(search_term, video_file))
            
            # Wait for both tasks to complete
            await asyncio.gather(audio_task, video_task)
            
            return True
        except Exception as e:
            print(f"Error processing scene {num}: {e}")
            return False
    
    async def _generate_audio(self, text, output_file):
        """Generate audio for text asynchronously
        
        Args:
            text (str): Text to convert to speech
            output_file (str): Path to save audio file
            
        Returns:
            str: Path to generated audio file
        """
        try:
            # Run in a thread pool since generate_voice is not async
            result = await asyncio.to_thread(generate_voice, text, output_file, self.language_code)
            return result
        except Exception as e:
            print(f"Error generating audio: {e}")
            raise
            
    async def _get_images(self, search_term, output_dir):
        """Download and process images for a segment
        
        Args:
            search_term (str): Term to search for images
            output_dir (str): Directory to save images
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Download images asynchronously
            await asyncio.to_thread(getim, search_term, output_dir)
            
            # Process images in separate threads
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Run image processing tasks in thread pool
                await asyncio.gather(
                    asyncio.to_thread(delete_invalid_images, output_dir),
                    asyncio.to_thread(sortimage, output_dir),
                    asyncio.to_thread(shape_error, output_dir)
                )
                
            return True
        except Exception as e:
            print(f"Error getting images for '{search_term}': {e}")
            # Create fallback blank image
            self._create_fallback_image(output_dir)
            return False
            
    def _create_fallback_image(self, directory):
        """Create a fallback image when download fails
        
        Args:
            directory (str): Directory to save fallback image
        """
        import numpy as np
        import cv2
        
        try:
            blank_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
            # Add some text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(blank_img, f"{self.title}", (100, 540), font, 2, (255, 255, 255), 5, cv2.LINE_AA)
            cv2.imwrite(os.path.join(directory, "fallback.jpg"), blank_img)
        except Exception as e:
            print(f"Error creating fallback image: {e}")
    
    async def _get_intro_media(self, intro_dir):
        """Get media for intro (either video or images)
        
        Args:
            intro_dir (str): Directory to save intro media
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if we should use video for intro
            use_video = read_config_file().get("intro_video", "no").lower() in ["yes", "true", "1"]
            
            if use_video:
                # Get intro video
                try:
                    video_links = await asyncio.to_thread(get_videos, self.title)
                    if video_links:
                        intro_video = os.path.join(intro_dir, "intro.mp4")
                        await asyncio.to_thread(download_file, video_links[0], intro_video)
                        return True
                except Exception as e:
                    print(f"Error getting intro video: {e}")
                    # Fall back to images
                    use_video = False
            
            # If not using video or video failed, get images
            if not use_video:
                return await self._get_images(self.title, intro_dir)
                
        except Exception as e:
            print(f"Error getting intro media: {e}")
            # Create fallback
            self._create_fallback_image(intro_dir)
            return False
            
    async def _get_outro_image(self, outro_dir):
        """Get image for outro
        
        Args:
            outro_dir (str): Directory to save outro image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get outro image from list
            image_path = os.path.join(outro_dir, "1.jpg")
            
            try:
                with open("download_list/outro_pic.txt", "r") as f:
                    lines = f.readlines()
                    if lines:
                        import random
                        outro_image_url = random.choice(lines).strip()
                        await asyncio.to_thread(download_file, outro_image_url, image_path)
                        return True
            except Exception as e:
                print(f"Error reading outro image list: {e}")
                
            # If reading from file fails, get a generic image
            return await self._get_images(f"{self.title} conclusion", outro_dir)
            
        except Exception as e:
            print(f"Error getting outro image: {e}")
            # Create fallback
            self._create_fallback_image(outro_dir)
            return False
            
    async def _get_video(self, search_term, output_file):
        """Get video for a scene in short videos
        
        Args:
            search_term (str): Term to search for video
            output_file (str): Path to save video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from lib.shortcore import get_video
            
            # Get video using the shortcore function
            result = await asyncio.to_thread(get_video, search_term, output_file)
            return result
        except Exception as e:
            print(f"Error getting video for '{search_term}': {e}")
            # Create fallback video
            self._create_fallback_video(output_file)
            return False
            
    def _create_fallback_video(self, output_file):
        """Create a fallback video when download fails
        
        Args:
            output_file (str): Path to save fallback video
        """
        import numpy as np
        import cv2
        
        try:
            # Create a 3-second blank video
            fps = 30
            duration = 3
            height, width = 1080, 1920
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            
            # Create blank frame with text
            blank_frame = np.zeros((height, width, 3), dtype=np.uint8)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(blank_frame, f"{self.title}", (width//4, height//2), font, 2, (255, 255, 255), 5, cv2.LINE_AA)
            
            # Write frames
            for _ in range(fps * duration):
                video.write(blank_frame)
                
            video.release()
        except Exception as e:
            print(f"Error creating fallback video: {e}")
            
    async def _merge_video(self):
        """Merge all components into final video
        
        Returns:
            str: Path to the final video
        """
        try:
            # Run mergevideo in a thread
            output_file = "UnQTube_output.mp4"
            if os.path.exists('/content'):
                output_file = os.path.join('/content', output_file)
                
            # Get background music path
            try:
                with open("download_list/background_music.txt", "r") as f:
                    music_list = f.readlines()
                    if music_list:
                        import random
                        background_music = random.choice(music_list).strip()
                    else:
                        background_music = None
            except Exception as e:
                print(f"Error reading background music list: {e}")
                background_music = None
                
            # Create final video using existing mergevideo function
            result = await asyncio.to_thread(
                mergevideo, 
                output_file, 
                background_music, 
                self.content.get("top10", []), 
                self.title
            )
            
            return output_file
        except Exception as e:
            print(f"Error merging video: {e}")
            raise
            
    async def _merge_short_video(self):
        """Merge all scenes into final short video
        
        Returns:
            str: Path to the final short video
        """
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
            from lib.shortcore import resize_and_text
            
            output_file = "UnQTube_short.mp4"
            if os.path.exists('/content'):
                output_file = os.path.join('/content', output_file)
                
            # Process each scene and prepare clips
            clips = []
            scene_count = len(self.content.get("scenes", []))
            
            for i in range(scene_count):
                scene_dir = os.path.join(self.temp_dir, f"scene_{i+1}")
                video_file = os.path.join(scene_dir, f"video_{i+1}.mp4")
                audio_file = os.path.join(scene_dir, f"audio_{i+1}.mp3")
                
                if os.path.exists(video_file) and os.path.exists(audio_file):
                    # Create path without extension for resize_and_text
                    base_path = os.path.join(scene_dir, f"scene_{i+1}")
                    
                    # Create symlinks for compatibility with resize_and_text
                    if not os.path.exists(f"{base_path}.mp4"):
                        os.symlink(video_file, f"{base_path}.mp4")
                    if not os.path.exists(f"{base_path}.mp3"):
                        os.symlink(audio_file, f"{base_path}.mp3")
                    
                    # Use resize_and_text to process the clip
                    clip = await asyncio.to_thread(resize_and_text, base_path)
                    clips.append(clip)
            
            # If we have clips, merge them
            if clips:
                final_clip = concatenate_videoclips(clips)
                final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac', fps=30)
                return output_file
            else:
                raise ValueError("No valid clips to merge")
                
        except Exception as e:
            print(f"Error merging short video: {e}")
            raise

async def make_video_async(title, genre=""):
    """Main entry point for asynchronous video generation
    
    Args:
        title (str): The main topic title
        genre (str): The general genre/category
        
    Returns:
        str: Path to the generated video
    """
    # Read config
    try:
        config = read_config_file()
        language = config.get("language", "english")
    except Exception as e:
        print(f"Error reading config: {e}")
        language = "english"
        
    # Create generator and run
    generator = AsyncVideoGenerator(title, genre, language)
    return await generator.generate_video()
    
async def make_short_video_async(topic, duration=30):
    """Main entry point for asynchronous short video generation
    
    Args:
        topic (str): The topic for the short video
        duration (int): Desired duration in seconds
        
    Returns:
        str: Path to the generated short video
    """
    # Read config
    try:
        config = read_config_file()
        language = config.get("language", "english")
    except Exception as e:
        print(f"Error reading config: {e}")
        language = "english"
        
    # Create generator and run
    generator = AsyncVideoGenerator(topic, "", language)
    return await generator.generate_short_video(duration)
    
def cleanup():
    """Clean up temporary files"""
    try:
        temp_dir = get_temp_dir()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up {temp_dir}")
    except Exception as e:
        print(f"Error during cleanup: {e}") 