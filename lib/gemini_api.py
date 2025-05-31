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