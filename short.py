import argparse
from lib.config_utils import update_config_file
from lib.shortcore import final_video

# Parse command line arguments
parser = argparse.ArgumentParser(description='UnQTube - short video generator')
parser.add_argument('-topic', dest='topic', type=str, help='Enter video topic. Example: top 10 survival video game')
parser.add_argument('-time', dest='time', type=str, help='video time in seconds')
parser.add_argument('-language', dest='language', type=str, help='video language')
parser.add_argument('-multi_speaker', dest='multi_speaker', type=str, help='Use multiple speakers in video')
parser.add_argument('-pexels_api', dest='pexels_api', type=str, help='get API from www.pexels.com')
parser.add_argument('-gemini_api', dest='gemini_api', type=str, help='Gemini API key for enhanced script generation')

args = parser.parse_args()

# Update config with any provided arguments
if args.pexels_api is not None:
	update_config_file('config.txt', 'pexels_api', args.pexels_api)
if args.multi_speaker is not None:
	update_config_file('config.txt', 'multi_speaker', args.multi_speaker)
if args.gemini_api is not None:
	update_config_file('config.txt', 'gemini_api', args.gemini_api)
	# Enable Gemini if API key is provided
	update_config_file('config.txt', 'use_gemini', 'yes')

# Process default values
if args.topic is not None:
	time = args.time if args.time is not None else "30"
	language = args.language if args.language is not None else "english"
	multi_speaker = args.multi_speaker if args.multi_speaker is not None else "no"
	
	# Start video creation
	final_video(args.topic, time, language, multi_speaker)
else:
	print('Please enter a topic with "-topic"')	