import asyncio
import random
import os
from concurrent.futures import ThreadPoolExecutor
import edge_tts
from edge_tts import VoicesManager
from lib.config_utils import read_config_file

def generate_voice(text, outputfile, lang):
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
    It works with edge-tts 7.0.2 by creating separate Communicate instances
    for audio and subtitle generation.
    
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
        
        # Generate audio file using the first Communicate instance
        audio_communicate = edge_tts.Communicate(text, speaker)
        await audio_communicate.save(outputfile)
        print(f"Successfully generated audio: {outputfile}")
        
        # Generate subtitle file using a SEPARATE Communicate instance
        subtitle_file = os.path.splitext(outputfile)[0] + ".vtt"
        try:
            # Create a new Communicate instance specifically for subtitles
            subtitle_communicate = edge_tts.Communicate(text, speaker)
            
            # Create subtitle file using the new stream
            with open(subtitle_file, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                # Collect subtitle data from the stream
                subtitle_data = []
                async for chunk in subtitle_communicate.stream():
                    if chunk["type"] == "WordBoundary":
                        # Store the chunk for subtitle processing
                        subtitle_data.append(chunk)
                
                # Process all subtitle chunks
                for chunk in subtitle_data:
                    # Format: 00:00:00.000 --> 00:00:01.000
                    start_time = format_timestamp(chunk["offset"] / 10000000)
                    end_time = format_timestamp((chunk["offset"] + chunk["duration"]) / 10000000)
                    
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{chunk['text']}\n\n")
            
            print(f"Successfully generated subtitles: {subtitle_file}")
        except Exception as subtitle_error:
            print(f"Warning: Could not generate subtitles: {subtitle_error}")
            # Continue execution even if subtitle generation fails
        
        return outputfile
        
    except Exception as e:
        print(f"Error generating audio using edge-tts: {e}")
        raise Exception(f"An error happened during edge_tts audio generation: {e}")

def format_timestamp(seconds):
    """Format seconds into VTT timestamp format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

