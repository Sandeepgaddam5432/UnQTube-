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
    try:
        voices = await VoicesManager.create()
        if (lang == "en"):
            voice = voices.find(Locale="en-US")
        else:
            voice = voices.find(Language = lang)
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
                    
        communicate = edge_tts.Communicate(text, speaker)
        submaker = edge_tts.SubMaker()
        with open(outputfile, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.add(chunk["offset"], chunk["duration"], chunk["text"])

    except Exception as e:
        print("Error generating audio using edge_tts", e)
        raise Exception("An error happened during edge_tts audio generation, no output audio generated", e)

    return outputfile

