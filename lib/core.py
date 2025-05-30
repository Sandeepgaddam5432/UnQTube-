import os
import shutil
import sys
import traceback
import time

from lib.video_texts import get_names, process_text, getyamll, read_random_line, get_item_content, get_intro_text
from lib.config_utils import read_config_file
from lib.image_procces import getim, delete_invalid_images, sortimage, shape_error
from lib.media_api import download_file, translateto, enhance_search_term, get_videos
from lib.video_editor import mergevideo
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.gemini_api import generate_script_with_gemini, generate_complete_top10_content

def get_temp_dir():
    """Get the appropriate tempfiles directory path based on environment"""
    try:
        # Check if we're running in Colab
        if os.path.exists('/content'):
            base_dir = '/content/UnQTube-'
            if os.path.exists(base_dir):
                temp_dir = os.path.join(base_dir, 'tempfiles')
                os.makedirs(temp_dir, exist_ok=True)
                return temp_dir
        
        # Default for local execution
        temp_dir = 'tempfiles'
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    except Exception as e:
        print(f"Error creating temp directory: {e}")
        # Fallback to a simple directory name
        return "tempfiles"

def intro(title):
    """Generate intro for video using Gemini"""
    temp_dir = get_temp_dir()
    intro_dir = os.path.join(temp_dir, "11")
    
    try:
        # Create directory
        os.makedirs(intro_dir, exist_ok=True)
        
        # Get intro text using Gemini
        try:
            introtext = get_intro_text(title)
            print(introtext)
        except Exception as e:
            print(f"Error generating intro text: {e}")
            # Fallback to simple intro text
            introtext = f"Welcome to our top ten video about {title}. If you enjoy this content, please like and subscribe to our channel."
            print(f"Using fallback intro text: {introtext}")
        
        audio_file = os.path.join(intro_dir, "11.mp3")
        try:
            generate_voice(introtext, audio_file, get_language_code(read_config_file()["language"]))
            print("Intro audio generated successfully")
        except Exception as e:
            print(f"Error generating intro voice: {e}")
            raise # Re-raise as this is critical
            
    except Exception as e:
        print(f"Error in intro generation: {e}")
        raise # Re-raise as this is a critical component

def top10s(top10, genre, title):
    """Generate content for each item in the top 10 list"""
    num = 1
    temp_dir = get_temp_dir()
    
    try:
        language = read_config_file()["language"]
    except Exception as e:
        print(f"Error reading language from config: {e}")
        language = "english"  # Default language
    
    language_code = get_language_code(language)
    
    # Calculate time per item
    try:
        total_minutes = int(read_config_file().get("time", "5"))
        time_per_item = int((total_minutes * 60) / 10)  # seconds per item
    except Exception as e:
        print(f"Error calculating time per item: {e}")
        time_per_item = 30  # Default time per item in seconds
    
    skipped_items = 0
    for top in top10:
        if skipped_items > 3:  # If more than 3 items fail, stop processing to avoid wasting time
            print("Too many failed items. Stopping processing.")
            break
            
        try:
            imagepath = str(num)
            npath = os.path.join(temp_dir, imagepath)
            mp3file = os.path.join(npath, f"{imagepath}.mp3")
        
            # Ensure directory exists
            os.makedirs(npath, exist_ok=True)
    
            try:
                # Get item content with search terms from Gemini
                item_data = get_item_content(title, top, genre, time_per_item)
                
                # Use the search terms for image search
                if "search_terms" in item_data and item_data["search_terms"]:
                    search_term = item_data["search_terms"][0]
                    print(f"Using Gemini-suggested search term: '{search_term}'")
                else:
                    search_term = f"{top} {genre}"
                    
                # Try to get images, but continue if it fails
                try:
                    getim(search_term, npath)
                    delete_invalid_images(npath)
                    sortimage(npath)
                    delete_invalid_images(npath)
                    shape_error(npath)
                    sortimage(npath)
                except Exception as e:
                    print(f"Error processing images for item {num}: {e}")
                    print("Continuing with available images...")
    
                # Get the script text
                text = item_data.get("script", f"Item {num}: {top} is an excellent example of {title}.")
                
                # Add the item number prefix
                try:
                    item_prefix = translateto(f"number {imagepath} {top}", language_code)
                    full_text = f"{item_prefix},,..,{text}"
                except Exception as e:
                    print(f"Error translating item prefix: {e}")
                    full_text = f"Item {imagepath}: {top}. {text}"
                
                print(full_text)
                print("--------------------------")
    
                generate_voice(full_text, mp3file, language_code)
                num = num + 1
                
            except Exception as e:
                print(f"Error processing item {num} ({top}): {e}")
                skipped_items += 1
                # Continue with the next item
                num = num + 1
                
        except Exception as e:
            print(f"Severe error processing item {num}: {e}")
            skipped_items += 1
            num = num + 1
            
    return num - 1  # Return the number of successfully processed items

