import subprocess
import tempfile
import os
from timeline_operation.timeline_operation_interface import TimelineOperation
from PySide6.QtCore import QTimeLine

class CutVideo(TimelineOperation):
    def __init__(self, start_time: int, end_time: int = None):
        self.start_time = max(0, int(start_time))
        self.end_time = int(end_time) if end_time is not None else None

    def applyOperation(self, qTimeLine: QTimeLine) -> QTimeLine:
        input_file = qTimeLine.property("input_file")
        original_file = qTimeLine.property("original_file")

        if not input_file or not os.path.exists(input_file):
            raise ValueError("Fisier de input inexistent in QTimeLine")

        if original_file is None:
            qTimeLine.setProperty("original_file", input_file)
            original_file = input_file

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_file)[1]).name

        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-ss", str(self.start_time)
        ]

        if self.end_time is not None:
            duration = self.end_time - self.start_time
            if duration <= 0:
                raise ValueError("end_time trebuie sa fie mai mare decat start_time")
            cmd.extend(["-t", str(duration)])

        cmd.extend([
            "-c", "copy",
            "-y",
            output_file
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-ss", str(self.start_time)
            ]

            if self.end_time is not None:
                duration = self.end_time - self.start_time
                cmd.extend(["-t", str(duration)])

            cmd.extend([
                "-y",
                output_file
            ])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                if os.path.exists(output_file):
                    os.unlink(output_file)
                raise RuntimeError(f"Eroare FFmpeg: {result.stderr}")

        if input_file != original_file and os.path.exists(input_file):
            os.unlink(input_file)

        qTimeLine.setProperty("input_file", output_file)
        return qTimeLine
