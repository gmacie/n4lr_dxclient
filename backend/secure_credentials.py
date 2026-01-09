"""
Secure credential storage using OS keyring with file fallback
Stores LoTW credentials securely in:
1. Windows Credential Manager
2. macOS Keychain
3. Linux Secret Service
4. Fallback to encrypted file if keyring unavailable
"""

import keyring
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64
import hashlib

KEYRING_SERVICE = "N4LR_DXClient"
KEYRING_USERNAME_KEY = "lotw_username"
KEYRING_PASSWORD_KEY = "lotw_password"
FALLBACK_FILE = Path("lotw_credentials.enc")
KEY_FILE = Path(".credential_key")


def _get_encryption_key():
    """Get or create encryption key for fallback file storage"""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    else:
        # Generate key from machine-specific data
        import platform
        import getpass
        
        # Combine machine name + username for unique key per machine/user
        unique_string = f"{platform.node()}{getpass.getuser()}N4LR_DXClient_v1"
        key = hashlib.sha256(unique_string.encode()).digest()
        key_encoded = base64.urlsafe_b64encode(key)
        
        KEY_FILE.write_bytes(key_encoded)
        return key_encoded


def _encrypt_data(data):
    """Encrypt data using Fernet"""
    key = _get_encryption_key()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()


def _decrypt_data(encrypted):
    """Decrypt data using Fernet"""
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted.encode()).decode()
    except:
        return None


def save_lotw_credentials(username, password):
    """
    Save LoTW credentials securely
    
    Tries OS keyring first, falls back to encrypted file
    """
    if not username or not password:
        return False
    
    # Try OS keyring first
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY, username)
        keyring.set_password(KEYRING_SERVICE, KEYRING_PASSWORD_KEY, password)
        
        # Clear any fallback file if keyring works
        if FALLBACK_FILE.exists():
            FALLBACK_FILE.unlink()
        
        print("LoTW credentials saved to system keyring")
        return True
        
    except Exception as e:
        print(f"Keyring not available ({e}), using encrypted file fallback")
        
        # Fallback to encrypted file
        try:
            data = {
                "username": _encrypt_data(username),
                "password": _encrypt_data(password)
            }
            
            FALLBACK_FILE.write_text(json.dumps(data))
            print("LoTW credentials saved to encrypted file")
            return True
            
        except Exception as e2:
            print(f"ERROR: Failed to save credentials: {e2}")
            return False


def get_lotw_credentials():
    """
    Retrieve LoTW credentials
    
    Returns: (username, password) or (None, None) if not found
    """
    # Try OS keyring first
    try:
        username = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY)
        password = keyring.get_password(KEYRING_SERVICE, KEYRING_PASSWORD_KEY)
        
        if username and password:
            return (username, password)
            
    except Exception as e:
        print(f"Keyring not available, trying encrypted file")
    
    # Fallback to encrypted file
    if FALLBACK_FILE.exists():
        try:
            data = json.loads(FALLBACK_FILE.read_text())
            username = _decrypt_data(data.get("username", ""))
            password = _decrypt_data(data.get("password", ""))
            
            if username and password:
                return (username, password)
                
        except Exception as e:
            print(f"ERROR: Failed to read credentials: {e}")
    
    return (None, None)


def delete_lotw_credentials():
    """Delete stored credentials"""
    # Try keyring
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY)
        keyring.delete_password(KEYRING_SERVICE, KEYRING_PASSWORD_KEY)
    except:
        pass
    
    # Delete fallback file
    if FALLBACK_FILE.exists():
        FALLBACK_FILE.unlink()
    
    print("LoTW credentials deleted")


def credentials_exist():
    """Check if credentials are stored"""
    username, password = get_lotw_credentials()
    return username is not None and password is not None


if __name__ == "__main__":
    # Test the module
    print("Testing secure credential storage...")
    
    # Save test credentials
    save_lotw_credentials("N4LR", "test_password_123")
    
    # Retrieve
    user, pw = get_lotw_credentials()
    print(f"Retrieved: username={user}, password={'*' * len(pw) if pw else 'None'}")
    
    # Check existence
    print(f"Credentials exist: {credentials_exist()}")
    
    # Delete
    delete_lotw_credentials()
    print(f"After delete: {credentials_exist()}")