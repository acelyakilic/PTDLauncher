import json
import os
from utils import get_file_path, logger

# Default versions configuration
DEFAULT_VERSIONS = {
    "flash_player": "",
    "games": {
        "PTD1": "",
        "PTD1RF": "",
        "PTD1_Hacked": "",
        "PTD2": "",
        "PTD2_Hacked": "",
        "PTD3": "",
        "PTD3_Hacked": ""
    }
}

def load_versions():
    versions_path = get_file_path("versions.json")
    versions = DEFAULT_VERSIONS.copy()
    
    try:
        if not os.path.exists(versions_path):
            logger.info("Creating new versions.json file")
            with open(versions_path, 'w') as f:
                json.dump(versions, f, indent=4)
            return versions
        
        with open(versions_path, 'r') as f:
            loaded = json.load(f)
        
        # Validate structure and ensure all keys exist
        if isinstance(loaded, dict):
            versions["flash_player"] = loaded.get("flash_player", "")
            
            if isinstance(loaded.get("games"), dict):
                for game in DEFAULT_VERSIONS["games"]:
                    versions["games"][game] = loaded["games"].get(game, "")
            
        return versions
    except Exception as e:
        logger.error(f"Error handling versions.json: {str(e)}")
        return versions

def save_versions(versions):
    try:
        if not isinstance(versions, dict):
            logger.error("Cannot save versions: not a valid dictionary")
            return False
            
        versions_path = get_file_path("versions.json")
        with open(versions_path, 'w') as f:
            json.dump(versions, f, indent=4)
        logger.info("Saved versions.json successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving versions.json: {str(e)}")
        return False