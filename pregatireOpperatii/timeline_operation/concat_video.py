import subprocess
import tempfile
import os
from timeline_operation.timeline_operation_interface import TimelineOperation
from PySide6.QtCore import QTimeLine

class ConcatVideo(TimelineOperation):
    def __init__(self, otherClip: QTimeLine):
        self.otherClip = otherClip

    def applyOperation(self, qTimeLine: QTimeLine) -> QTimeLine:
        input_file1 = qTimeLine.property("input_file")
        input_file2 = self.otherClip.property("input_file")
        original_file = qTimeLine.property("original_file")

        if not input_file1 or not os.path.exists(input_file1):
            raise ValueError("Primul videoclip nu exista")
        if not input_file2 or not os.path.exists(input_file2):
            raise ValueError("Al doilea videoclip nu exista")

        if original_file is None:
            qTimeLine.setProperty("original_file", input_file1)
            original_file = input_file1

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_file1)[1]).name

        cmd = [
            "ffmpeg",
            "-i", input_file1,
            "-i", input_file2,
            "-filter_complex",
            "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-crf", "20",
            "-preset", "veryfast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-vsync", "2",
            "-y",
            output_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise RuntimeError(f"Eroare FFmpeg: {result.stderr}")

        if input_file1 != original_file and os.path.exists(input_file1):
            os.unlink(input_file1)

        qTimeLine.setProperty("input_file", output_file)
        return qTimeLine