def outro():
    """Generate outro for video"""
    temp_dir = get_temp_dir()
    outro_dir = os.path.join(temp_dir, "0")
  
    try:
        os.makedirs(outro_dir, exist_ok=True)
        
        try:
            # Download outro image
            image_path = os.path.join(outro_dir, "1.jpg")
            outro_image = read_random_line("download_list/outro_pic.txt")
            download_file(outro_image, image_path)
            if not os.path.exists(image_path):
                print("Warning: Outro image download failed")
        except Exception as e:
            print(f"Error downloading outro image: {e}")
            # Continue even if image fails
        
        try:
            # Generate outro audio
            audio_path = os.path.join(outro_dir, "0.mp3")
            outro_text = getyamll("outro_text")
            language_code = get_language_code(read_config_file().get("language", "english"))
            translated_outro = translateto(outro_text, language_code)
            generate_voice(translated_outro, audio_path, language_code)
            
            if not os.path.exists(audio_path):
                print("Error: Failed to generate outro audio")
                # Create a blank file as placeholder to avoid errors later
                with open(audio_path, "wb") as f:
                    f.write(b"")
                
        except Exception as e:
            print(f"Error generating outro audio: {e}")
            # This is more critical, but try to continue
    
    except Exception as e:
        print(f"Error in outro generation: {e}")
        # Try to continue as outro is not critical


