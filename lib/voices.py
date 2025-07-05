import asyncio
import random
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
import edge_tts
from edge_tts import VoicesManager
from lib.config_utils import read_config_file

def generate_voice(text, outputfile, lang):
    """Generate voice using TTS system
    
    This function first attempts to use Gemini TTS if configured,
    and falls back to edge-tts if Gemini is unavailable or fails.
    
    Args:
        text (str): Text to convert to speech
        outputfile (str): Path to save the audio file
        lang (str): Language code for the voice
        
    Returns:
        str: Path to the generated audio file
    """
    try:
        # First attempt with Gemini TTS if configured to use it
        use_gemini = read_config_file().get('use_gemini', 'no').lower() in ['yes', 'true', '1']
        if use_gemini:
            try:
                # Import here to avoid circular imports
                from lib.gemini_tts import generate_gemini_tts, select_voice_parameters, create_subtitle_file
                
                # Determine voice parameters based on text content
                content_type = "default"
                if "introduction" in text.lower() or "welcome" in text.lower():
                    content_type = "intro"
                elif "conclusion" in text.lower() or "thank you" in text.lower():
                    content_type = "outro"
                    
                voice_params = select_voice_parameters(text, content_type=content_type)
                
                # Get user-selected TTS model if specified
                config = read_config_file()
                tts_model = config.get('tts_model', voice_params.get("model", "gemini-2.5-flash-preview-tts"))
                voice_name = config.get('tts_voice', voice_params.get("voice_name", "Kore"))
                
                # Generate audio with Gemini TTS
                print(f"Using Gemini TTS for voice generation ({tts_model}, {voice_name})")
                generate_gemini_tts(
                    text, 
                    outputfile, 
                    voice_name=voice_name,
                    model=tts_model
                )
                
                # Create subtitle file for compatibility with video editor
                create_subtitle_file(outputfile, text)
                
                print(f"Gemini TTS generated: {outputfile}")
                return outputfile
            except Exception as e:
                print(f"Gemini TTS failed: {e}")
                print("Falling back to edge-tts...")
    except Exception as e:
        print(f"Error checking for Gemini TTS: {e}")
        print("Proceeding with edge-tts...")
        
    # Fall back to original edge-tts implementation
    return _legacy_generate_voice(text, outputfile, lang)

