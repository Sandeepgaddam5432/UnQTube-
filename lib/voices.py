import asyncio
import random
import os
from concurrent.futures import ThreadPoolExecutor
import edge_tts
from edge_tts import VoicesManager
from lib.video_texts import read_config_file

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
    It works with edge-tts 7.0.2 by using the communicate.save() method.
    
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
        multi = read_config_file()["multi_speaker"]
        if(multi=="yes" or multi=="Yes" or multi=="YES"): 
            speaker = random.choice(voice)["Name"]
        else:      
            try:
                speaker = read_config_file("temp.txt")["speaker"]
            except:
                speaker = random.choice(voice)["Name"]
                with open("temp.txt", "w") as file:
                    file.write("speaker = " + speaker)
        
        # Create communicate instance
        communicate = edge_tts.Communicate(text, speaker)
        
        # Generate audio file
        await communicate.save(outputfile)
        
        # Generate subtitle file (optional - for future use)
        subtitle_file = os.path.splitext(outputfile)[0] + ".vtt"
        await communicate.save_subtitles(subtitle_file)
        
        print(f"Successfully generated audio: {outputfile}")
        return outputfile
        
    except Exception as e:
        print(f"Error generating audio using edge_tts: {e}")
        raise Exception(f"An error happened during edge_tts audio generation: {e}")

