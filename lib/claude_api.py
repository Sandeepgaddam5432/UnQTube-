"""
Claude API Module for UnQTube

This module integrates Anthropic's Claude AI for content generation,
providing an alternative to the Gemini API.
"""

import os
import json
import time
import requests
import traceback
from lib.config_utils import read_config_file, intelligent_rate_limit_handling

def get_claude_key():
    """Get Claude API key from environment variable or config file
    
    Returns:
        str: The Claude API key or empty string if not found
    """
    # First check if key is in environment variable
    api_key = os.environ.get('CLAUDE_API_KEY')
    
    # If not found in env vars, try to get from config file
    if not api_key:
        try:
            api_key = read_config_file().get('claude_api', '')
        except Exception as e:
            print(f"Warning: Could not read config file for Claude API key: {e}")
            api_key = ''
            
    return api_key

async def generate_script_with_claude(prompt, model="claude-3-haiku-20240307", max_retries=3):
    """Generate content using Claude API
    
    Args:
        prompt (str): The prompt to send to Claude
        model (str): Claude model to use (claude-3-haiku, claude-3-sonnet, claude-3-opus)
        max_retries (int): Maximum number of retries on failure
        
    Returns:
        str: Generated content from Claude
        
    Raises:
        ValueError: If Claude API key is not found
        Exception: If API request fails after all retries
    """
    api_key = get_claude_key()
    if not api_key:
        raise ValueError("Claude API key not found. Please set CLAUDE_API_KEY environment variable "
                         "or add 'claude_api = YOUR_API_KEY' to config.txt")
    
    # API endpoint
    api_url = "https://api.anthropic.com/v1/messages"
    
    # Headers
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Payload
    payload = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # Make API request with retries and intelligent rate limiting
    for attempt in range(max_retries):
        try:
            print(f"Claude API attempt {attempt+1}/{max_retries}: Generating content")
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Extract content from response
                result = response.json()
                try:
                    content = result["content"][0]["text"]
                    print(f"✅ Successfully generated content with Claude ({len(content)} chars)")
                    return content
                except (KeyError, IndexError) as e:
                    print(f"Error extracting content from Claude response: {e}")
                    print(f"Response structure: {json.dumps(result, indent=2)[:500]}...")
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to extract content from Claude response: {e}")
            elif response.status_code == 429:
                # Rate limit - use intelligent rate limit handling
                retry_after = int(response.headers.get('retry-after', 60))
                print(f"Rate limit hit. Waiting {retry_after} seconds before retrying...")
                intelligent_rate_limit_handling(retry_after)
            else:
                error_message = f"Claude API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data and "message" in error_data["error"]:
                        error_message = error_data["error"]["message"]
                except:
                    pass
                print(f"Claude API error: {error_message}")
                
                # If this was the last attempt, raise the exception
                if attempt == max_retries - 1:
                    raise Exception(f"Claude API error after {max_retries} attempts: {error_message}")
                
                # Wait before retrying with exponential backoff
                wait_time = min(2 ** attempt, 30)
                time.sleep(wait_time)
        except requests.RequestException as e:
            print(f"Request error: {e}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to connect to Claude API after {max_retries} attempts: {e}")
    
    # If we've exhausted all retries
    raise Exception(f"Failed to generate content using Claude API after {max_retries} attempts")

def is_claude_available():
    """Check if Claude API is available and configured
    
    Returns:
        bool: True if Claude API is available, False otherwise
    """
    try:
        api_key = get_claude_key()
        return bool(api_key)
    except:
        return False 