import sys
import os
import logging

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
FILES_DIR = os.path.join(BASE_DIR, "files")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
LOG_FILE = os.path.join(FILES_DIR, "ptdlauncher.log")

# Ensure directories exist before setting up logging
os.makedirs(FILES_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger('PTDLauncher')

# Caches for paths
_resource_cache = {}
_file_cache = {}

def get_resource_path(filename):
    """Get path for embedded resources with caching."""
    if filename in _resource_cache:
        return _resource_cache[filename]
    
    try:
        # Use PyInstaller's _MEIPASS if available, otherwise use relative path
        base = getattr(sys, '_MEIPASS', '') or ''
        path = os.path.join(base, "resources", filename)
        _resource_cache[filename] = path
        return path
    except Exception as e:
        logger.error(f"Resource path error for {filename}: {e}")
        return os.path.join(RESOURCES_DIR, filename)

def get_file_path(filename):
    """Get path for non-embedded files with caching."""
    if filename in _file_cache:
        return _file_cache[filename]
    
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        path = os.path.join(FILES_DIR, filename)
        _file_cache[filename] = path
        return path
    except Exception as e:
        logger.error(f"File path error for {filename}: {e}")
        return os.path.join(FILES_DIR, filename)

def ensure_directories():
    """Ensure required directories exist."""
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        logger.info("Directories verified")
        return True
    except Exception as e:
        logger.error(f"Directory creation error: {e}")
        return False