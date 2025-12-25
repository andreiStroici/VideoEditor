import os
import hashlib
import subprocess
import time
import shutil
from PySide6.QtCore import QThread, Signal

class FileImporterWorker(QThread):
    finished_success = Signal(str, str)
    
    def __init__(self, file_path, cache_dir):
        super().__init__()
        self.file_path = file_path
        self.cache_dir = cache_dir

    def run(self):
        if not os.path.exists(self.file_path):
            self.finished_success.emit(self.file_path, self.file_path)
            return

        base_name = os.path.basename(self.file_path)
        name, ext = os.path.splitext(base_name)
        file_hash = hashlib.md5(f"{self.file_path}_{time.time()}".encode()).hexdigest()[:8]
        
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
        
        if ext.lower() in audio_exts:
            new_name = f"{name}_{file_hash}_converted.mp4"
            new_path = os.path.join(self.cache_dir, new_name)
            
            cmd = (
                f'ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=30 '
                f'-i "{self.file_path}" '
                f'-c:v libx264 -g 1 -pix_fmt yuv420p ' 
                f'-c:a aac -b:a 192k -ac 2 '
                f'-shortest "{new_path}"'
            )
            try:
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.finished_success.emit(self.file_path, new_path)
            except Exception as e:
                print(f"Conversion Error: {e}")
                self.finished_success.emit(self.file_path, self.file_path)
        else:
            new_name = f"{name}_{file_hash}{ext}"
            new_path = os.path.join(self.cache_dir, new_name)
            try:
                shutil.copy2(self.file_path, new_path)
                self.finished_success.emit(self.file_path, new_path)
            except:
                self.finished_success.emit(self.file_path, self.file_path)