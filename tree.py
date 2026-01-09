import os
from pathlib import Path

EXCLUDE = {'venv', '__pycache__', '.git', 'build', 'dist', '.vscode', '.idea'}
EXCLUDE_EXT = {'.pyc', '.pyo', '.spec'}

def print_tree(directory, prefix="", max_depth=5, current_depth=0):
    if current_depth >= max_depth:
        return
    
    path = Path(directory)
    items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    
    for i, item in enumerate(items):
        if item.name in EXCLUDE or item.suffix in EXCLUDE_EXT:
            continue
        
        is_last = i == len(items) - 1
        print(f"{prefix}{'└── ' if is_last else '├── '}{item.name}")
        
        if item.is_dir():
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(item, new_prefix, max_depth, current_depth + 1)

if __name__ == "__main__":
    print("n4lr_dxclient/")
    print_tree(".", "", max_depth=4)