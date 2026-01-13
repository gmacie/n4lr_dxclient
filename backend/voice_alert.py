# backend/voice_alert.py - Text-to-speech voice alerts for DX spots
"""
Provides voice alerts using pyttsx3 for spotted callsigns
"""

import threading
import queue
from backend.app_logging import get_logger

logger = get_logger(__name__)

# Global TTS engine and queue
_tts_engine = None
_alert_queue = queue.Queue()
_worker_thread = None
_running = False


def _init_engine():
    """Initialize the TTS engine (lazy loading)"""
    global _tts_engine
    
    if _tts_engine is not None:
        return _tts_engine
    
    try:
        import pyttsx3
        _tts_engine = pyttsx3.init()
        
        # Configure voice properties (optional)
        _tts_engine.setProperty('rate', 150)    # Speed (words per minute)
        _tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Optional: Set voice (commented out - uses system default)
        # voices = _tts_engine.getProperty('voices')
        # _tts_engine.setProperty('voice', voices[0].id)  # 0=male, 1=female on Windows
        
        logger.info("Voice alert engine initialized")
        return _tts_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize voice alert engine: {e}")
        return None


def _alert_worker():
    """Background thread that processes voice alerts"""
    global _running
    
    engine = _init_engine()
    if not engine:
        logger.error("Voice alert worker: Engine initialization failed")
        return
    
    logger.info("Voice alert worker started")
    
    while _running:
        try:
            # Wait for an alert (blocking with timeout)
            message = _alert_queue.get(timeout=1.0)
            
            if message is None:  # Shutdown signal
                break
            
            # Speak the message
            logger.info(f"VOICE ALERT - Speaking: {message}")
            engine.say(message)
            engine.runAndWait()
            
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Voice alert error: {e}")
    
    logger.info("Voice alert worker stopped")


def start_voice_alerts():
    """Start the voice alert worker thread"""
    global _worker_thread, _running
    
    if _running:
        return  # Already running
    
    _running = True
    _worker_thread = threading.Thread(target=_alert_worker, daemon=True)
    _worker_thread.start()
    logger.info("Voice alerts enabled")


def stop_voice_alerts():
    """Stop the voice alert worker thread"""
    global _running, _alert_queue
    
    if not _running:
        return
    
    _running = False
    _alert_queue.put(None)  # Shutdown signal
    logger.info("Voice alerts disabled")


def speak_callsign(callsign, band=None):
    """
    Queue a callsign to be spoken
    
    Args:
        callsign: The callsign to speak (e.g., "K1ABC")
        band: Optional band (e.g., "20M")
    """
    if not _running:
        start_voice_alerts()
    
    # Format the message
    if band:
        # Convert band to spoken form (e.g., "20M" -> "twenty meters")
        band_spoken = _format_band(band)
        message = f"{_format_callsign(callsign)} on {band_spoken}"
    else:
        message = _format_callsign(callsign)
    
    # Queue the alert
    _alert_queue.put(message)


def _format_callsign(callsign):
    """
    Format callsign for better speech
    
    Examples:
        K1ABC -> "K one A B C"
        W2XYZ -> "W two X Y Z"
        3B7A -> "three B seven A"
    """
    result = []
    for char in callsign.upper():
        if char.isdigit():
            # Speak numbers as words
            numbers = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', 
                      '4': 'four', '5': 'five', '6': 'six', '7': 'seven',
                      '8': 'eight', '9': 'nine'}
            result.append(numbers.get(char, char))
        elif char.isalpha():
            # Speak letters individually
            result.append(char)
        elif char == '/':
            result.append('stroke')
    
    return ' '.join(result)


def _format_band(band):
    """
    Format band for speech
    
    Examples:
        20M -> "twenty meters"
        6M -> "six meters"
        70CM -> "seventy centimeters"
    """
    band = band.upper()
    
    if band.endswith('M'):
        # Meters
        num = band[:-1]
        if num == '6':
            return "six meters"
        elif num == '10':
            return "ten meters"
        elif num == '12':
            return "twelve meters"
        elif num == '15':
            return "fifteen meters"
        elif num == '17':
            return "seventeen meters"
        elif num == '20':
            return "twenty meters"
        elif num == '30':
            return "thirty meters"
        elif num == '40':
            return "forty meters"
        elif num == '60':
            return "sixty meters"
        elif num == '80':
            return "eighty meters"
        elif num == '160':
            return "one sixty meters"
        else:
            return f"{num} meters"
    elif band.endswith('CM'):
        # Centimeters
        num = band[:-2]
        return f"{num} centimeters"
    else:
        return band


# Auto-start on import (optional - can be disabled)
# start_voice_alerts()


if __name__ == "__main__":
    # Test the voice alerts
    print("Testing voice alerts...")
    
    start_voice_alerts()
    
    # Test various callsigns
    speak_callsign("K1ABC", "20M")
    speak_callsign("W2XYZ", "15M")
    speak_callsign("3B7A", "10M")
    speak_callsign("FT5ZM")
    
    # Wait for alerts to finish
    import time
    time.sleep(10)
    
    stop_voice_alerts()
    print("Test complete!")