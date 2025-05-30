import re
import requests
import urllib.parse
from deep_translator import GoogleTranslator
import os
from lib.config_utils import read_config_file

#images API (Bing)
def _extractBingImages(html):
    pattern = r'mediaurl=(.*?)&.*?expw=(\d+).*?exph=(\d+)'
    matches = re.findall(pattern, html)
    result = []

    for match in matches:
        url, width, height = match
        if url.endswith('.jpg') or url.endswith('.jpeg'):
            result.append({'url': urllib.parse.unquote(url), 'width': int(width), 'height': int(height)})

    return result

def getBingImages(texts, retries=5):
    texts = texts + " Quality image"
    texts = texts.replace(" ", "+")
    images = []
    tries = 0
    while(len(images) == 0 and tries < retries):
        response = requests.get(f"https://www.bing.com/images/search?q={texts}&first=1")
        if(response.status_code == 200):
            images = _extractBingImages(response.text)
        else:
            print("Error While making bing image searches", response.text)
            raise Exception("Error While making bing image searches")
    if(images):
        return images
    raise Exception("Error While making bing image searches")

#video API (Pexels)
def get_videos(title):
  url = "https://api.pexels.com/videos/search"
  headers = {
      "Authorization": read_config_file()["pexels_api"]
  }
  params = {
      "query": title,
      "orientation": "landscape",
      "per_page": 30
  }

  response = requests.get(url, headers=headers, params=params)
  json_data = response.json()

  links = []
  for i in range(30):
    link = json_data['videos'][i]['video_files'][0]['link']
    links.append(link)

  return links
        
# Download any file
def download_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(8192):
                file.write(chunk)
        print("file downloaded successfully.")
    else:
        print("Failed to download the file.")


def translateto(text, language):
    translator = GoogleTranslator(target=language)
    return translator.translate(text)

# Enhanced media search using Gemini
def enhance_search_term(term, api_key=None):
    """Use Gemini to enhance a search term for better media results"""
    try:
        from lib.gemini_api import generate_script_with_gemini
        
        prompt = f"""
        Enhance this search term to make it more specific and better for finding high-quality stock 
        footage or images: "{term}"
        
        Return ONLY the enhanced search term as a single line of text, with no explanation or additional text.
        Focus on adding visual details, camera angles, or composition details.
        """
        
        response = generate_script_with_gemini(prompt, api_key)
        
        # Clean up response - extract just the first line without any quotes or formatting
        enhanced_term = response.strip().split('\n')[0]
        for char in ['"', "'", '`', '*', '#']:
            enhanced_term = enhanced_term.replace(char, '')
            
        print(f"Enhanced search term: '{term}' → '{enhanced_term}'")
        return enhanced_term
    except Exception as e:
        print(f"Error enhancing search term with Gemini: {e}")
    
    # Return original term if enhancement fails
    return term 