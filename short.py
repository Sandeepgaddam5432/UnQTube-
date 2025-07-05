import argparse
import asyncio
from lib.shortcore import final_video
from lib.async_core import make_short_video_async, cleanup
from lib.config_utils import read_config_file

def parse_args():
	parser = argparse.ArgumentParser(description='Create a short vertical video')
	parser.add_argument('-topic', type=str, help='topic of video', default='cooking secrets')
	parser.add_argument('-time', type=str, help='time of video in seconds', default='30')
	parser.add_argument('-pexels_api', type=str, help='pexels api', default='')
	parser.add_argument('-language', type=str, help='language of video', default='english')
	parser.add_argument('-multi_speaker', type=str, help='use multi speaker', default='no')
	parser.add_argument('-use_async', type=str, help='use async processing (yes/no)', default='yes')
	return parser.parse_args()

async def main_async():
	args = parse_args()
	try:
		# Import update_config_file from the correct module
		from lib.config_utils import update_config_file
		
		# Update config if pexels_api is provided
		if args.pexels_api:
			update_config_file('config.txt', 'pexels_api', args.pexels_api)
			
		# Update other config values
		update_config_file('config.txt', 'language', args.language)
		update_config_file('config.txt', 'multi_speaker', args.multi_speaker)
		
		# Use async version if requested (default)
		if args.use_async.lower() in ['yes', 'y', 'true', '1']:
			print("\nUsing high-performance asynchronous processing\n")
			await make_short_video_async(args.topic, int(args.time))
		else:
			print("\nUsing legacy synchronous processing\n")
			# Run legacy version in thread to avoid blocking the event loop
			await asyncio.to_thread(final_video, args.topic, args.time, args.language, args.multi_speaker)
	except Exception as e:
		print(f"Error: {e}")
	finally:
		# Clean up temp files
		cleanup()

def main():
	args = parse_args()
	
	# For backward compatibility, use the legacy synchronous version
	try:
		# Import update_config_file from the correct module
		from lib.config_utils import update_config_file
		
		# Update config if pexels_api is provided
		if args.pexels_api:
			update_config_file('config.txt', 'pexels_api', args.pexels_api)
			
		# Update other config values
		update_config_file('config.txt', 'language', args.language)
		update_config_file('config.txt', 'multi_speaker', args.multi_speaker)
		
		# Check if we should use async version
		if args.use_async.lower() in ['yes', 'y', 'true', '1']:
			print("\nUsing high-performance asynchronous processing\n")
			asyncio.run(make_short_video_async(args.topic, int(args.time)))
		else:
			print("\nUsing legacy synchronous processing\n")
			final_video(args.topic, args.time, args.language, args.multi_speaker)
	except Exception as e:
		print(f"Error: {e}")
	finally:
		# Clean up temp files
		cleanup()

if __name__ == '__main__':
	main()	