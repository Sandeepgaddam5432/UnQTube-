import re
import yaml
import random
from lib.config_utils import read_config_file
from lib.gemini_api import generate_script_with_gemini, generate_top10_list

def read_random_line(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        random_line = random.choice(lines)
        return random_line.strip()  

def getyamll(name):
    with open('lib/prompt.yaml', 'r') as file:
        data = yaml.safe_load(file)    
    return data[name]

def get_names(title):
    """Get top 10 items for a given topic using Gemini"""
    try:
        # Use the new structured top10 list generator
        result = generate_top10_list(title)
        return result["items"]
    except Exception as e:
        print(f"Error getting top 10 items: {e}")
        
        # Fallback to simpler approach if structured generation fails
        flag = True
        while flag:
            prompt = f"""
            Generate a list of the top 10 items for: {title}
            
            Return ONLY a JSON array of strings, nothing else.
            Example: ["Item 1", "Item 2", "Item 3", ...]
            """
            
            message = generate_script_with_gemini(prompt)
            try:
                # Try to parse as JSON
                if "```json" in message:
                    json_text = message.split("```json")[1].split("```")[0].strip()
                elif "```" in message:
                    json_text = message.split("```")[1].strip()
                else:
                    json_text = message.strip()
                    
                import json
                items = json.loads(json_text)
                if isinstance(items, list) and len(items) >= 10:
                    return items[:10]
            except:
                # If JSON parsing fails, try regex patterns
                if re.search(r'\[.*\]', message):
                    # Extract content between brackets
                    start_index = message.find('[')
                    end_index = message.rfind(']')
                    if start_index != -1 and end_index != -1:
                        item_text = message[start_index + 1:end_index]
                        items = [item.strip().strip('"\'') for item in item_text.split(',')]
                        if len(items) >= 10:
                            return items[:10]
                elif re.search(r'\d+\.\s+.+', message):
                    # Extract numbered list items
                    items = re.findall(r'\d+\.\s+(.+)', message)
                    items = [item.strip().strip('"\'') for item in items]
                    if len(items) >= 10:
                        return items[:10]

def get_item_content(title, item, genre="", time=30):
    """Get detailed content for a specific item in a top 10 list"""
    try:
        prompt = f"""
        Create engaging script content for "{item}" in a top 10 video about "{title}".
        The script should be about {time} seconds when read aloud.
        
        Also provide 2 specific visual search terms that would work well for finding stock footage or images.
        
        OUTPUT FORMAT:
        Return a JSON object with these fields:
        - "script": The script text explaining this item (about 3-4 sentences)
        - "search_terms": Array of 2 visual search terms (be specific with visual details)
        """
        
        response = generate_script_with_gemini(prompt)
        
        try:
            # Extract the JSON
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].strip()
            else:
                json_text = response.strip()
                
            import json
            data = json.loads(json_text)
            return data
        except:
            # Fallback to using the whole text as script
            return {
                "script": response.strip(),
                "search_terms": [f"{item} {genre}", f"{item} {title}"]
            }
    except Exception as e:
        print(f"Error getting item content: {e}")
        return {
            "script": f"Item {item} is an excellent example of {title}. It stands out for its unique characteristics and exceptional quality.",
            "search_terms": [f"{item} {genre}", f"{item} {title}"]
        }

def process_text(text, keyword):
    """Remove any prefixes from text based on keyword"""
    index = text.find(keyword)
    if index != -1:
        result = text[index + len(keyword):]
    else:
        result = text
    return result

def get_intro_text(title):
    """Generate intro text for a video"""
    language = read_config_file()["language"]
    prompt = getyamll("intro_prompt").format(title=title, language=language)
    
    try:
        intro_text = generate_script_with_gemini(prompt)
        return process_text(intro_text, ":")
    except Exception as e:
        print(f"Error generating intro text: {e}")
        return f"Welcome to our top ten video about {title}. Please like and subscribe to our channel for more great content."


