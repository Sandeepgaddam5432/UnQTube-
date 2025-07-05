"""
Gemini TTS Module for UnQTube

This module integrates Google's Gemini TTS API for high-quality voice generation.
It provides functions for generating speech from text using the Gemini 2.5 API.
"""

import os
import requests
import json
import base64
import time
import traceback
from lib.config_utils import read_config_file

def get_gemini_key():
    """Get Gemini API key from environment variable or config file
    
    Returns:
        str: The Gemini API key or empty string if not found
    """
    # First check if key is in environment variable
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # If not found in env vars, try to get from config file
    if not api_key:
        try:
            api_key = read_config_file().get('gemini_api', '')
        except Exception as e:
            print(f"Warning: Could not read config file for Gemini API key: {e}")
            api_key = ''
            
    return api_key

def select_voice_parameters(text, content_type="default", segment_position=0.5):
    """Select optimal voice parameters based on content type and position
    
    Args:
        text (str): The text content to analyze
        content_type (str): Type of content (intro, main, conclusion, etc.)
        segment_position (float): Position in video (0-1 range)
        
    Returns:
        dict: Voice parameters including model and voice_config
    """
    # Default parameters
    params = {
        "model": "gemini-2.5-flash",
        "voice_config": "natural"
    }
    
    # Special cases based on content type
    if content_type == "intro":
        params["voice_config"] = "expressive"
        params["model"] = "gemini-2.5-pro"
    elif content_type == "conclusion" or content_type == "outro":
        params["voice_config"] = "expressive"
        params["model"] = "gemini-2.5-pro"
    elif "question" in text.lower() or "?" in text:
        params["voice_config"] = "casual"
    
    # Analyze text for emphasis or excitement
    if "!" in text or any(word in text.lower() for word in ["amazing", "incredible", "exciting"]):
        params["voice_config"] = "expressive"
    
    return params

def generate_gemini_tts(text, output_file, voice_config="natural", model="gemini-2.5-flash", max_retries=3):
    """Generate TTS audio using Gemini API
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Path to save audio file
        voice_config (str): Voice style (natural, casual, expressive)
        model (str): Gemini model to use (gemini-2.5-flash or gemini-2.5-pro)
        max_retries (int): Maximum number of retries on failure
        
    Returns:
        str: Path to the generated audio file
        
    Raises:
        ValueError: If Gemini API key is not found
        Exception: If API request fails after all retries
    """
    api_key = get_gemini_key()
    if not api_key:
        raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY environment variable "
                         "or add 'gemini_api = YOUR_API_KEY' to config.txt")
    
    # Determine model endpoint
    if "pro" in model:
        model_endpoint = "gemini-2.5-pro:generateContent" 
    else:
        model_endpoint = "gemini-2.5-flash:generateContent"
        
    # Create API URL
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    api_url = f"{base_url}/{model_endpoint}?key={api_key}"
    
    # Create payload
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Generate speech for the following text: {text}"
            }]
        }],
        "generationConfig": {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_config
                    }
                }
            }
        }
    }
    
    # Make API request with retries
    for attempt in range(max_retries):
        try:
            print(f"Gemini TTS attempt {attempt+1}/{max_retries}: Generating audio for {len(text)} chars")
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Extract audio data
                result = response.json()
                try:
                    audio_data = result["candidates"][0]["content"]["parts"][0]["audio_data"]
                    
                    # Decode and save audio
                    with open(output_file, "wb") as f:
                        f.write(base64.b64decode(audio_data))
                        
                    print(f"✅ Successfully generated audio: {output_file}")
                    return output_file
                except (KeyError, IndexError) as e:
                    print(f"Error extracting audio from Gemini response: {e}")
                    print(f"Response structure: {json.dumps(result, indent=2)[:500]}...")
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to extract audio data from Gemini response: {e}")
            elif response.status_code == 429:
                # Rate limit - wait and retry with exponential backoff
                wait_time = min(2 ** attempt, 60)  # Exponential backoff up to 60 seconds
                print(f"Rate limit hit. Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                error_message = f"Gemini API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data and "message" in error_data["error"]:
                        error_message = error_data["error"]["message"]
                except:
                    pass
                print(f"Gemini TTS API error: {error_message}")
                
                # If this was the last attempt, raise the exception
                if attempt == max_retries - 1:
                    raise Exception(f"Gemini TTS API error after {max_retries} attempts: {error_message}")
                
                # Wait before retrying
                wait_time = min(2 ** attempt, 30)
                time.sleep(wait_time)
        except requests.RequestException as e:
            print(f"Request error: {e}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to connect to Gemini API after {max_retries} attempts: {e}")
    
    # If we've exhausted all retries
    raise Exception(f"Failed to generate TTS using Gemini API after {max_retries} attempts")

def create_subtitle_file(output_file, text, duration=None):
    """Create a simple subtitle file for the generated audio
    
    Args:
        output_file (str): Path to save the subtitle file
        text (str): The text content
        duration (float): Optional estimated duration in seconds
        
    Returns:
        str: Path to the created subtitle file
    """
    # Calculate a simple subtitle file with basic timing
    if not duration:
        # Estimate duration based on character count (average reading speed)
        char_count = len(text)
        duration = max(1, char_count / 15)  # ~15 chars per second
    
    subtitle_file = os.path.splitext(output_file)[0] + ".vtt"
    
    try:
        with open(subtitle_file, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            f.write("00:00:00.000 --> " + format_timestamp(duration) + "\n")
            f.write(text + "\n")
            
        return subtitle_file
    except Exception as e:
        print(f"Error creating subtitle file: {e}")
        traceback.print_exc()
        return None

def format_timestamp(seconds):
    """Format seconds into VTT timestamp format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_remainder:06.3f}" 