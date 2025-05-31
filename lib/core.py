import os
import shutil
import sys

from lib.video_texts import get_names,process_text,getyamll,read_config_file,read_random_line
from lib.image_procces import getim,delete_invalid_images,sortimage,shape_error
from lib.APIss import download_file,chatgpt,translateto,enhance_search_term
from lib.video_editor import mergevideo
from lib.voices import generate_voice
from lib.language import get_language_code

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
  introtext = chatgpt(getyamll("intro_prompt").format(title=title,language=read_config_file()["language"]))
  introtext = process_text(introtext, ":")
  print(introtext)
  
  temp_dir = get_temp_dir()
  intro_dir = os.path.join(temp_dir, "11")
  
  try:
      os.makedirs(intro_dir, exist_ok=True)
  except Exception as e:
      print(f"Error creating directory {intro_dir}: {e}")
  
  audio_file = os.path.join(intro_dir, "11.mp3")
  generate_voice(introtext, audio_file, get_language_code(read_config_file()["language"]))

def top10s(top10,genre,title):
  num = 1
  temp_dir = get_temp_dir()
  
  for top in top10:
    imagepath=str(num)
    npath = os.path.join(temp_dir, imagepath)
    mp3file = os.path.join(npath, f"{imagepath}.mp3")
    
    # Ensure directory exists
    os.makedirs(npath, exist_ok=True)

    getim(top+" "+genre,npath)
    delete_invalid_images(npath)
    sortimage(npath)
    delete_invalid_images(npath)
    shape_error(npath)
    sortimage(npath)

    time = int(read_config_file()["time"]) * 60 / 10
    time = int(time)
    text = chatgpt(getyamll("text_prompt").format(title=title,top=top,genre=genre,time=str(time),language=read_config_file()["language"]))
    text = translateto("number " + imagepath +" " + top, get_language_code(read_config_file()["language"])) +",,.."+ text
    lines = text.strip().split('\n')
    if "Here's" in lines[0]:
        lines.pop()
    if "sure" in lines[0]:
        lines.pop()
    text = '\n'.join(lines)

    print(text)

    generate_voice(text, mp3file,get_language_code(read_config_file()["language"]))

    print("--------------------------")
    num = num + 1

def outro():
  temp_dir = get_temp_dir()
  outro_dir = os.path.join(temp_dir, "0")
  
  os.makedirs(outro_dir, exist_ok=True)
  
  download_file(read_random_line("download_list/outro_pic.txt"), os.path.join(outro_dir, "1.jpg"))
  generate_voice(translateto(getyamll("outro_text"),get_language_code(read_config_file()["language"])), 
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

def making_video(title,genre=""):
  genre = read_config_file()["general_topic"]
  print("--------------------------")
  print(title)
  print("--------------------------")
  top10=get_names(title)
  print(top10)
  print("--------------------------")
  intro(title)
  print("--------------------------")
  top10s(top10,genre,title)
  outro()

  temp_dir = get_temp_dir()
  download_file(read_random_line("download_list/background_music.txt"), os.path.join(temp_dir, "song.mp3"))
  mergevideo(title, os.path.join(temp_dir, "song.mp3"), top10, title)
  delete_directories_and_file(0, 11)
  if os.path.exists("temp.txt"):
    os.remove("temp.txt")
  sys.exit()

def make_intro(title):
  withvideo= read_config_file()["intro_video"]
  if(withvideo == "yes" or withvideo == "Yes" or withvideo == "YES"):
    
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
