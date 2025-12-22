# config.py - User configuration management
import configparser
import os
from pathlib import Path

CONFIG_FILE = "config.ini"

def get_config_path():
    """Get the path to the config file in the app directory"""
    return Path(CONFIG_FILE)

def load_config():
    """Load configuration from config.ini, create with defaults if doesn't exist"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    if config_path.exists():
        config.read(config_path)
    else:
        # Create default config
        config['user'] = {
            'callsign': 'N4LR',
            'grid': 'EM50'
        }
        config['cluster'] = {
            'server': 'www.ve7cc.net',
            'port': '23'
        }
        save_config(config)
    
    return config

def save_config(config):
    """Save configuration to config.ini"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        config.write(f)

def get_user_callsign():
    """Get user's callsign from config"""
    config = load_config()
    return config.get('user', 'callsign', fallback='N4LR')

def get_user_grid():
    """Get user's grid square from config"""
    config = load_config()
    return config.get('user', 'grid', fallback='EM50')

def set_user_callsign(callsign):
    """Set user's callsign in config"""
    config = load_config()
    if 'user' not in config:
        config['user'] = {}
    config['user']['callsign'] = callsign
    save_config(config)

def set_user_grid(grid):
    """Set user's grid square in config"""
    config = load_config()
    if 'user' not in config:
        config['user'] = {}
    config['user']['grid'] = grid.upper()
    save_config(config)

def set_user_settings(callsign, grid):
    """Set both callsign and grid at once"""
    config = load_config()
    if 'user' not in config:
        config['user'] = {}
    config['user']['callsign'] = callsign
    config['user']['grid'] = grid.upper()
    save_config(config)