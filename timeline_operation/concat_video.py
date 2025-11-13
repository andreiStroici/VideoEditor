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

        concat_list = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        concat_list.write(f"file '{os.path.abspath(input_file1)}'\n")
        concat_list.write(f"file '{os.path.abspath(input_file2)}'\n")
        concat_list.close()

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_file1)[1]).name

        try:
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list.name,
                "-c", "copy",
                "-y",
                output_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                cmd = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list.name,
                    "-y",
                    output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    if os.path.exists(output_file):
                        os.unlink(output_file)
                    raise RuntimeError(f"Eroare FFmpeg: {result.stderr}")

        finally:
            if os.path.exists(concat_list.name):
                os.unlink(concat_list.name)

        if input_file1 != original_file and os.path.exists(input_file1):
            os.unlink(input_file1)

        qTimeLine.setProperty("input_file", output_file)
        return qTimeLine
