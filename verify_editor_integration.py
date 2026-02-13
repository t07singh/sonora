
import sys
import os

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"Project root: {current_dir}")
print(f"Sys path: {sys.path}")

try:
    print("Attempting to import AudioEditorUI...")
    from sonora.editor_ui import AudioEditorUI
    print("[OK] Successfully imported AudioEditorUI")
    
    print("Attempting to instantiate AudioEditorUI...")
    editor = AudioEditorUI(audio_path=None)
    print("[OK] Successfully instantiated AudioEditorUI")
    
    print("Checking internal components...")
    if hasattr(editor, 'audio_separator'):
        print(f"[OK] AudioSeparator present: {editor.audio_separator}")
    else:
        print("[ERROR] AudioSeparator MISSING")

except ImportError as e:
    print(f"[ERROR] ImportError: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
