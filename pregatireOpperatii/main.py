from abc import ABC, abstractmethod
import moviepy.editor as mp


class TimelineOperation(ABC):

    @abstractmethod
    def apply_operation(self, video_clip) -> mp.VideoFileClip:
        pass


class Transformations(ABC):

    @abstractmethod
    def apply_transformation(self, video_clip) -> mp.VideoFileClip:
        pass


class PlaybackSpeed(Transformations, ABC):
    def __init__(self, factor):
        self.factor = factor

    def apply_transformation(self, video_clip) -> mp.VideoFileClip:
        return video_clip.fx(mp.vfx.speedx, self.factor)


class GroupVideo(TimelineOperation, ABC):
    def __init__(self, video_clp):
        self.video = video_clp

    def apply_operation(self, video_clip) -> mp.VideoFileClip:
        return mp.concatenate_videoclips([self.video, video_clip], method="compose")


class CutVideo(TimelineOperation, ABC):
    def __init__(self, start_time):
        self.start_time = start_time

    def apply_operation(self, video_clip) -> mp.VideoFileClip:
        v = video_clip.subclip(self.start_time)
        return v


v1 = mp.VideoFileClip("v1.mp4")
v2 = mp.VideoFileClip("v2.mp4")

g = GroupVideo(v2)

f = g.apply_operation(v1)

c = CutVideo(10.123)
f2 = c.apply_operation(f)

ps = PlaybackSpeed(2.0)
f3 = ps.apply_transformation(v1)

f.write_videofile("final.mp4", codec="libx264", audio_codec="aac")
f2.write_videofile("final2.mp4", codec="libx264", audio_codec="aac")
f3.write_videofile("final3.mp4", codec="libx264", audio_codec="aac")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