def delete_directories_and_file(start, end, base_directory=None):
    if base_directory is None:
        base_directory = get_temp_dir()
        
    try:
        for i in range(start, end + 1):
            directory_path = os.path.join(base_directory, str(i))
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                try:
                    shutil.rmtree(directory_path)
                    print(f"Directory {i} deleted successfully.")
                except Exception as e:
                    print(f"Error deleting directory {i}: {e}")

        song_file_path = os.path.join(base_directory, "song.mp3")
        if os.path.exists(song_file_path) and os.path.isfile(song_file_path):
            try:
                os.remove(song_file_path)
                print("File 'song.mp3' deleted successfully.")
            except Exception as e:
                print(f"Error deleting 'song.mp3': {e}")

        print("Cleanup completed.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def making_video(title, genre=""):
    """Main function to create a top 10 video"""
    output_file = "UnQTube_" + title.replace(" ", "_") + ".mp4"
    if os.path.exists('/content'):
        output_file = os.path.join('/content', output_file)
        
    temp_dir = get_temp_dir()
    
    # Save cleanup function for finally block
    def cleanup():
        try:
            print("\n----- Running cleanup -----")
            if os.path.exists("temp.txt"):
                os.remove("temp.txt")
            delete_directories_and_file(0, 11)
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    try:
        # Get the genre
        try:
            genre = read_config_file()["general_topic"]
        except Exception as e:
            print(f"Error reading genre from config: {e}")
            if not genre:  # Only use default if no genre was provided as parameter
                genre = "video"  # Default genre
        
        print("\n====== STARTING TOP 10 VIDEO CREATION ======")
        print(f"Topic: {title}")
        print(f"Genre: {genre}")
        print(f"Output file will be: {output_file}")
        print("==========================================")
        
        # Get the top 10 list using Gemini
        try:
            print("\n----- Generating top 10 list with Gemini -----")
            top10 = get_names(title)
            if not top10 or len(top10) < 10:
                print(f"Warning: Only received {len(top10) if top10 else 0} items, expected 10")
                # Pad the list if needed
                if not top10:
                    top10 = [f"Item {i+1}" for i in range(10)]
                elif len(top10) < 10:
                    top10.extend([f"Item {len(top10) + i + 1}" for i in range(10 - len(top10))])
            
            print("Top 10 items:")
            for i, item in enumerate(top10, 1):
                print(f"{i}. {item}")
            print("✓ Top 10 list generated")
        except Exception as e:
            print(f"Error getting top 10 list: {e}")
            print("Using generic items...")
            top10 = [f"Item {i+1} for {title}" for i in range(10)]
            print("✓ Created fallback top 10 list")
        
        # Generate intro
        try:
            print("\n----- Creating intro -----")
            intro(title)
            print("✓ Intro created successfully")
        except Exception as e:
            print(f"Failed to create intro: {e}")
            print("Continuing without intro...")
        
        # Generate content for each item
        print("\n----- Generating content for each item -----")
        successful_items = top10s(top10, genre, title)
        if successful_items < 5:  # If less than half the items were successful
            print("Warning: Less than 5 items were successfully processed.")
        else:
            print(f"✓ Successfully processed {successful_items} items")
        
        # Generate outro
        try:
            print("\n----- Creating outro -----")
            outro()
            print("✓ Outro created successfully")
        except Exception as e:
            print(f"Failed to create outro: {e}")
            print("Continuing without outro...")
        
        # Download background music
        try:
            print("\n----- Downloading background music -----")
            music_file = os.path.join(temp_dir, "song.mp3")
            download_file(read_random_line("download_list/background_music.txt"), music_file)
            
            if not os.path.exists(music_file):
                print("Warning: Background music download failed. Creating empty file.")
                # Create empty file as fallback
                with open(music_file, "wb") as f:
                    f.write(b"") 
            else:
                print("✓ Background music downloaded")
                    
        except Exception as e:
            print(f"Error downloading background music: {e}")
            # Create empty file as fallback
            with open(os.path.join(temp_dir, "song.mp3"), "wb") as f:
                f.write(b"")
            print("Created empty music file as fallback")
        
        # Generate final video
        try:
            print("\n----- Creating final video -----")
            success = mergevideo(title, os.path.join(temp_dir, "song.mp3"), top10, title)
            if success:
                print(f"✓ Video successfully saved as: {output_file}")
                return True
            else:
                print("× Failed to create final video file")
                return False
        except Exception as e:
            print(f"Error creating final video: {e}")
            print("See error details above.")
            return False
        
    except Exception as e:
        print(f"Error in video creation process: {e}")
        traceback.print_exc()
        print("\nUnQTube video creation failed.")
        return False
    finally:
        cleanup()

def make_intro(title):
    """Make video intro with optional video instead of image"""
    try:
        withvideo = read_config_file()["intro_video"].lower() in ["yes", "true", "1"]
    except Exception as e:
        print(f"Error reading intro_video setting: {e}")
        withvideo = False
        
    if withvideo:
        try:
            # Check if we should use Gemini to enhance the video search
            use_gemini = read_config_file().get('use_gemini', 'no').lower() in ['yes', 'true', '1']
            
            search_title = title
            if use_gemini:
                try:
                    # Enhance the search title using Gemini
                    enhanced_title = enhance_search_term(title)
                    if enhanced_title and enhanced_title != title:
                        print(f"Using Gemini-enhanced intro video search: '{enhanced_title}'")
                        search_title = enhanced_title
                except Exception as e:
                    print(f"Error enhancing search term: {e}")
                    # Continue with original title
            
            try:
                links = get_videos(search_title)
                return links  # Return the links for video processing
            except Exception as e:
                print(f"Error getting videos for intro: {e}")
                return None  # Return None to indicate failure
                
        except Exception as e:
            print(f"Error in video intro preparation: {e}")
            return None  # Return None to indicate failure
    
    # If withvideo is False or any errors occur, return None
    return None

def making_video_optimized(title, genre=""):
    """Optimized function to create a top 10 video using a single Gemini API call"""
    output_file = "UnQTube_" + title.replace(" ", "_") + ".mp4"
    if os.path.exists('/content'):
        output_file = os.path.join('/content', output_file)
        
    temp_dir = get_temp_dir()
    
    # Save cleanup function for finally block
    def cleanup():
        try:
            print("\n----- Running cleanup -----")
            if os.path.exists("temp.txt"):
                os.remove("temp.txt")
            delete_directories_and_file(0, 11)
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    try:
        # Get the genre
        try:
            genre = read_config_file()["general_topic"]
        except Exception as e:
            print(f"Error reading genre from config: {e}")
            if not genre:  # Only use default if no genre was provided as parameter
                genre = "video"  # Default genre
        
        print("\n====== STARTING OPTIMIZED TOP 10 VIDEO CREATION ======")
        print(f"Topic: {title}")
        print(f"Genre: {genre}")
        print(f"Output file will be: {output_file}")
        print("==========================================")
        
        # Get all content in a single API call
        try:
            print("\n----- Generating all content with a single Gemini API call -----")
            language = read_config_file().get("language", "english")
            complete_content = generate_complete_top10_content(title, genre, language)
            
            if not complete_content:
                raise ValueError("Failed to generate complete content")
                
            print("✓ Successfully generated all content in a single API call")
            print(f"Top 10 items:")
            for i, item in enumerate(complete_content["items"], 1):
                print(f"{i}. {item}")
                
        except Exception as e:
            print(f"Error generating complete content: {e}")
            print("Falling back to non-optimized content generation...")
            return making_video(title, genre)
        
        # Generate intro
        try:
            print("\n----- Creating intro -----")
            intro_dir = os.path.join(temp_dir, "11")
            os.makedirs(intro_dir, exist_ok=True)
            
            # Use intro text from the complete content
            intro_text = complete_content["intro"]
            print(intro_text)
            
            # Generate intro audio
            audio_file = os.path.join(intro_dir, "11.mp3")
            language_code = get_language_code(language)
            generate_voice(intro_text, audio_file, language_code)
            print("✓ Intro audio generated successfully")
            
            # Download images for intro
            try:
                getim(title, intro_dir)
                delete_invalid_images(intro_dir)
                sortimage(intro_dir)
                delete_invalid_images(intro_dir)
                shape_error(intro_dir)
                sortimage(intro_dir)
                print("✓ Intro images downloaded and processed")
            except Exception as e:
                print(f"Error processing intro images: {e}")
                print("Continuing with available or placeholder images...")
            
        except Exception as e:
            print(f"Failed to create intro: {e}")
            print("Continuing without intro...")
        
        # Generate content for each item
        print("\n----- Generating content for each item -----")
        top10 = complete_content["items"]
        successful_items = 0
        
        # Process each item
        for i, (item, segment) in enumerate(zip(top10, complete_content["segments"]), 1):
            try:
                print(f"\nProcessing item {i}: {item}")
                item_dir = os.path.join(temp_dir, str(i))
                os.makedirs(item_dir, exist_ok=True)
                
                # Get search terms
                search_terms = segment.get("search_terms", [])
                if search_terms:
                    search_term = search_terms[0]
                    print(f"Using search term: '{search_term}'")
                else:
                    search_term = f"{item} {genre}"
                    print(f"Using default search term: '{search_term}'")
                
                # Download images
                try:
                    getim(search_term, item_dir)
                    delete_invalid_images(item_dir)
                    sortimage(item_dir)
                    delete_invalid_images(item_dir)
                    shape_error(item_dir)
                    sortimage(item_dir)
                    print("✓ Images downloaded and processed")
                except Exception as e:
                    print(f"Error processing images: {e}")
                    print("Continuing with available or placeholder images...")
                
                # Get script text
                script_text = segment.get("script", f"Item {i}: {item} is an excellent example of {title}.")
                
                # Add the item number prefix
                try:
                    item_prefix = translateto(f"number {i} {item}", language_code)
                    full_text = f"{item_prefix},,..,{script_text}"
                except Exception as e:
                    print(f"Error translating item prefix: {e}")
                    full_text = f"Item {i}: {item}. {script_text}"
                
                print(full_text)
                
                # Generate audio
                mp3file = os.path.join(item_dir, f"{i}.mp3")
                generate_voice(full_text, mp3file, language_code)
                print(f"✓ Item {i} processed successfully")
                successful_items += 1
                
            except Exception as e:
                print(f"Error processing item {i}: {e}")
                print("Continuing with next item...")
        
        # Generate outro
        try:
            print("\n----- Creating outro -----")
            outro_dir = os.path.join(temp_dir, "0")
            os.makedirs(outro_dir, exist_ok=True)
            
            # Download outro image
            try:
                image_path = os.path.join(outro_dir, "1.jpg")
                outro_image = read_random_line("download_list/outro_pic.txt")
                download_file(outro_image, image_path)
                if os.path.exists(image_path):
                    print("✓ Outro image downloaded")
                else:
                    print("Warning: Outro image download failed")
            except Exception as e:
                print(f"Error downloading outro image: {e}")
            
            # Generate outro audio
            try:
                audio_path = os.path.join(outro_dir, "0.mp3")
                outro_text = complete_content["outro"]
                generate_voice(outro_text, audio_path, language_code)
                
                if os.path.exists(audio_path):
                    print("✓ Outro audio generated")
                else:
                    print("Error: Failed to generate outro audio")
                    # Create a blank file as placeholder
                    with open(audio_path, "wb") as f:
                        f.write(b"")
            except Exception as e:
                print(f"Error generating outro audio: {e}")
                # Create a blank file as placeholder
                with open(os.path.join(outro_dir, "0.mp3"), "wb") as f:
                    f.write(b"")
        
        except Exception as e:
            print(f"Failed to create outro: {e}")
            print("Continuing without outro...")
        
        # Download background music
        try:
            print("\n----- Downloading background music -----")
            music_file = os.path.join(temp_dir, "song.mp3")
            download_file(read_random_line("download_list/background_music.txt"), music_file)
            
            if not os.path.exists(music_file):
                print("Warning: Background music download failed. Creating empty file.")
                # Create empty file as fallback
                with open(music_file, "wb") as f:
                    f.write(b"") 
            else:
                print("✓ Background music downloaded")
                    
        except Exception as e:
            print(f"Error downloading background music: {e}")
            # Create empty file as fallback
            with open(os.path.join(temp_dir, "song.mp3"), "wb") as f:
                f.write(b"")
            print("Created empty music file as fallback")
        
        # Generate final video
        try:
            print("\n----- Creating final video -----")
            success = mergevideo(title, os.path.join(temp_dir, "song.mp3"), top10, title)
            if success:
                print(f"✓ Video successfully saved as: {output_file}")
                return True
            else:
                print("× Failed to create final video file")
                return False
        except Exception as e:
            print(f"Error creating final video: {e}")
            print("See error details above.")
            return False
        
    except Exception as e:
        print(f"Error in optimized video creation process: {e}")
        traceback.print_exc()
        print("\nFalling back to non-optimized video creation...")
        return making_video(title, genre)
    finally:
        cleanup()

# For backward compatibility, replace the original function with the optimized one
making_video_original = making_video  # Keep the original function
making_video = making_video_optimized  # Replace with optimized version
