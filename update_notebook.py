import json
import os

# Define the Gemini API form field to add
GEMINI_FORM_FIELD = """# @markdown Use Gemini API for enhanced script generation (optional)
GEMINI_API_KEY = \"\" #@param {type:\"string\"}
"""

# Define the config.txt update code to add
CONFIG_UPDATE_CODE = """
# Update config.txt with Gemini API Key from form
gemini_api_key_from_form = GEMINI_API_KEY # Gets value from the form field
if gemini_api_key_from_form:
    print(f\"Attempting to update config.txt with Gemini API Key: {gemini_api_key_from_form[:5]}...\") # Print first 5 chars for verification
    config_path = \"/content/UnQTube-/config.txt\"
    try:
        with open(config_path, \"r\") as f_read:
            lines = f_read.readlines()
        
        updated_lines = []
        key_updated = False
        gemini_enabled = False

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith(\"gemini_api\"):
                updated_lines.append(f\"gemini_api = {gemini_api_key_from_form}\\n\")
                key_updated = True
            elif stripped_line.startswith(\"use_gemini\"):
                updated_lines.append(\"use_gemini = yes\\n\")
                gemini_enabled = True
            else:
                updated_lines.append(line)
        
        # If keys were not in original file, add them
        if not key_updated:
            updated_lines.append(f\"gemini_api = {gemini_api_key_from_form}\\n\")
        if not gemini_enabled:
            updated_lines.append(\"use_gemini = yes\\n\")

        with open(config_path, \"w\") as f_write:
            f_write.writelines(updated_lines)
        print(f\"Successfully updated {config_path} with Gemini API Key and set use_gemini to yes.\")

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
        print(f\"ERROR: Could not update {config_path} to disable Gemini. Error: {e}\")
"""

# Define improved ALSA config for the System Setup cell
ALSA_CONFIG = """# @title System Setup
# Install required system packages
!apt-get update -qq
!apt-get install -qq -y python3-tk alsa-utils libasound2-plugins

# Create dummy ALSA config to redirect sound to null device (prevents ALSA errors)
%%bash
cat > ~/.asoundrc << 'EOT'
pcm.!default {
    type null
}
ctl.!default {
    type null
}
EOT"""

def update_notebook():
    # Make a backup of the original notebook
    if os.path.exists('UnQTube_Colab.ipynb'):
        with open('UnQTube_Colab.ipynb', 'r') as f:
            original_content = f.read()
        
        with open('UnQTube_Colab.ipynb.bak', 'w') as f:
            f.write(original_content)
        
        print("Created backup as UnQTube_Colab.ipynb.bak")
    
    # Read the notebook
    try:
        with open('UnQTube_Colab.ipynb', 'r') as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"Error reading notebook: {e}")
        return
    
    # Update System Setup cell
    try:
        system_setup_cell = notebook['cells'][0]
        system_setup_cell['source'] = ALSA_CONFIG
    except Exception as e:
        print(f"Error updating System Setup cell: {e}")
    
    # Update Long Video cell
    try:
        long_video_cell = notebook['cells'][2]
        
        # Extract all content before the final Python command
        source_content = ''.join(long_video_cell['source'])
        
        # Find the position of the last Python command (which runs video.py)
        python_cmd_pos = source_content.rfind('!python video.py')
        
        if python_cmd_pos > 0:
            # Split the content
            content_before_cmd = source_content[:python_cmd_pos]
            python_cmd = source_content[python_cmd_pos:]
            
            # Check if Gemini API field already exists
            if "GEMINI_API_KEY" not in content_before_cmd:
                # Add Gemini form field and config update code
                new_content = content_before_cmd + GEMINI_FORM_FIELD + CONFIG_UPDATE_CODE + "\n" + python_cmd
                
                # Update the cell source
                long_video_cell['source'] = new_content
                print("Updated Long Video cell with Gemini API Key field and config update code")
            else:
                print("Long Video cell already has Gemini API Key field")
    except Exception as e:
        print(f"Error updating Long Video cell: {e}")
    
    # Update Short Video cell
    try:
        short_video_cell = notebook['cells'][3]
        
        # Extract all content before the final Python command
        source_content = ''.join(short_video_cell['source'])
        
        # Find the position of the last Python command (which runs short.py)
        python_cmd_pos = source_content.rfind('!python short.py')
        
        if python_cmd_pos > 0:
            # Split the content
            content_before_cmd = source_content[:python_cmd_pos]
            python_cmd = source_content[python_cmd_pos:]
            
            # Check if Gemini API field already exists
            if "GEMINI_API_KEY" not in content_before_cmd:
                # Add Gemini form field and config update code
                new_content = content_before_cmd + GEMINI_FORM_FIELD + CONFIG_UPDATE_CODE + "\n" + python_cmd
                
                # Update the cell source
                short_video_cell['source'] = new_content
                print("Updated Short Video cell with Gemini API Key field and config update code")
            else:
                print("Short Video cell already has Gemini API Key field")
    except Exception as e:
        print(f"Error updating Short Video cell: {e}")
    
    # Write the updated notebook
    try:
        with open('UnQTube_Colab.ipynb', 'w') as f:
            json.dump(notebook, f, indent=2)
        print("Successfully wrote updated notebook to UnQTube_Colab.ipynb")
    except Exception as e:
        print(f"Error writing updated notebook: {e}")
        
        # Restore from backup if write failed
        with open('UnQTube_Colab.ipynb.bak', 'r') as f:
            backup_content = f.read()
        
        with open('UnQTube_Colab.ipynb', 'w') as f:
            f.write(backup_content)
        
        print("Restored notebook from backup due to write error")

if __name__ == "__main__":
    update_notebook()
    print("Notebook update process completed. Please verify the changes.") 