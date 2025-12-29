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
            'port': '23',
            'auto_connect': 'yes'
        }
        config['display'] = {
            'needed_spot_minutes': '15'
        }
        config['lotw'] = {
            'username': '',
            'password': '',
            'last_vucc_update': ''
        }
        save_config(config)
    
    # Ensure display section exists
    if 'display' not in config:
        config['display'] = {'needed_spot_minutes': '15'}
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

def get_cluster_servers():
    """Get list of cluster servers from config"""
    config = load_config()
    servers_str = config.get('cluster', 'servers', fallback='www.ve7cc.net:23,www.dxspots.com:7300,cluster.ve3eid.com:8300')
    return [s.strip() for s in servers_str.split(',')]

def get_current_server():
    """Get currently selected cluster server"""
    config = load_config()
    return config.get('cluster', 'current_server', fallback='www.ve7cc.net:23')

def set_current_server(server):
    """Set the current cluster server"""
    config = load_config()
    if 'cluster' not in config:
        config['cluster'] = {}
    config['cluster']['current_server'] = server
    save_config(config)

def get_auto_connect():
    """Get auto-connect setting"""
    config = load_config()
    return config.getboolean('cluster', 'auto_connect', fallback=True)

def set_auto_connect(value):
    """Set auto-connect setting"""
    config = load_config()
    if 'cluster' not in config:
        config['cluster'] = {}
    config['cluster']['auto_connect'] = 'yes' if value else 'no'
    save_config(config)

def get_needed_spot_minutes():
    """Get how long to keep needed spots (in minutes)"""
    config = load_config()
    return config.getint('display', 'needed_spot_minutes', fallback=15)

def set_needed_spot_minutes(minutes):
    """Set how long to keep needed spots (in minutes)"""
    config = load_config()
    if 'display' not in config:
        config['display'] = {}
    config['display']['needed_spot_minutes'] = str(minutes)
    save_config(config)

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

def get_lotw_username():
    """Get LoTW username"""
    config = load_config()
    return config.get('lotw', 'username', fallback='')

def get_lotw_password():
    """Get LoTW password"""
    config = load_config()
    return config.get('lotw', 'password', fallback='')

def set_lotw_credentials(username, password):
    """Set LoTW username and password"""
    config = load_config()
    if 'lotw' not in config:
        config['lotw'] = {}
    config['lotw']['username'] = username
    config['lotw']['password'] = password
    save_config(config)

def get_last_vucc_update():
    """Get last VUCC data update timestamp"""
    config = load_config()
    return config.get('lotw', 'last_vucc_update', fallback='')

def set_last_vucc_update(timestamp):
    """Set last VUCC data update timestamp"""
    config = load_config()
    if 'lotw' not in config:
        config['lotw'] = {}
    config['lotw']['last_vucc_update'] = timestamp
    save_config(config)