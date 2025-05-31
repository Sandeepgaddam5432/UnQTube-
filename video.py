import argparse
from lib.config_utils import update_config_file
from lib.core import making_video

# Parse command line arguments
parser = argparse.ArgumentParser(description='UnQTube - long video generator')
parser.add_argument('-topic', dest='topic', type=str, help='Enter video topic. Example: survival video game')
parser.add_argument('-general_topic', dest='general_topic', type=str, help='general topic you want to make a video about.Example: video game, food, city, person and...')
parser.add_argument('-time', dest='time', type=str, help='video time in minute')
parser.add_argument('-intro_video', dest='intro_video', type=str, help='do you want intro with video instead photo?')
parser.add_argument('-pexels_api', dest='pexels_api', type=str, help='get API from www.pexels.com')
parser.add_argument('-language', dest='language', type=str, help='video language')
parser.add_argument('-multi_speaker', dest='multi_speaker', type=str, help='Use multiple speakers in video')
parser.add_argument('-gemini_api', dest='gemini_api', type=str, help='Gemini API key for enhanced script generation')

args = parser.parse_args()

# Update config file with provided arguments
if args.general_topic is not None:
	update_config_file('config.txt', 'general_topic', args.general_topic)
if args.time is not None:
	update_config_file('config.txt', 'time', args.time)
if args.intro_video is not None:	
	update_config_file('config.txt', 'intro_video', args.intro_video)
if args.pexels_api is not None:
	update_config_file('config.txt', 'pexels_api', args.pexels_api)
if args.language is not None:
	update_config_file('config.txt', 'language', args.language)
if args.multi_speaker is not None:
	update_config_file('config.txt', 'multi_speaker', args.multi_speaker)
if args.gemini_api is not None:
	update_config_file('config.txt', 'gemini_api', args.gemini_api)
	# Enable Gemini if API key is provided
	update_config_file('config.txt', 'use_gemini', 'yes')

# Start video creation if topic is provided
if args.topic is not None:
	making_video(args.topic)
else:
	print('Please enter a topic with "-topic"')		