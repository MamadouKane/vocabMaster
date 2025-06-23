"""
Environment variables loader for VocabMaster
Loads configuration from .env file with fallback to environment variables
"""
import os
from typing import Optional

def load_env_file() -> dict:
    """Load environment variables from .env file"""
    env_vars = {}
    env_path = '.env'
    
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            env_vars[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")
    
    return env_vars

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable from .env file
    """
    # Check .env file
    env_vars = load_env_file()
    value = env_vars.get(key)
    if value:
        return value

    # Return default value
    return default

# Pre-load common configuration
HUGGINGFACE_TOKEN = get_env_var('HUGGINGFACE_TOKEN')
FIREBASE_DATABASE_URL = get_env_var('FIREBASE_DATABASE_URL')
APP_NAME = get_env_var('APP_NAME', 'VocabMaster')
DEBUG_MODE = get_env_var('DEBUG_MODE', 'false').lower() == 'true'
SERVER_PORT = int(get_env_var('SERVER_PORT', '5000'))
SERVER_HOST = get_env_var('SERVER_HOST', '0.0.0.0')