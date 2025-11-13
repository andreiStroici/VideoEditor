from abc import ABC, abstractmethod
import numpy as np
import subprocess
import json

# ==========================
# Clasa care reprezintă video-ul în memorie
# ==========================
class VideoClipInMemory:
    def __init__(self, video_path=None, array=None, width=None, height=None, fps=None):
        if video_path:
            self.array, self.width, self.height, self.fps = self.load_video(video_path)
        elif array is not None:
            self.array = array
            self.height = height
            self.width = width
            self.fps = fps
        else:
            raise ValueError("Trebuie să specifici video_path sau array.")

    def load_video(self, path):
        # Obține info video cu ffprobe
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
            "-of", "json",
            path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        stream = info['streams'][0]
        width = int(stream['width'])
        height = int(stream['height'])
        fps = eval(stream['r_frame_rate'])
        num_frames = int(stream.get("nb_frames", 0))

        # Citește video ca raw frames
        cmd = [
            "ffmpeg",
            "-i", path,
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-"
        ]
        proc = subprocess.run(cmd, capture_output=True)
        video_array = np.frombuffer(proc.stdout, np.uint8).reshape([num_frames, height, width, 3])
        return video_array, width, height, fps

    def write_to_file(self, path):
        # Scrie video folosind ffmpeg prin subprocess
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            path
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for frame in self.array:
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        proc.wait()


# ==========================
# Abstract base classes
# ==========================
class TimelineOperation(ABC):
    @abstractmethod
    def apply_operation(self, video_clip: VideoClipInMemory) -> VideoClipInMemory:
        pass

class Transformations(ABC):
    @abstractmethod
    def apply_transformation(self, video_clip: VideoClipInMemory) -> VideoClipInMemory:
        pass


# ==========================
# Transformations concrete
# ==========================
class PlaybackSpeed(Transformations):
    def __init__(self, factor):
        self.factor = factor

    def apply_transformation(self, video_clip: VideoClipInMemory) -> VideoClipInMemory:
        indices = (np.arange(0, len(video_clip.array), 1/self.factor)).astype(int)
        indices = np.clip(indices, 0, len(video_clip.array)-1)
        new_array = video_clip.array[indices]
        return VideoClipInMemory(array=new_array, width=video_clip.width, height=video_clip.height, fps=video_clip.fps)


# ==========================
# TimelineOperations concrete
# ==========================
class GroupVideo(TimelineOperation):
    def __init__(self, video_clip: VideoClipInMemory):
        self.video = video_clip

    def apply_operation(self, video_clip: VideoClipInMemory) -> VideoClipInMemory:
        new_array = np.concatenate([self.video.array, video_clip.array], axis=0)
        return VideoClipInMemory(array=new_array, width=self.video.width, height=self.video.height, fps=self.video.fps)

class CutVideo(TimelineOperation):
    def __init__(self, start_time: float):
        self.start_time = start_time

    def apply_operation(self, video_clip: VideoClipInMemory) -> VideoClipInMemory:
        start_frame = int(self.start_time * video_clip.fps)
        new_array = video_clip.array[start_frame:]
        return VideoClipInMemory(array=new_array, width=video_clip.width, height=video_clip.height, fps=video_clip.fps)


class VideoEditor(ABC):
    pass


class History(ABC):
    def __init__(self):
        self.__undo = []
        self.__redo = []

    def undo(self):
        video = self.__undo.pop()
        self.__redo.append(video)
        return video

    def redo(self):
        video = self.__redo.pop()
        self.__undo.append(video)
        return video

    def save(self, video:VideoClipInMemory):
        self.__undo.append(video)

    def clear_history(self):
        self.__undo.clear()
        self.__redo.clear()

    @staticmethod
    def create_instance(self):
        self.history = History()
        return self.history

# ==========================
# Exemplu de utilizare
# ==========================
v1 = VideoClipInMemory("v1.mp4")
v2 = VideoClipInMemory("v2.mp4")

# Concatenare
g = GroupVideo(v2)
f = g.apply_operation(v1)

# Cut
c = CutVideo(10.123)
f2 = c.apply_operation(f)

# Accelerare
ps = PlaybackSpeed(0.5)
f3 = ps.apply_transformation(v1)

# Salvare pe disc
f.write_to_file("final.mp4")
f2.write_to_file("final2.mp4")
f3.write_to_file("final3.mp4")
