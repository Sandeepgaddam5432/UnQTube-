import json

# Read the notebook
with open('UnQTube_Colab.ipynb', 'r') as f:
    notebook = json.load(f)

# Update the System Setup cell (first cell)
system_setup_cell = notebook['cells'][0]

# Replace the source with the fixed version
system_setup_cell['source'] = """# @title System Setup
# Install required system packages
print("Starting system setup...")
!apt-get update -qq
!apt-get install -qq -y python3-tk alsa-utils libasound2-plugins
print("System packages installed.")

# Create dummy ALSA config to redirect sound to null device (prevents ALSA errors)
print("Creating dummy ALSA config...")
alsa_config_content = \"\"\"
pcm.!default {
    type null
}
ctl.!default {
    type null
}
\"\"\"

# Write to home directory using os.path.expanduser to handle ~ correctly
import os
asoundrc_path = os.path.expanduser("~/.asoundrc")
try:
    with open(asoundrc_path, "w") as f:
        f.write(alsa_config_content)
    print(f"Dummy ALSA config created at {asoundrc_path}")
    # Verify file was created
    !cat ~/.asoundrc
except Exception as e:
    print(f"Warning: Could not create ALSA config: {e}")
    # Try alternative approach with shell command
    !echo "pcm.!default { type null }\\nctl.!default { type null }" > ~/.asoundrc
    print("Attempted alternative method to create ALSA config")

print("System setup complete.")"""

# Update Long Video cell with Gemini model selector
long_video_cell = notebook['cells'][2]
long_video_source = long_video_cell['source']

# Convert source to string if it's a list
if isinstance(long_video_source, list):
    long_video_source = ''.join(long_video_source)

# Add Gemini model selector after API key and update the config handling
gemini_form_field = """# @markdown Use Gemini API for enhanced script generation (optional)
GEMINI_API_KEY = \"\" #@param {type:\"string\"}
# @markdown Select Gemini model
GEMINI_MODEL_NAME = \"gemini-1.5-flash-latest\" #@param [\"gemini-1.0-pro\", \"gemini-1.5-flash-latest\", \"gemini-1.5-pro-latest\"]

# Update config.txt with Gemini API Key and model from form
gemini_api_key_from_form = GEMINI_API_KEY # Gets value from the form field
gemini_model_from_form = GEMINI_MODEL_NAME # Gets model from the form field

if gemini_api_key_from_form:
    print(f\"Attempting to update config.txt with Gemini API Key: {gemini_api_key_from_form[:5]}... and model: {gemini_model_from_form}\")
    config_path = \"/content/UnQTube-/config.txt\"
    try:
        with open(config_path, \"r\") as f_read:
            lines = f_read.readlines()
        
        updated_lines = []
        key_updated = False
        model_updated = False
        gemini_enabled = False

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith(\"gemini_api\"):
                updated_lines.append(f\"gemini_api = {gemini_api_key_from_form}\\n\")
                key_updated = True
            elif stripped_line.startswith(\"gemini_model\"):
                updated_lines.append(f\"gemini_model = {gemini_model_from_form}\\n\")
                model_updated = True
            elif stripped_line.startswith(\"use_gemini\"):
                updated_lines.append(\"use_gemini = yes\\n\")
                gemini_enabled = True
            else:
                updated_lines.append(line)
        
        # If keys were not in original file, add them
        if not key_updated:
            updated_lines.append(f\"gemini_api = {gemini_api_key_from_form}\\n\")
        if not model_updated:
            updated_lines.append(f\"gemini_model = {gemini_model_from_form}\\n\")
        if not gemini_enabled:
            updated_lines.append(\"use_gemini = yes\\n\")

        with open(config_path, \"w\") as f_write:
            f_write.writelines(updated_lines)
        print(f\"Successfully updated {config_path} with Gemini API Key, model {gemini_model_from_form}, and set use_gemini to yes.\")

    except FileNotFoundError:
        print(f\"ERROR: {config_path} not found. Cannot update Gemini API Key.\")
    except Exception as e:
        print(f\"ERROR: Could not update {config_path}. Error: {e}\")
else:
    # Ensure Gemini is disabled if no key is provided
    print(\"No Gemini API Key provided in the form. Ensuring Gemini is disabled in config.\")
    config_path = \"/content/UnQTube-/config.txt\"
    try:
        with open(config_path, \"r\") as f_read:
            lines = f_read.readlines()
        
        updated_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith(\"gemini_api\"):
                updated_lines.append(\"gemini_api = \\n\") 
            elif stripped_line.startswith(\"use_gemini\"):
                updated_lines.append(\"use_gemini = no\\n\")
            else:
                updated_lines.append(line)
        
        with open(config_path, \"w\") as f_write:
            f_write.writelines(updated_lines)
        print(f\"Updated {config_path}: Cleared Gemini API key and set use_gemini to no.\")
    except Exception as e:
        print(f\"ERROR: Could not update {config_path} to disable Gemini. Error: {e}\")"""

# Find the existing Gemini API key field and replace it with our updated fields
if "GEMINI_API_KEY" in long_video_source:
    # Find the start position of Gemini API section
    start_pos = long_video_source.find("# @markdown Use Gemini API for enhanced script generation")
    
    # Find the end position (where the command starts)
    end_pos = long_video_source.find("!python video.py")
    
    if start_pos > 0 and end_pos > 0:
        # Replace the entire Gemini section
        updated_source = long_video_source[:start_pos] + gemini_form_field + "\n\n" + long_video_source[end_pos:]
        long_video_cell['source'] = updated_source

# Update Short Video cell with Gemini model selector
short_video_cell = notebook['cells'][3]
short_video_source = short_video_cell['source']

# Convert source to string if it's a list
if isinstance(short_video_source, list):
    short_video_source = ''.join(short_video_source)

# Find the existing Gemini API key field and replace it with our updated fields
if "GEMINI_API_KEY" in short_video_source:
    # Find the start position of Gemini API section
    start_pos = short_video_source.find("# @markdown Use Gemini API for enhanced script generation")
    
    # Find the end position (where the command starts)
    end_pos = short_video_source.find("!python short.py")
    
    if start_pos > 0 and end_pos > 0:
        # Replace the entire Gemini section
        updated_source = short_video_source[:start_pos] + gemini_form_field + "\n\n" + short_video_source[end_pos:]
        short_video_cell['source'] = updated_source

# Write the updated notebook back to file
with open('UnQTube_Colab.ipynb', 'w') as f:
    json.dump(notebook, f, indent=2)

print("Successfully updated UnQTube_Colab.ipynb with Gemini model selector and fixed System Setup cell") 