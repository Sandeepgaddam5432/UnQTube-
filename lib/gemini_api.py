import os
import requests
import json
from lib.config_utils import read_config_file

def get_gemini_key():
    """Get Gemini API key from environment variable or config file"""
    # First check if key is in environment variable
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # If not found in env vars, try to get from config file
    if not api_key:
        try:
            api_key = read_config_file().get('gemini_api', '')
        except:
            api_key = ''
            
    return api_key

def get_gemini_model():
    """Get the selected Gemini model from config file or use default"""
    try:
        model = read_config_file().get('gemini_model', 'gemini-1.5-flash-latest')
        return model
    except:
        # Default to a stable model if not specified
        return 'gemini-1.5-flash-latest'

def generate_script_with_gemini(prompt, api_key=None):
    """Generate script using Gemini API
    
    Args:
        prompt: The prompt to send to Gemini
        api_key: Optional Gemini API key, if not provided will try to get from env/config
        
    Returns:
        The generated text from Gemini
    """
    if not api_key:
        api_key = get_gemini_key()
        
    if not api_key:
        raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY environment variable or add 'gemini_api = YOUR_API_KEY' to config.txt")
    
    # Get model from config or use default
    model_name = get_gemini_model()
    
    # Use stable v1 API instead of v1beta
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    params = {
        "key": api_key
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192
        }
    }
    
    response = requests.post(url, headers=headers, params=params, json=data)
    
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
        
    result = response.json()
    
    # Extract the generated text from the response
    try:
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return generated_text
    except (KeyError, IndexError):
        raise Exception(f"Unexpected Gemini API response format: {result}")

def enhance_media_search_with_gemini(script, segment_count=5, api_key=None):
    """Analyze a script and suggest better media search terms for each segment
    
    Args:
        script: The script to analyze
        segment_count: How many segments to divide the script into
        api_key: Optional Gemini API key
        
    Returns:
        A list of suggested search terms for visuals
    """
    if not api_key:
        api_key = get_gemini_key()
        
    prompt = f"""
    Analyze this script and suggest {segment_count} specific, vivid visual search terms that would 
    work well for finding stock footage or images to accompany each part of the script.
    
    SCRIPT:
    {script}
    
    OUTPUT FORMAT:
    Return only a JSON array of strings with {segment_count} search terms, one for each segment of the script.
    Example: ["aerial view of modern city skyline", "close-up of computer code on screen", ...]
    
    Make search terms very specific and visually descriptive. Include details about camera angles, 
    lighting, or composition when relevant.
    """
    
    response = generate_script_with_gemini(prompt, api_key)
    
    # Try to parse the response as JSON
    try:
        # Extract JSON if it's wrapped in text or code blocks
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].strip()
        else:
            json_text = response.strip()
            
        search_terms = json.loads(json_text)
        
        # Ensure we got a list of strings
        if not isinstance(search_terms, list):
            raise ValueError("Response is not a list")
            
        return search_terms
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, try to extract terms using simple text processing
        lines = response.strip().split('\n')
        search_terms = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Remove numbering, quotes, and other common formatting
                term = line.strip()
                for char in ['"', "'", ':', '-', '*', '•', '[', ']', '1.', '2.', '3.', '4.', '5.']:
                    term = term.replace(char, '').strip()
                if term:
                    search_terms.append(term)
                    
        # Limit to requested segment count
        return search_terms[:segment_count]

