#!/usr/bin/env python3
import argparse
import sys
import os
from pathlib import Path

# Add project root to sys.path for internal imports
sys.path.append(os.getcwd())

try:
    from sonora.utils.voice_registry import save_character_voice
except ImportError:
    print("❌ Critical: Could not find sonora modules. Please run from project root.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="SONORA Studio: Character Casting Utility")
    parser.add_argument("--name", required=True, help="The name of the character to digitize")
    parser.add_argument("--source", required=True, help="Path to a clean 3-5s audio sample of the voice")
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Error: Source file '{args.source}' not found.")
        sys.exit(1)
        
    print(f"--- SONORA CASTING: Digitizing '{args.name.upper()}' ---")
    
    success = save_character_voice(args.name, str(source_path))
    
    if success:
        print(f"\n[SONORA CASTING] Character '{args.name}' has been successfully digitized and added to the registry.")
        print(f"Locked Asset: sonora/data/voices/{args.name.lower().replace(' ', '_')}.json")
    else:
        print(f"\n❌ Error: Failed to digitize character '{args.name}'. Check console logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
