"""
API Validation Module for UnQTube

This module provides validation functions for API keys and service availability.
"""

import requests
import asyncio
import json
from typing import Dict, Tuple, Optional

def validate_gemini_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Google Gemini API key by making a test request
    
    Args:
        api_key (str): The Gemini API key to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not api_key or len(api_key.strip()) < 10:
        return False, "API key is too short or empty"
    
    try:
        # Test the API key by fetching available models
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        params = {"key": api_key.strip()}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            model_count = len(models_data.get("models", []))
            return True, f"✅ Valid API key with access to {model_count} models"
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Invalid API key format")
                return False, f"❌ Invalid API key: {error_message}"
            except:
                return False, "❌ Invalid API key format"
        elif response.status_code == 403:
            return False, "❌ API key is valid but access is forbidden. Check your API permissions."
        elif response.status_code == 429:
            return False, "⚠️ API key is valid but rate limited. Try again in a few minutes."
        else:
            return False, f"❌ API validation failed with status {response.status_code}"
            
    except requests.RequestException as e:
        return False, f"❌ Network error during validation: {str(e)}"
    except Exception as e:
        return False, f"❌ Unexpected error during validation: {str(e)}"

def validate_pexels_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Pexels API key by making a test request
    
    Args:
        api_key (str): The Pexels API key to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not api_key or len(api_key.strip()) < 10:
        return False, "API key is too short or empty"
    
    try:
        # Test the API key with a minimal search request
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key.strip()}
        params = {"query": "test", "per_page": 1}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return True, "✅ Valid Pexels API key"
        elif response.status_code == 401:
            return False, "❌ Invalid Pexels API key"
        elif response.status_code == 429:
            return False, "⚠️ Pexels API key is valid but rate limited"
        else:
            return False, f"❌ Pexels API validation failed with status {response.status_code}"
            
    except requests.RequestException as e:
        return False, f"❌ Network error during Pexels validation: {str(e)}"
    except Exception as e:
        return False, f"❌ Unexpected error during Pexels validation: {str(e)}"

def check_system_requirements() -> Dict[str, Tuple[bool, str]]:
    """
    Check system requirements for video generation
    
    Returns:
        Dict[str, Tuple[bool, str]]: Dictionary of requirement checks
    """
    requirements = {}
    
    # Check Python version
    import sys
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        requirements["python"] = (True, f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        requirements["python"] = (False, f"❌ Python {python_version.major}.{python_version.minor} (requires 3.8+)")
    
    # Check required packages
    required_packages = [
        "requests", "asyncio", "json", "tkinter", 
        "moviepy", "numpy", "PIL", "pydub"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            requirements[package] = (True, f"✅ {package} installed")
        except ImportError:
            requirements[package] = (False, f"❌ {package} not installed")
    
    # Check FFmpeg availability
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            requirements["ffmpeg"] = (True, "✅ FFmpeg available")
        else:
            requirements["ffmpeg"] = (False, "❌ FFmpeg not working properly")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        requirements["ffmpeg"] = (False, "❌ FFmpeg not found")
    except Exception:
        requirements["ffmpeg"] = (False, "❌ FFmpeg check failed")
    
    # Check disk space (basic check)
    try:
        import shutil
        free_space_gb = shutil.disk_usage(".").free / (1024**3)
        if free_space_gb > 5:
            requirements["disk_space"] = (True, f"✅ {free_space_gb:.1f}GB available")
        else:
            requirements["disk_space"] = (False, f"⚠️ Only {free_space_gb:.1f}GB available (recommend 5GB+)")
    except Exception:
        requirements["disk_space"] = (False, "❌ Could not check disk space")
    
    return requirements

def validate_video_settings(topic: str, duration: str, language: str) -> Tuple[bool, str]:
    """
    Validate video generation settings
    
    Args:
        topic (str): Video topic
        duration (str): Video duration
        language (str): Video language
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    # Validate topic
    if not topic or len(topic.strip()) < 3:
        return False, "Topic must be at least 3 characters long"
    
    if len(topic.strip()) > 200:
        return False, "Topic is too long (max 200 characters)"
    
    # Validate duration
    try:
        duration_num = float(duration)
        if duration_num <= 0:
            return False, "Duration must be greater than 0"
        if duration_num > 60:  # For long videos
            return False, "Duration too long (max 60 minutes for stability)"
    except ValueError:
        return False, "Duration must be a valid number"
    
    # Validate language
    supported_languages = [
        "english", "hindi", "bengali", "telugu", "marathi", "tamil", "urdu",
        "gujarati", "kannada", "malayalam", "punjabi", "assamese", "odia",
        "persian", "arabic", "vietnamese", "spanish", "french", "german", 
        "italian", "japanese", "korean", "portuguese", "russian", "turkish"
    ]
    
    if language.lower() not in supported_languages:
        return False, f"Language '{language}' not supported"
    
    return True, "✅ Video settings are valid"

async def quick_connectivity_check() -> Dict[str, bool]:
    """
    Quick check of internet connectivity to required services
    
    Returns:
        Dict[str, bool]: Service connectivity status
    """
    services = {
        "google_ai": "https://generativelanguage.googleapis.com",
        "pexels": "https://api.pexels.com",
        "general_internet": "https://httpbin.org/get"
    }
    
    connectivity = {}
    
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            connectivity[service] = response.status_code in [200, 403]  # 403 is OK for API endpoints without auth
        except:
            connectivity[service] = False
    
    return connectivity

def generate_system_report() -> str:
    """
    Generate a comprehensive system report for troubleshooting
    
    Returns:
        str: Formatted system report
    """
    report = ["🔍 UnQTube System Report", "=" * 50, ""]
    
    # System requirements
    requirements = check_system_requirements()
    report.append("📋 System Requirements:")
    for req, (status, message) in requirements.items():
        report.append(f"  {message}")
    report.append("")
    
    # Connectivity check
    try:
        import asyncio
        connectivity = asyncio.run(quick_connectivity_check())
        report.append("🌐 Connectivity Status:")
        for service, status in connectivity.items():
            status_icon = "✅" if status else "❌"
            report.append(f"  {status_icon} {service.replace('_', ' ').title()}")
        report.append("")
    except Exception as e:
        report.append(f"🌐 Connectivity check failed: {e}")
        report.append("")
    
    # Python environment
    import sys, platform
    report.append("🐍 Python Environment:")
    report.append(f"  Python Version: {sys.version}")
    report.append(f"  Platform: {platform.system()} {platform.release()}")
    report.append(f"  Architecture: {platform.machine()}")
    report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    # Test the validation functions
    print(generate_system_report())