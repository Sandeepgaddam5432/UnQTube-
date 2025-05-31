import re
import yaml
import random
from lib.config_utils import read_config_file
from lib.gemini_api import generate_script_with_gemini

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
    flag = True
    while(flag):
        prompt = getyamll("names_prompt").format(title=title)
        message = generate_ai_text(prompt)
        city_names_list = []
        start_index = message.find('[')
        end_index = message.find(']')
        if start_index != -1 and end_index != -1:
            city_names_text = message[start_index + 1:end_index]
            city_names_list = city_names_text.split(',')
            for city in city_names_list:
              if city[0] == " ":
                city  = city[0:]
            city_names_list = [city.strip('" ') for city in city_names_list]
            flag = False
            return city_names_list
        elif re.search(r'\d+\.\s+.+', message):
            city_names_list = re.findall(r'\d+\.\s+(.+)', message)
            city_names_list = [item.strip('"') for item in city_names_list]
            flag = False
            return city_names_list


def process_text(text, keyword):
    index = text.find(keyword)
    if index != -1:
        result = text[index + len(keyword):]
    else:
        result = text
    return result

# Helper function to generate AI text without circular imports
def generate_ai_text(prompt):
    """Generate text using Gemini AI without circular imports"""
    try:
        return generate_script_with_gemini(prompt)
    except Exception as e:
        raise Exception(f"Error generating AI text: {e}")


