"""
Utility functions for reading and writing configuration files.
This module provides functions to read from and update the config.txt file.
"""

def read_config_file(file_path="config.txt"):
    """
    Read configuration from a file and return as a dictionary.
    
    Args:
        file_path: Path to the configuration file (default: config.txt)
        
    Returns:
        Dictionary containing configuration key-value pairs
    """
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split(' = ', 1)  # Split on first equals sign only
                config[key.strip()] = value.strip()
    return config

def update_config_file(file_path, variable_name, new_value):
    """
    Update a specific configuration variable in the config file.
    
    Args:
        file_path: Path to the configuration file
        variable_name: The name of the variable to update
        new_value: The new value to set for the variable
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        found = False
        for line in lines:
            if '=' in line:
                key, value = line.strip().split(' = ', 1)  # Split on first equals sign only
                if key.strip() == variable_name:
                    line = f"{key.strip()} = {new_value}\n"
                    found = True
            file.write(line)
        
        # If the variable wasn't found, add it to the end of the file
        if not found:
            file.write(f"{variable_name} = {new_value}\n") 