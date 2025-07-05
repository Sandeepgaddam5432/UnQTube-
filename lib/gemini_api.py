import os
import requests
import json
import time
import re
from lib.config_utils import read_config_file

def get_gemini_key():
    """Get Gemini API key from environment variable or config file"""
    # First check if key is in environment variable
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # If not found in env vars, try to get from config file
    if not api_key:
        try:
            api_key = read_config_file().get('gemini_api', '')
        except Exception as e:
            print(f"Warning: Could not read config file: {e}")
            api_key = ''
            
    return api_key

def list_available_gemini_models(api_key=None):
    """Fetch available Gemini models dynamically from the API
    
    Args:
        api_key: Optional Gemini API key, if not provided will try to get from env/config
        
    Returns:
        A dictionary with separate lists for text and TTS models
    """
    if not api_key:
        api_key = get_gemini_key()
        
    if not api_key:
        print("Warning: No Gemini API key found. Using default models.")
        return get_default_models()
    
    try:
        # Fetch models from the API
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        params = {"key": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            text_models = []
            tts_models = []
            
            for model in models_data.get("models", []):
                model_name = model.get("name", "")
                display_name = model.get("displayName", "")
                supported_methods = model.get("supportedGenerationMethods", [])
                
                # Filter for text generation models
                if "generateContent" in supported_methods:
                    # Extract just the model ID (remove 'models/' prefix)
                    model_id = model_name.replace("models/", "") if model_name.startswith("models/") else model_name
                    
                    # Categorize models
                    if "tts" in model_id.lower() or "text-to-speech" in display_name.lower():
                        tts_models.append(model_id)
                    elif any(keyword in model_id.lower() for keyword in ["gemini", "bison", "chat"]):
                        text_models.append(model_id)
            
            # Sort models by name for better organization
            text_models.sort()
            tts_models.sort()
            
            if text_models or tts_models:
                print(f"✅ Successfully fetched {len(text_models)} text and {len(tts_models)} TTS models from Gemini API")
                return {
                    "text_models": text_models,
                    "tts_models": tts_models,
                    "all_voices": get_default_tts_voices()  # Keep our curated voice list
                }
            else:
                print("Warning: No suitable models found in API response. Using defaults.")
                return get_default_models()
                
        else:
            print(f"Warning: Failed to fetch models from API (status {response.status_code}). Using defaults.")
            return get_default_models()
            
    except Exception as e:
        print(f"Warning: Error fetching models from API: {e}. Using defaults.")
        return get_default_models()

def get_default_models():
    """Return default model lists when API fetch fails
    
    Returns:
        A dictionary with default text and TTS models
    """
    return {
        "text_models": [
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro-latest",
            "gemini-2.5-flash-preview-04-17"
        ],
        "tts_models": [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-pro-preview-tts"
        ],
        "all_voices": get_default_tts_voices()
    }

def get_default_tts_voices():
    """Return the curated list of high-quality TTS voices
    
    Returns:
        List of available TTS voice names
    """
    return [
        'Kore', 'Puck', 'Charon', 'Leda', 'Orus', 'Aoede', 'Callirrhoe',
        'Iapetus', 'Umbriel', 'Algieba', 'Despina', 'Erinome', 'Algenib',
        'Rasalgethi', 'Laomedeia', 'Achernar', 'Alnilam', 'Schedar',
        'Gacrux', 'Pulcherrima', 'Achird', 'Zubenelgenubi', 'Vindemiatrix',
        'Sadachbia', 'Sadaltager', 'Sulafat', 'Zephyr', 'Fenrir',
        'Autonoe', 'Enceladus'
    ]

def is_beta_model(model_name):
    """Always returns True as we're exclusively using gemini-2.5-flash-preview-04-17
    which requires the v1beta API endpoint
    
    Args:
        model_name: Not used but kept for compatibility
        
    Returns:
        Always True
    """
    return True

def get_gemini_model():
    """Always returns the fixed model name
    
    Returns:
        The string "models/gemini-2.5-flash-preview-04-17"
    """
    # Always return our fixed model
    return 'models/gemini-2.5-flash-preview-04-17'

def generate_script_with_gemini(prompt, api_key=None, max_retries=3):
    """Generate script using Gemini API with the fixed model gemini-2.5-flash-preview-04-17
    
    Args:
        prompt: The prompt to send to Gemini
        api_key: Optional Gemini API key, if not provided will try to get from env/config
        max_retries: Maximum number of retries on failure
        
    Returns:
        The generated text from Gemini
    """
    if not api_key:
        api_key = get_gemini_key()
        
    if not api_key:
        raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY environment variable or add 'gemini_api = YOUR_API_KEY' to config.txt")
    
    # Use our fixed model
    model_name = get_gemini_model()
    model_id = "gemini-2.5-flash-preview-04-17"  # Fixed model ID
    
    # Always use v1beta API for this model
    api_version = "v1beta"
    
    # Use the correct API endpoint format with appropriate version
    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_id}:generateContent"
    print(f"Using API endpoint: {url}")
    
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
    
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(url, headers=headers, params=params, json=data)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return generated_text
                except (KeyError, IndexError) as e:
                    print(f"Error parsing Gemini response: {e}")
                    print(f"Response structure: {json.dumps(result, indent=2)[:500]}...")
                    raise Exception(f"Unexpected Gemini API response format: {e}")
            elif response.status_code == 429:
                # Rate limit - wait and retry with exponential backoff
                wait_time = min(2 ** retries, 60)  # Exponential backoff up to 60 seconds
                print(f"Rate limit hit with model gemini-2.5-flash-preview-04-17. Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            elif response.status_code == 400:
                error_message = "Invalid request"
                try:
                    error_data = response.json()
                    if "error" in error_data and "message" in error_data["error"]:
                        error_message = error_data["error"]["message"]
                except:
                    pass
                print(f"Gemini API error with model gemini-2.5-flash-preview-04-17 (400): {error_message}")
                print(f"Attempted URL: {url}")
                
                # For bad requests, don't retry - likely a problem with the prompt
                raise Exception(f"Gemini API error (400) with model gemini-2.5-flash-preview-04-17: {error_message}")
            else:
                print(f"Gemini API error with model gemini-2.5-flash-preview-04-17: {response.status_code} - {response.text}")
                # For other errors, retry
        except requests.RequestException as e:
            print(f"Request error with model gemini-2.5-flash-preview-04-17: {e}")
            if retries < max_retries - 1:
                wait_time = min(2 ** retries, 60)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to connect to Gemini API with model gemini-2.5-flash-preview-04-17 after {max_retries} attempts: {e}")
        
        retries += 1
    
    # If we've exhausted all retries
    raise Exception(f"Failed to get a valid response from Gemini API with model gemini-2.5-flash-preview-04-17 after {max_retries} attempts. The model may be rate-limited or experiencing issues.")

def enhance_media_search_with_gemini(script, segment_count=5, api_key=None, max_retries=2):
    """Analyze a script and suggest better media search terms for each segment
    
    Args:
        script: The script to analyze
        segment_count: How many segments to divide the script into
        api_key: Optional Gemini API key
        max_retries: Maximum number of retries on failure
        
    Returns:
        A list of suggested search terms for visuals
    """
    if not api_key:
        api_key = get_gemini_key()
        
    # If script is too long, truncate it to avoid token limits
    max_script_length = 15000
    if len(script) > max_script_length:
        script = script[:max_script_length] + "..."
        print(f"Warning: Script truncated to {max_script_length} characters for media search term generation")
        
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
    
    for attempt in range(max_retries):
        try:
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
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"Failed to parse JSON response ({e}). Retrying...")
                    continue
                    
                # If parsing fails, try to extract terms using simple text processing
                print(f"JSON parsing failed: {e}. Attempting text-based extraction...")
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
                
                # If we found some terms, use them
                if search_terms:
                    print(f"Extracted {len(search_terms)} search terms through text parsing")
                    return search_terms[:segment_count]
                
                # Last resort: generate generic search terms
                print("Could not extract search terms. Using generic visuals...")
                return [
                    "professional high quality visual",
                    "detailed clear image",
                    "cinematic shot",
                    "high resolution photograph",
                    "professional stock footage"
                ][:segment_count]
                    
        except Exception as e:
            print(f"Error in search term generation (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print("Using fallback generic search terms...")
                return [
                    "professional high quality visual",
                    "detailed clear image", 
                    "cinematic shot",
                    "high resolution photograph",
                    "professional stock footage"
                ][:segment_count]
            # Sleep before retry
            time.sleep(2)

def generate_top10_list(title, genre="", language="english", api_key=None, max_retries=2):
    """
    Generate a top 10 list along with search terms for each item
    
    Args:
        title: The main topic for the top 10 list
        genre: Optional genre/category for additional context
        language: The language to generate the script in
        api_key: Optional Gemini API key
        max_retries: Maximum number of retries on failure
        
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
    
    top10_items = None
    for attempt in range(max_retries):
        try:
            response = generate_script_with_gemini(list_prompt, api_key)
            
            # Extract the JSON array
            try:
                if "```json" in response:
                    json_text = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_text = response.split("```")[1].strip()
                else:
                    json_text = response.strip()
                    
                top10_items = json.loads(json_text)
                
                if not isinstance(top10_items, list):
                    raise ValueError("Response is not a list")
                
                # Ensure we have exactly 10 items
                if len(top10_items) > 10:
                    top10_items = top10_items[:10]
                elif len(top10_items) < 10:
                    # If we have fewer than 10 items, pad the list with generic items
                    missing = 10 - len(top10_items)
                    print(f"Warning: Only {len(top10_items)} items generated. Adding {missing} generic items.")
                    for i in range(missing):
                        top10_items.append(f"Item #{len(top10_items) + 1} for {title}")
                
                break  # Success, exit the retry loop
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON response for top 10 list: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying (attempt {attempt+1}/{max_retries})...")
                    time.sleep(1)
                else:
                    # Create a fallback list of 10 generic items
                    print("Using generic fallback list of items...")
                    top10_items = [f"Item #{i+1} for {title}" for i in range(10)]
        except Exception as e:
            print(f"Error generating top 10 list: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(2)
            else:
                # Create a fallback list of 10 generic items
                print("Using generic fallback list of items...")
                top10_items = [f"Item #{i+1} for {title}" for i in range(10)]
    
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
        
        try:
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
                
                # Ensure required fields are present
                if "script" not in segment_data:
                    segment_data["script"] = f"Item {i}: {item} is an excellent example of {title}."
                if "search_terms" not in segment_data or not segment_data["search_terms"]:
                    segment_data["search_terms"] = [f"{item} {genre}", f"{item} {title}"]
                
                result["segments"].append(segment_data)
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if JSON parsing fails
                print(f"Warning: Could not parse JSON for item {i}. Using raw text. Error: {e}")
                result["segments"].append({
                    "script": segment_response.strip() or f"Item {i}: {item} is an excellent example of {title}.",
                    "search_terms": [f"{item} {genre}", f"{item} {title}"]
                })
        except Exception as e:
            print(f"Error generating content for item {i}: {e}")
            # Use fallback content
            result["segments"].append({
                "script": f"Item {i}: {item} is an excellent example of {title}.",
                "search_terms": [f"{item} {genre}", f"{item} {title}"]
            })
    
    return result

def generate_short_video_script(topic, duration_seconds=30, language="english", api_key=None, max_retries=2):
    """
    Generate a short video script with scene descriptions, text overlays, and search terms
    
    Args:
        topic: The topic of the short video
        duration_seconds: Approximate duration in seconds
        language: Language to generate content in
        api_key: Optional Gemini API key
        max_retries: Maximum number of retries on failure
        
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
    
    for attempt in range(max_retries):
        try:
            response = generate_script_with_gemini(prompt, api_key)
            
            # Extract the JSON
            try:
                if "```json" in response:
                    json_text = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_text = response.split("```")[1].strip()
                else:
                    json_text = response.strip()
                    
                script_data = json.loads(json_text)
                
                # Validate and ensure required fields are present
                if "scenes" not in script_data or not script_data["scenes"]:
                    raise ValueError("No scenes found in script data")
                
                if "title" not in script_data:
                    script_data["title"] = f"Short video about {topic}"
                    
                # Ensure each scene has the required fields
                for i, scene in enumerate(script_data["scenes"]):
                    if "visual_description" not in scene:
                        scene["visual_description"] = f"Scene {i+1} for {topic}"
                    if "text" not in scene:
                        scene["text"] = f"Scene {i+1} about {topic}"
                    if "search_terms" not in scene or not scene["search_terms"]:
                        scene["search_terms"] = [scene["visual_description"], f"{topic} visual"]
                
                return script_data
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON response for short video: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying (attempt {attempt+1}/{max_retries})...")
                    time.sleep(1)
                else:
                    # Fallback if JSON parsing fails - create a simple structure from the raw text
                    print("Using fallback parsing for short video script.")
                    return _parse_short_video_fallback(response, topic, scene_count)
        except Exception as e:
            print(f"Error generating short video script: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(2)
            else:
                # Create a fallback script
                print("Creating fallback short video script...")
                return _create_fallback_short_video_script(topic, scene_count)
    
    # This should not be reached due to the else clauses above, but just in case
    return _create_fallback_short_video_script(topic, scene_count)

def _parse_short_video_fallback(response, topic, scene_count=5):
    """Parse a non-JSON short video script response"""
    try:
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
        
        # If we couldn't extract any scenes, create fallback
        if not scenes:
            return _create_fallback_short_video_script(topic, scene_count)
            
        return {
            "title": topic,
            "scenes": scenes
        }
    except Exception as e:
        print(f"Error in fallback parsing: {e}")
        return _create_fallback_short_video_script(topic, scene_count)

def _create_fallback_short_video_script(topic, scene_count=5):
    """Create a simple fallback script when all else fails"""
    scenes = []
    
    # Generic scene descriptions for different topics
    generic_scenes = [
        {
            "visual_description": "Close-up shot of the main subject",
            "text": f"Discover the fascinating world of {topic}",
            "search_terms": [f"close-up {topic}", "detailed view"]
        },
        {
            "visual_description": "Wide angle establishing shot",
            "text": f"What makes {topic} so special?",
            "search_terms": [f"wide angle {topic}", "panoramic view"]
        },
        {
            "visual_description": "Person demonstrating the concept",
            "text": f"Here's what you need to know about {topic}",
            "search_terms": ["person explaining", "demonstration"]
        },
        {
            "visual_description": "Slow motion detail shot",
            "text": f"The details that make {topic} unique",
            "search_terms": ["slow motion details", "cinematic close up"]
        },
        {
            "visual_description": "Before and after comparison",
            "text": f"See the transformation with {topic}",
            "search_terms": ["before and after", "comparison shot"]
        },
        {
            "visual_description": "Overhead view of the scene",
            "text": f"A different perspective on {topic}",
            "search_terms": ["overhead view", "aerial perspective"]
        }
    ]
    
    # Use the generic scenes to fill our scene count
    for i in range(min(scene_count, len(generic_scenes))):
        scenes.append(generic_scenes[i])
    
    # If we need more scenes than we have in our template, duplicate with variations
    while len(scenes) < scene_count:
        base_scene = generic_scenes[len(scenes) % len(generic_scenes)]
        scenes.append({
            "visual_description": base_scene["visual_description"],
            "text": f"Another interesting aspect of {topic}",
            "search_terms": base_scene["search_terms"]
        })
    
    return {
        "title": f"Short video about {topic}",
        "scenes": scenes
    }

def generate_complete_top10_content(title, genre="", language="english", api_key=None, max_retries=2):
    """
    Generate a complete top 10 video script including all content in a single API call
    
    Args:
        title: The main topic for the top 10 list
        genre: Optional genre/category for additional context
        language: The language to generate the script in
        api_key: Optional Gemini API key
        max_retries: Maximum number of retries on failure
        
    Returns:
        A dictionary containing:
        - intro: Intro text
        - items: List of the 10 items
        - segments: Array of segment data objects with script and search_terms
        - outro: Outro text
    """
    if not api_key:
        api_key = get_gemini_key()
    
    # Prepare a comprehensive prompt to get all content at once
    prompt = f"""
    I need a complete script for a top 10 video about "{title}"{' related to ' + genre if genre else ''}.
    
    Please generate all the following content at once in a single structured JSON response:
    
    1. An intro text that introduces the topic
    2. A list of the 10 best items for this topic
    3. Detailed content for each of the 10 items
    4. An outro text thanking viewers and asking them to like and subscribe
    
    OUTPUT FORMAT:
    Return the content as a JSON object with these fields:
    - "intro": An engaging introduction text (3-4 sentences)
    - "items": Array of 10 item titles
    - "segments": Array of 10 objects (one per item) with:
      - "script": The script text explaining this item (3-4 sentences)
      - "search_terms": Array of 2-3 visual search terms for finding imagery/video
    - "outro": A brief conclusion thanking viewers (1-2 sentences)
    
    Example structure (simplified):
    {{
      "intro": "Welcome to our top 10 video about...",
      "items": ["First item", "Second item", ...],
      "segments": [
        {{
          "script": "Our first item is...",
          "search_terms": ["term1", "term2"]
        }},
        ...
      ],
      "outro": "Thanks for watching..."
    }}
    
    Make each item genuinely informative with interesting facts.
    For search terms, be specific and descriptive for better visuals.
    Language: {language}
    """
    
    for attempt in range(max_retries):
        try:
            print(f"Generating complete top 10 content for '{title}' in a single API call...")
            response = generate_script_with_gemini(prompt, api_key)
            
            try:
                # Extract the JSON response
                if "```json" in response:
                    json_text = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_text = response.split("```")[1].strip()
                else:
                    json_text = response.strip()
                    
                content_data = json.loads(json_text)
                
                # Validate required fields
                if "intro" not in content_data:
                    content_data["intro"] = f"Welcome to our top ten video about {title}. Today, we're going to explore the most fascinating aspects of this topic. If you enjoy this content, please like and subscribe."
                
                if "items" not in content_data or not content_data["items"] or len(content_data["items"]) < 10:
                    print("Warning: Incomplete or missing items list in response")
                    # Create or pad items list
                    if "items" not in content_data or not content_data["items"]:
                        content_data["items"] = [f"Item {i+1} for {title}" for i in range(10)]
                    elif len(content_data["items"]) < 10:
                        current_length = len(content_data["items"])
                        content_data["items"].extend([f"Item {current_length + i + 1} for {title}" for i in range(10 - current_length)])
                
                if "segments" not in content_data or not content_data["segments"] or len(content_data["segments"]) < 10:
                    print("Warning: Incomplete or missing segments in response")
                    # Create or pad segments
                    if "segments" not in content_data or not content_data["segments"]:
                        content_data["segments"] = []
                    
                    # Generate segments for each item
                    items = content_data["items"]
                    for i in range(len(content_data["segments"]), 10):
                        item_text = items[i] if i < len(items) else f"Item {i+1}"
                        content_data["segments"].append({
                            "script": f"Number {i+1} on our list is {item_text}. This is an excellent example of {title} that stands out for its unique qualities.",
                            "search_terms": [f"{item_text} {genre}", f"{item_text} {title}"]
                        })
                
                if "outro" not in content_data:
                    content_data["outro"] = f"Thanks for watching our video about {title}. If you enjoyed it, please hit the like button and subscribe to our channel for more content like this!"
                
                print(f"✓ Successfully generated complete top 10 content in a single API call")
                return content_data
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON response: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying... (attempt {attempt+1}/{max_retries})")
                    time.sleep(2)
                else:
                    # Attempt to extract useful data from text response
                    print("Attempting to extract content from non-JSON response...")
                    return _extract_top10_content_from_text(response, title, genre)
        except Exception as e:
            print(f"Error generating complete top 10 content: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying... (attempt {attempt+1}/{max_retries})")
                time.sleep(2)
            else:
                # Create fallback content
                return _create_fallback_top10_content(title, genre)
    
    # This should not be reached due to the else clauses above, but just in case
    return _create_fallback_top10_content(title, genre)

def _extract_top10_content_from_text(response, title, genre):
    """Extract content from a non-JSON text response"""
    try:
        # Initialize with defaults
        content = {
            "intro": f"Welcome to our top ten video about {title}.",
            "items": [f"Item {i+1}" for i in range(10)],
            "segments": [],
            "outro": f"Thanks for watching our video about {title}. If you enjoyed it, please like and subscribe!"
        }
        
        # Try to find intro
        intro_match = re.search(r'"intro":\s*"([^"]+)"', response)
        if intro_match:
            content["intro"] = intro_match.group(1)
            
        # Try to find items
        items_section = re.search(r'"items":\s*\[(.*?)\]', response, re.DOTALL)
        if items_section:
            items_text = items_section.group(1)
            items = re.findall(r'"([^"]+)"', items_text)
            if items and len(items) > 0:
                content["items"] = items[:10]  # Take up to 10 items
                if len(items) < 10:
                    content["items"].extend([f"Item {len(items) + i + 1}" for i in range(10 - len(items))])
        
        # Try to find segments
        segments_section = re.search(r'"segments":\s*\[(.*?)\]', response, re.DOTALL)
        if segments_section:
            segments_text = segments_section.group(1)
            script_patterns = re.findall(r'"script":\s*"([^"]+)"', segments_text)
            
            # Build segments
            for i, script in enumerate(script_patterns[:10]):
                item = content["items"][i] if i < len(content["items"]) else f"Item {i+1}"
                content["segments"].append({
                    "script": script,
                    "search_terms": [f"{item} {genre}", f"{item} {title}"]
                })
        
        # Fill any missing segments
        for i in range(len(content["segments"]), 10):
            item = content["items"][i] if i < len(content["items"]) else f"Item {i+1}"
            content["segments"].append({
                "script": f"Number {i+1} on our list is {item}. This is an excellent example of {title}.",
                "search_terms": [f"{item} {genre}", f"{item} {title}"]
            })
            
        # Try to find outro
        outro_match = re.search(r'"outro":\s*"([^"]+)"', response)
        if outro_match:
            content["outro"] = outro_match.group(1)
            
        return content
    except Exception as e:
        print(f"Error extracting content from text: {e}")
        return _create_fallback_top10_content(title, genre)
    
def _create_fallback_top10_content(title, genre):
    """Create fallback content when all else fails"""
    items = [f"Item {i+1} for {title}" for i in range(10)]
    segments = []
    
    for i, item in enumerate(items):
        segments.append({
            "script": f"Number {i+1} on our list is {item}. This is an excellent example of {title} that stands out for its unique qualities.",
            "search_terms": [f"{item} {genre}", f"{item} {title}"]
        })
    
    return {
        "intro": f"Welcome to our top ten video about {title}. Today, we're going to explore the most fascinating aspects of this topic. If you enjoy this content, please like and subscribe.",
        "items": items,
        "segments": segments,
        "outro": f"Thanks for watching our video about {title}. If you enjoyed it, please hit the like button and subscribe to our channel for more content like this!"
    } 