def generate_top10_list(title, genre="", language="english", api_key=None):
    """
    Generate a top 10 list along with search terms for each item
    
    Args:
        title: The main topic for the top 10 list
        genre: Optional genre/category for additional context
        language: The language to generate the script in
        api_key: Optional Gemini API key
        
    Returns:
        A dictionary containing:
        - The list of top 10 items
        - Full script text
        - Search terms for each item
    """
    if not api_key:
        api_key = get_gemini_key()
    
    # First, get the list of 10 items
    list_prompt = f"""
    I want to create a top 10 video about "{title}"{' related to ' + genre if genre else ''}.
    Generate a list of the 10 best items for this topic.
    
    Return ONLY a JSON array of strings with the 10 items, nothing else.
    Example format: ["Item 1", "Item 2", "Item 3", ...]
    
    Make sure each item is concise but descriptive.
    """
    
    try:
        response = generate_script_with_gemini(list_prompt, api_key)
        
        # Extract the JSON array
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].strip()
        else:
            json_text = response.strip()
            
        top10_items = json.loads(json_text)
        
        if not isinstance(top10_items, list) or len(top10_items) != 10:
            raise ValueError("Failed to generate a valid list of 10 items")
        
        # Now get detailed content for each item along with search terms
        result = {
            "items": top10_items,
            "segments": []
        }
        
        for i, item in enumerate(top10_items, 1):
            segment_prompt = f"""
            Create engaging script content for item #{i} in a top 10 video about "{title}": "{item}".
            
            Also provide 2 specific visual search terms that would work well for finding stock footage or images
            to accompany this segment.
            
            OUTPUT FORMAT:
            Return a JSON object with these fields:
            - "script": The script text explaining this item (about 3-4 sentences)
            - "search_terms": Array of 2 visual search terms (be specific with visual details)
            
            Example:
            {{
              "script": "Item explanation text here...",
              "search_terms": ["specific visual term 1", "specific visual term 2"]
            }}
            
            Language: {language}
            """
            
            segment_response = generate_script_with_gemini(segment_prompt, api_key)
            
            try:
                # Extract the JSON
                if "```json" in segment_response:
                    json_text = segment_response.split("```json")[1].split("```")[0].strip()
                elif "```" in segment_response:
                    json_text = segment_response.split("```")[1].strip()
                else:
                    json_text = segment_response.strip()
                    
                segment_data = json.loads(json_text)
                result["segments"].append(segment_data)
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if JSON parsing fails
                print(f"Warning: Could not parse JSON for item {i}. Using raw text.")
                result["segments"].append({
                    "script": segment_response.strip(),
                    "search_terms": [f"{item} {genre}", f"{item} {title}"]
                })
        
        return result
    
    except Exception as e:
        print(f"Error generating top 10 list with Gemini: {e}")
        raise

def generate_short_video_script(topic, duration_seconds=30, language="english", api_key=None):
    """
    Generate a short video script with scene descriptions, text overlays, and search terms
    
    Args:
        topic: The topic of the short video
        duration_seconds: Approximate duration in seconds
        language: Language to generate content in
        api_key: Optional Gemini API key
        
    Returns:
        A dictionary containing the structured script with scenes and search terms
    """
    if not api_key:
        api_key = get_gemini_key()
    
    # Calculate approximately how many scenes we need based on duration
    # Assuming average scene is ~5 seconds
    scene_count = max(3, min(10, duration_seconds // 5))
    
    prompt = f"""
    Create a script for a {duration_seconds}-second short video about "{topic}".
    
    Structure the output as a JSON object with an array of {scene_count} scenes.
    Each scene should include:
    1. A visual description for finding stock footage
    2. Text to display on screen as overlay/caption
    3. Specific search terms for finding the perfect stock footage
    
    OUTPUT FORMAT:
    {{
      "title": "Catchy title for the video",
      "scenes": [
        {{
          "visual_description": "Close-up of hands typing on keyboard",
          "text": "Did you know 85% of people...",
          "search_terms": ["close up fingers typing modern keyboard", "hands typing laptop keyboard"]
        }},
        ...additional scenes...
      ]
    }}
    
    Make each scene visually interesting, with specific details.
    Use {language} language for the text.
    """
    
    try:
        response = generate_script_with_gemini(prompt, api_key)
        
        # Extract the JSON
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].strip()
        else:
            json_text = response.strip()
            
        script_data = json.loads(json_text)
        return script_data
        
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails - create a simple structure from the raw text
        print("Warning: Could not parse JSON for short video script. Using fallback parsing.")
        
        # Very basic fallback parser for [visual] text: "text" format
        scenes = []
        lines = response.strip().split('\n')
        
        current_visual = None
        current_text = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('[') and ']' in line:
                # If we have a previous scene, save it
                if current_visual and current_text:
                    scenes.append({
                        "visual_description": current_visual,
                        "text": current_text,
                        "search_terms": [current_visual, f"{topic} {current_visual}"]
                    })
                
                # Start new scene
                current_visual = line.strip('[]')
                current_text = None
            elif "text:" in line.lower() or "text :" in line.lower():
                current_text = line.split(":", 1)[1].strip().strip('"')
                
        # Add the last scene if complete
        if current_visual and current_text:
            scenes.append({
                "visual_description": current_visual,
                "text": current_text,
                "search_terms": [current_visual, f"{topic} {current_visual}"]
            })
            
        return {
            "title": topic,
            "scenes": scenes
        }
    except Exception as e:
        print(f"Error generating short video script with Gemini: {e}")
        raise 