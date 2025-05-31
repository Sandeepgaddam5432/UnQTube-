import os
import shutil
import sys

from lib.video_texts import get_names, process_text, getyamll, read_random_line, get_item_content, get_intro_text
from lib.config_utils import read_config_file
from lib.image_procces import getim, delete_invalid_images, sortimage, shape_error
from lib.media_api import download_file, translateto, enhance_search_term, get_videos
from lib.video_editor import mergevideo
from lib.voices import generate_voice
from lib.language import get_language_code
from lib.gemini_api import generate_script_with_gemini

def get_temp_dir():
    """Get the appropriate tempfiles directory path based on environment"""
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

def intro(title):
    """Generate intro for video using Gemini"""
    # Get intro text using Gemini
    introtext = get_intro_text(title)
    print(introtext)
  
    temp_dir = get_temp_dir()
    intro_dir = os.path.join(temp_dir, "11")
  
    try:
        os.makedirs(intro_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {intro_dir}: {e}")
  
    audio_file = os.path.join(intro_dir, "11.mp3")
    generate_voice(introtext, audio_file, get_language_code(read_config_file()["language"]))

def top10s(top10, genre, title):
    """Generate content for each item in the top 10 list"""
    num = 1
    temp_dir = get_temp_dir()
    language = read_config_file()["language"]
    language_code = get_language_code(language)
    
    # Calculate time per item
    total_minutes = int(read_config_file()["time"])
    time_per_item = int((total_minutes * 60) / 10)  # seconds per item
  
    for top in top10:
        imagepath = str(num)
        npath = os.path.join(temp_dir, imagepath)
        mp3file = os.path.join(npath, f"{imagepath}.mp3")
    
        # Ensure directory exists
        os.makedirs(npath, exist_ok=True)

        # Get item content with search terms from Gemini
        item_data = get_item_content(title, top, genre, time_per_item)
        
        # Use the search terms for image search
        if "search_terms" in item_data and item_data["search_terms"]:
            search_term = item_data["search_terms"][0]
            print(f"Using Gemini-suggested search term: '{search_term}'")
        else:
            search_term = f"{top} {genre}"
            
        getim(search_term, npath)
        delete_invalid_images(npath)
        sortimage(npath)
        delete_invalid_images(npath)
        shape_error(npath)
        sortimage(npath)

        # Get the script text
        text = item_data.get("script", f"Item {num}: {top} is an excellent example of {title}.")
        
        # Add the item number prefix
        item_prefix = translateto(f"number {imagepath} {top}", language_code)
        full_text = f"{item_prefix},,..,{text}"
        
        print(full_text)
        print("--------------------------")

        generate_voice(full_text, mp3file, language_code)
        num = num + 1

def outro():
    """Generate outro for video"""
    temp_dir = get_temp_dir()
    outro_dir = os.path.join(temp_dir, "0")
  
    os.makedirs(outro_dir, exist_ok=True)
  
    download_file(read_random_line("download_list/outro_pic.txt"), os.path.join(outro_dir, "1.jpg"))
    
    # Get the outro text from YAML and translate it
    outro_text = getyamll("outro_text")
    translated_outro = translateto(outro_text, get_language_code(read_config_file()["language"]))
    
    generate_voice(translated_outro, 
                 os.path.join(outro_dir, "0.mp3"),
                 get_language_code(read_config_file()["language"]))


def delete_directories_and_file(start, end, base_directory=None):
    if base_directory is None:
        base_directory = get_temp_dir()
        
    try:
        for i in range(start, end + 1):
            directory_path = os.path.join(base_directory, str(i))
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                shutil.rmtree(directory_path)
                print(f"Directory {i} deleted successfully.")
            else:
                print(f"Directory {i} not found.")

        song_file_path = os.path.join(base_directory, "song.mp3")
        if os.path.exists(song_file_path) and os.path.isfile(song_file_path):
            os.remove(song_file_path)
            print("File 'song.mp3' deleted successfully.")
        else:
            print("File 'song.mp3' not found.")

        print("All directories and the file 'song.mp3' deleted successfully.")
    except Exception as e:
        print(f"Error while deleting directories and file: {e}")

def making_video(title, genre=""):
    """Main function to create a top 10 video"""
    genre = read_config_file()["general_topic"]
    print("--------------------------")
    print(title)
    print("--------------------------")
    
    # Get the top 10 list using Gemini
    top10 = get_names(title)
    print(top10)
    print("--------------------------")
    
    # Generate intro, content for each item, and outro
    intro(title)
    print("--------------------------")
    top10s(top10, genre, title)
    outro()

    temp_dir = get_temp_dir()
    download_file(read_random_line("download_list/background_music.txt"), os.path.join(temp_dir, "song.mp3"))
    mergevideo(title, os.path.join(temp_dir, "song.mp3"), top10, title)
    delete_directories_and_file(0, 11)
    
    if os.path.exists("temp.txt"):
        os.remove("temp.txt")
    
    sys.exit()

def make_intro(title):
    """Make video intro with optional video instead of image"""
    withvideo = read_config_file()["intro_video"]
    if withvideo.lower() in ["yes", "true", "1"]:
        # Check if we should use Gemini to enhance the video search
        use_gemini = read_config_file().get('use_gemini', 'no').lower() in ['yes', 'true', '1']
        
        if use_gemini:
            # Enhance the search title using Gemini
            enhanced_title = enhance_search_term(title)
            print(f"Using Gemini-enhanced intro video search: '{enhanced_title}'")
            search_title = enhanced_title
        else:
            search_title = title
        
        links = get_videos(search_title)
