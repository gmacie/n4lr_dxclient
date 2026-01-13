"""
Central file path management with data subdirectory
All data files go in /data folder for clean organization
"""

# file_paths.py 01/07/2026

import sys
from pathlib import Path

def get_app_directory():
    """
    Get the application directory (where .exe or main.py is located)
    """
    if getattr(sys, 'frozen', False):
        # Running as .exe - return exe directory
        return Path(sys.executable).parent
    else:
        # Running as script - return project root
        # Go up from backend/file_paths.py to project root
        return Path(__file__).parent.parent

def get_data_directory():
    """Get the data directory (creates if doesn't exist)"""
    data_dir = get_app_directory() / "data"
    
    #Print(f"DEBUG: App directory: {get_app_directory()}")
    #print(f"DEBUG: Data directory: {data_dir}")
    #print(f"DEBUG: Data directory exists: {data_dir.exists()}")
    
    data_dir.mkdir(exist_ok=True)
    return data_dir

def get_static_data_directory():
    """Get the static data directory (reference files)"""
    static_dir = get_data_directory() / "static"
    static_dir.mkdir(exist_ok=True)
    return static_dir


def get_user_data_directory():
    """Get the user data directory (runtime/generated files)"""
    user_dir = get_data_directory() / "user"
    user_dir.mkdir(exist_ok=True)
    return user_dir


# Static reference files (from repo, read-only)
def get_dxcc_entities_file():
    return get_static_data_directory() / "dxcc_entities.json"

def get_dxcc_mapping_file():
    return get_static_data_directory() / "dxcc_mapping.json"

def get_dxcc_prefixes_file():
    return get_static_data_directory() / "dxcc_prefixes.json"

def get_dxcc_overrides_file():
    return get_static_data_directory() / "dxcc_name_overrides.json"

def get_cty_dat_file():
    return get_static_data_directory() / "cty.dat"

def get_ffma_grids_file():
    return get_static_data_directory() / "ffma_grids.json"


# User/runtime files (generated, modified)
def get_config_file():
    return get_user_data_directory() / "config.ini"

def get_challenge_data_file():
    return get_user_data_directory() / "challenge_data.json"
    
def get_ffma_data_file():
    return get_user_data_directory() / "ffma_data.json"

def get_lotw_users_file():
    return get_user_data_directory() / "lotw_users.json"

def get_lotw_credentials_file():
    return get_user_data_directory() / "lotw_credentials.enc"

def get_app_log_file():
    return get_user_data_directory() / "app.log"


# Ensure directories exist on import
get_static_data_directory()
get_user_data_directory()


if __name__ == "__main__":

    print("=== File Path Structure ===")
    print(f"App directory: {get_app_directory()}")
    print(f"Data directory: {get_data_directory()}")

    print(f"Static data: {get_static_data_directory()}")
    print(f"User data: {get_user_data_directory()}")
    print()
    print("Static files:")
    print(f"  DXCC entities: {get_dxcc_entities_file()}")
    print(f"  CTY.DAT: {get_cty_dat_file()}")
    print()
    print("User files:")
    print(f"  Config: {get_config_file()}")
    print(f"  Challenge: {get_challenge_data_file()}")
    print(f"  Log: {get_app_log_file()}")