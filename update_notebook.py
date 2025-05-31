import json
import os

# Read the existing notebook
with open('UnQTube_Colab.ipynb', 'r') as file:
    notebook = json.load(file)

# Update System Setup cell for ALSA errors
system_setup_cell = notebook['cells'][0]
system_setup_cell['source'] = [
    "# @title System Setup\n",
    "# Install required system packages\n",
    "!apt-get update -qq\n",
    "!apt-get install -qq -y python3-tk alsa-utils libasound2-plugins\n",
    "\n",
    "# Create dummy ALSA config to redirect sound to null device (prevents ALSA errors)\n",
    "%%bash\n",
    "cat > ~/.asoundrc << 'EOT'\n",
    "pcm.!default {\n",
    "    type null\n",
    "}\n",
    "ctl.!default {\n",
    "    type null\n",
    "}\n",
    "EOT"
]

# Define the Gemini API key form field and code to add to both cells
gemini_form_field = [
    "# @markdown Use Gemini API for enhanced script generation (optional)\n",
    "GEMINI_API_KEY = \"\" #@param {type:\"string\"}\n",
    "\n"
]

gemini_config_code = [
    "# Update config.txt with Gemini API Key from form\n",
    "gemini_api_key_from_form = GEMINI_API_KEY # Gets value from the form field\n",
    "if gemini_api_key_from_form:\n",
    "    print(f\"Attempting to update config.txt with Gemini API Key: {gemini_api_key_from_form[:5]}...\") # Print first 5 chars for verification\n",
    "    config_path = \"/content/UnQTube-/config.txt\"\n",
    "    try:\n",
    "        with open(config_path, \"r\") as f_read:\n",
    "            lines = f_read.readlines()\n",
    "        \n",
    "        updated_lines = []\n",
    "        key_updated = False\n",
    "        gemini_enabled = False\n",
    "\n",
    "        for line in lines:\n",
    "            stripped_line = line.strip()\n",
    "            if stripped_line.startswith(\"gemini_api_key\"):\n",
    "                updated_lines.append(f\"gemini_api_key = {gemini_api_key_from_form}\\n\")\n",
    "                key_updated = True\n",
    "            elif stripped_line.startswith(\"use_gemini\"):\n",
    "                updated_lines.append(\"use_gemini = yes\\n\")\n",
    "                gemini_enabled = True\n",
    "            else:\n",
    "                updated_lines.append(line)\n",
    "        \n",
    "        # If keys were not in original file, add them (less likely for existing config)\n",
    "        if not key_updated:\n",
    "            updated_lines.append(f\"gemini_api_key = {gemini_api_key_from_form}\\n\")\n",
    "        if not gemini_enabled and key_updated: # Enable gemini if key is set and use_gemini wasn't already yes\n",
    "            # This logic might need refinement depending on desired behavior if use_gemini was explicitly 'no'\n",
    "            pass # For now, assume if gemini_api_key is set, we want to try using it unless use_gemini is 'no'\n",
    "\n",
    "        with open(config_path, \"w\") as f_write:\n",
    "            f_write.writelines(updated_lines)\n",
    "        print(f\"Successfully updated {config_path} with Gemini API Key and set use_gemini to yes.\")\n",
    "\n",
    "    except FileNotFoundError:\n",
    "        print(f\"ERROR: {config_path} not found. Cannot update Gemini API Key.\")\n",
    "    except Exception as e:\n",
    "        print(f\"ERROR: Could not update {config_path}. Error: {e}\")\n",
    "else:\n",
    "    # Ensure Gemini is disabled if no key is provided\n",
    "    print(\"No Gemini API Key provided in the form. Ensuring Gemini is disabled in config.\")\n",
    "    config_path = \"/content/UnQTube-/config.txt\"\n",
    "    try:\n",
    "        with open(config_path, \"r\") as f_read:\n",
    "            lines = f_read.readlines()\n",
    "        \n",
    "        updated_lines = []\n",
    "        for line in lines:\n",
    "            stripped_line = line.strip()\n",
    "            if stripped_line.startswith(\"gemini_api_key\"):\n",
    "                updated_lines.append(\"gemini_api_key = \\n\") \n",
    "            elif stripped_line.startswith(\"use_gemini\"):\n",
    "                updated_lines.append(\"use_gemini = no\\n\")\n",
    "            else:\n",
    "                updated_lines.append(line)\n",
    "        \n",
    "        with open(config_path, \"w\") as f_write:\n",
    "            f_write.writelines(updated_lines)\n",
    "        print(f\"Updated {config_path}: Cleared Gemini API key and set use_gemini to no.\")\n",
    "    except Exception as e:\n",
    "        print(f\"ERROR: Could not update {config_path} to disable Gemini. Error: {e}\")\n",
    "\n"
]

# Update Long Video cell
long_video_cell = notebook['cells'][2]
long_video_source = long_video_cell['source']

# Find the line with multi_speaker parameter (or pexels_api if multi_speaker not found)
insert_idx = -1
for i, line in enumerate(long_video_source):
    if "multi_speaker" in line:
        insert_idx = i + 1
        break

if insert_idx == -1:  # Fallback
    for i, line in enumerate(long_video_source):
        if "pexels_api" in line:
            insert_idx = i + 1
            break

# Add Gemini form field and config code
if insert_idx >= 0:
    # Get the line that runs the Python command (last line)
    python_cmd_line = long_video_source[-1]
    # Remove the last line (Python command)
    long_video_source = long_video_source[:-1]
    # Add Gemini form field
    long_video_source.insert(insert_idx, gemini_form_field[0])
    long_video_source.insert(insert_idx + 1, gemini_form_field[1])
    long_video_source.insert(insert_idx + 2, gemini_form_field[2])
    # Add Gemini config code
    long_video_source.extend(gemini_config_code)
    # Add back the Python command
    long_video_source.append(python_cmd_line)

# Update Short Video cell
short_video_cell = notebook['cells'][3]
short_video_source = short_video_cell['source']

# Find the line with pexels_api parameter
insert_idx = -1
for i, line in enumerate(short_video_source):
    if "pexels_api" in line:
        insert_idx = i + 1
        break

# Add Gemini form field and config code
if insert_idx >= 0:
    # Get the line that runs the Python command (last line)
    python_cmd_line = short_video_source[-1]
    # Remove the last line (Python command)
    short_video_source = short_video_source[:-1]
    # Add Gemini form field
    short_video_source.insert(insert_idx, gemini_form_field[0])
    short_video_source.insert(insert_idx + 1, gemini_form_field[1])
    short_video_source.insert(insert_idx + 2, gemini_form_field[2])
    # Add Gemini config code
    short_video_source.extend(gemini_config_code)
    # Add back the Python command
    short_video_source.append(python_cmd_line)

# Write the updated notebook back to file
with open('UnQTube_Colab.ipynb', 'w') as file:
    json.dump(notebook, file, indent=2)

print("Successfully updated UnQTube_Colab.ipynb with Gemini API key input fields!") 