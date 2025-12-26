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
            new_name = f"{name}_{file_hash}_converted.mov"
            new_path = os.path.join(self.cache_dir, new_name)
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bg_image_path = os.path.join(base_dir, "icons", "blackCat.jpg")
            if not os.path.exists(bg_image_path):
                bg_image_path = os.path.join(base_dir, "icons", "blackCat.png")
            
            if os.path.exists(bg_image_path):
                cmd = (
                    f'ffmpeg -y -loop 1 -i "{bg_image_path}" '
                    f'-i "{self.file_path}" '
                    f'-c:v libx264 -tune stillimage -pix_fmt yuv420p '
                    f'-vf "scale=1920:1080,format=yuv420p" '
                    f'-c:a pcm_s16le -ar 48000 -ac 2 '
                    f'-shortest "{new_path}"'
                )
            else:
                cmd = (
                    f'ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=30 '
                    f'-i "{self.file_path}" '
                    f'-c:v libx264 -g 30 -pix_fmt yuv420p ' 
                    f'-c:a pcm_s16le -ar 48000 -ac 2 '
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