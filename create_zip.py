"""Helper script to create zip archive from output directory."""
import zipfile
from pathlib import Path

output_dir = Path('output')
zip_path = Path('sonora_voice_metadata_full.zip')

if not output_dir.exists():
    print(f"[ERROR] Output directory not found: {output_dir}")
    exit(1)

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    files_added = 0
    for file in output_dir.glob('*'):
        if file.is_file():
            zipf.write(file, file.name)
            print(f'  Added: {file.name}')
            files_added += 1

if files_added > 0:
    size_kb = zip_path.stat().st_size / 1024
    print(f'\n[OK] Zip created: {zip_path.absolute()}')
    print(f'   Size: {size_kb:.2f} KB')
    print(f'   Files: {files_added}')
else:
    print('[WARNING] No files were added to zip')

