from abc import ABC
import subprocess
import tempfile
import os
from PySide6.QtCore import QTimeLine

class BaseProcessor(ABC):
    def _apply_ffmpeg(self, qTimeLine: QTimeLine, filter_str: str, filter_type: str = "video") -> QTimeLine:
        input_file = qTimeLine.property("input_file")
        original_file = qTimeLine.property("original_file")

        if not input_file or not os.path.exists(input_file):
            raise ValueError("Fisier de input inexistent in QTimeLine")

        if original_file is None:
            qTimeLine.setProperty("original_file", input_file)
            original_file = input_file

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_file)[1]).name

        if filter_type == "video":
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-vf", filter_str,
                "-c:a", "copy",
                "-y",
                output_file
            ]
        elif filter_type == "audio":
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-af", filter_str,
                "-c:v", "copy",
                "-y",
                output_file
            ]
        else:
            raise ValueError("filter_type must be 'video' or 'audio'")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise RuntimeError(f"Eroare FFmpeg: {result.stderr}")

        if input_file != original_file and os.path.exists(input_file):
            os.unlink(input_file)

        qTimeLine.setProperty("input_file", output_file)
        return qTimeLine