def _legacy_generate_voice(text, outputfile, lang):
    """Legacy voice generation using edge-tts
    
    This is the original implementation, kept as a fallback
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Run the async function directly in this thread
        result = loop.run_until_complete(async_generate_voice(text, outputfile, lang))
        
        # Ensure all pending tasks are completed
        pending = asyncio.all_tasks(loop)
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
    finally:
        # Close the loop properly
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    if not os.path.exists(outputfile):
        print("An error happened during edge_tts audio generation, no output audio generated")
        raise Exception("An error happened during edge_tts audio generation, no output audio generated")

    return outputfile

async def async_generate_voice(text, outputfile, lang):
    """Generate voice audio using edge-tts
    
    This function uses edge-tts to generate speech audio from text.
    It works with edge-tts 7.0.2 by using the correct subtitle generation method.
    
    Args:
        text: The text to convert to speech
        outputfile: Path to save the audio file
        lang: Language code for the voice
    
    Returns:
        Path to the generated audio file
    """
    try:
        # Create voice manager and select appropriate voice
        voices = await VoicesManager.create()
        if (lang == "en"):
            voice = voices.find(Locale="en-US")
        else:
            voice = voices.find(Language=lang)
            
        # Get voice based on multi_speaker setting
        multi = read_config_file().get("multi_speaker", "no").lower()
        if multi in ["yes", "true", "1"]: 
            speaker = random.choice(voice)["Name"]
        else:      
            try:
                speaker = read_config_file("temp.txt")["speaker"]
            except:
                speaker = random.choice(voice)["Name"]
                with open("temp.txt", "w") as file:
                    file.write("speaker = " + speaker)
        
        # Create a single Communicate instance
        communicate = edge_tts.Communicate(text, speaker)
        
        # Generate subtitle file path
        subtitle_file = os.path.splitext(outputfile)[0] + ".vtt"
        
        try:
            # First try the built-in method to generate both audio and subtitles at once
            # This would work if the version of edge-tts supports it
            await communicate.save(outputfile, subtitle_file)
            print(f"Successfully generated audio and subtitles: {outputfile}, {subtitle_file}")
            return outputfile
        except (AttributeError, TypeError) as e:
            # Older versions of edge-tts don't have the subtitle parameter in save()
            # Fall back to separate audio and subtitle generation
            print(f"Using alternative subtitle generation method (Reason: {e})...")
            
            # Save audio
            await communicate.save(outputfile)
            print(f"Successfully generated audio: {outputfile}")
            
            # Create a new Communicate instance for subtitle generation
            subtitle_communicate = edge_tts.Communicate(text, speaker)
            
            # Create a temporary file for subtitles
            temp_subtitle_file = f"{subtitle_file}.temp"
            
            try:
                # Try using the add_text_file method if available (later versions of edge-tts)
                if hasattr(subtitle_communicate, "add_text_file"):
                    await subtitle_communicate.add_text_file(temp_subtitle_file)
                    
                    # Convert from SSML to VTT if needed
                    with open(temp_subtitle_file, "r", encoding="utf-8") as f_read:
                        content = f_read.read()
                    
                    with open(subtitle_file, "w", encoding="utf-8") as f_write:
                        f_write.write("WEBVTT\n\n")
                        # Basic parsing of SSML to VTT format
                        import re
                        matches = re.findall(r'begin="([^"]+)".*end="([^"]+)".*>([^<]+)<', content)
                        for begin, end, text in matches:
                            f_write.write(f"{begin} --> {end}\n")
                            f_write.write(f"{text.strip()}\n\n")
                else:
                    # Last resort: Manual collection from stream
                    with open(subtitle_file, 'w', encoding='utf-8') as f:
                        f.write("WEBVTT\n\n")
                        
                        # Process subtitles in memory first to avoid consuming the stream
                        subtitle_data = []
                        async for chunk in subtitle_communicate.stream():
                            if chunk["type"] == "WordBoundary":
                                subtitle_data.append(chunk)
                        
                        # Write all subtitle data at once
                        for chunk in subtitle_data:
                            start_time = format_timestamp(chunk["offset"] / 10000000)
                            end_time = format_timestamp((chunk["offset"] + chunk["duration"]) / 10000000)
                            f.write(f"{start_time} --> {end_time}\n")
                            f.write(f"{chunk['text']}\n\n")
                
                # Clean up temp file if it exists
                if os.path.exists(temp_subtitle_file):
                    os.remove(temp_subtitle_file)
                    
                print(f"Successfully generated subtitles: {subtitle_file}")
                return outputfile
            except Exception as subtitle_error:
                print(f"Warning: Could not generate subtitles: {subtitle_error}")
                traceback.print_exc()
                # Create a minimal empty subtitle file to avoid downstream issues
                with open(subtitle_file, "w", encoding="utf-8") as f:
                    f.write("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nSubtitles unavailable\n\n")
                print(f"Created minimal subtitle file as fallback: {subtitle_file}")
                # Continue execution even if subtitle generation fails
                return outputfile
        except Exception as e:
            print(f"Warning: Could not generate subtitles with main method: {e}")
            traceback.print_exc()
            # Try alternative method with a new communicate instance
            try:
                # Generate audio only
                await communicate.save(outputfile)
                print(f"Successfully generated audio: {outputfile}")
                
                # Create a minimal empty subtitle file to avoid downstream issues
                with open(subtitle_file, "w", encoding="utf-8") as f:
                    f.write("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nSubtitles unavailable\n\n")
                print(f"Created minimal subtitle file as fallback: {subtitle_file}")
                return outputfile
            except Exception as e2:
                print(f"Critical error in audio generation: {e2}")
                traceback.print_exc()
                raise
        
    except Exception as e:
        print(f"Error generating audio using edge-tts: {e}")
        traceback.print_exc()
        raise Exception(f"An error happened during edge_tts audio generation: {e}")

def format_timestamp(seconds):
    """Format seconds into VTT timestamp format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

