"""
Logging configuration for N4LR DX Client
Logs to app.log in root directory, rotates weekly
"""

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
#from backend.file_paths import get_lotw_users_file

from backend.file_paths import get_app_log_file

LOG_FILE = str(get_app_log_file()) 
LOG_LEVEL = logging.INFO

def setup_logging():
    """
    Configure application logging
    - Logs to app.log in data/user directory
    - Rotates every Monday (weekly)
    - Keeps last 4 weeks of logs
    - Also logs to console for development
    """
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler - ALWAYS add this first
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # NOW try to create file handler
    try:
        log_path = Path(LOG_FILE)
        print(f"Attempting to create log at: {log_path.absolute()}")
        
        # ENSURE directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Log directory created: {log_path.parent}")
        
        # File handler - rotates weekly
        file_handler = TimedRotatingFileHandler(
            str(log_path),  # Convert to string
            when='W0',
            interval=1,
            backupCount=4,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Test write
        logger.info("="*80)
        logger.info("N4LR DX Client Starting")
        logger.info(f"Log file: {log_path.absolute()}")
        logger.info(f"Frozen mode: {getattr(sys, 'frozen', False)}")
        logger.info(f"Executable: {sys.executable}")
        logger.info("="*80)
        
        print(f"SUCCESS: Logging to {log_path.absolute()}")
        
    except Exception as e:
        print(f"ERROR setting up file logging: {e}")
        print(f"Attempted log file: {LOG_FILE}")
        logger.error(f"Failed to create log file: {e}")
        # Continue with console logging only
    
    return logger

def get_logger(name):
    """Get a logger for a specific module"""
    return logging.getLogger(name)


# Auto-setup when imported
if not logging.getLogger().handlers:
    setup_logging()