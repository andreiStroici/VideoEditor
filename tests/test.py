import os
import sys
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QTimeLine
from filters import BlurFilter, EdgeDetect, KernelFiltering, NoiseReduction, Volume, Tempo
from transformations import CropTransform, Rotate, ScaleTransform, Transpose, PaddingTransform, ChangeFPS, PlaybackSpeed
from timing import FadeInOut
from text_operation import DrawText
from timeline_operation import CutVideo, ConcatVideo
from composition import Overlay, BlendVideos, Chorus, Delay, Echo

## run from project root!

def test_blur_filter():
    print("\nTesting BlurFilter...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    blur = BlurFilter(radius=10)
    timeline = blur.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "BlurFilter output file does not exist"

    dest_file = "tests/output_blur_filter.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"BlurFilter passed! Output: {dest_file}")
    return timeline

def test_crop_transform():
    print("\nTesting CropTransform...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    crop = CropTransform(x=100, y=50, width=1080, height=620)
    timeline = crop.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "CropTransform output file does not exist"

    dest_file = "tests/output_crop_transform.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"CropTransform passed! Output: {dest_file}")
    return timeline

def test_fade_in_out():
    print("\nTesting FadeInOut...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    fade = FadeInOut(duration=1, type="both")
    timeline = fade.applyOperation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "FadeInOut output file does not exist"

    dest_file = "tests/output_fade_in_out.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"FadeInOut passed! Output: {dest_file}")
    return timeline

def test_draw_text():
    print("\nTesting DrawText...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    text = DrawText(
        text="Test Video",
        position=(50, 50),
        font="Arial",
        size=48,
        color="white",
        opacity=0.9
    )
    timeline = text.applyText(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "DrawText output file does not exist"

    dest_file = "tests/output_draw_text.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"DrawText passed! Output: {dest_file}")
    return timeline

def test_cut_video():
    print("\nTesting CutVideo...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    cut = CutVideo(start_time=2, end_time=5)
    timeline = cut.applyOperation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "CutVideo output file does not exist"

    dest_file = "tests/output_cut_video.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"CutVideo passed! Output: {dest_file}")
    return timeline

def test_concat_video():
    print("\nTesting ConcatVideo...")
    timeline1 = QTimeLine()
    timeline1.setProperty("input_file", "tests/test_video.mp4")

    timeline2 = QTimeLine()
    timeline2.setProperty("input_file", "tests/sample2.mp4")

    concat = ConcatVideo(otherClip=timeline2)
    timeline1 = concat.applyOperation(timeline1)

    output_file = timeline1.property("input_file")
    assert os.path.exists(output_file), "ConcatVideo output file does not exist"

    dest_file = "tests/output_concat_video.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"ConcatVideo passed! Output: {dest_file}")
    return timeline1

def test_overlay():
    print("\nTesting Overlay...")
    timeline1 = QTimeLine()
    timeline1.setProperty("input_file", "tests/test_video.mp4")

    timeline2 = QTimeLine()
    timeline2.setProperty("input_file", "tests/sample_video.mp4")

    overlay = Overlay(otherClip=timeline2, alpha=0.5, position=(100, 100))
    timeline1 = overlay.applyComposition(timeline1)

    output_file = timeline1.property("input_file")
    assert os.path.exists(output_file), "Overlay output file does not exist"

    dest_file = "tests/output_overlay.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Overlay passed! Output: {dest_file}")
    return timeline1

def test_edge_detect():
    print("\nTesting EdgeDetect...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    edge = EdgeDetect(method="sobel", threshold=0.1)
    timeline = edge.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "EdgeDetect output file does not exist"

    dest_file = "tests/output_edge_detect.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"EdgeDetect passed! Output: {dest_file}")
    return timeline

def test_volume():
    print("\nTesting Volume...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    volume = Volume(gain_db=5.0)
    timeline = volume.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Volume output file does not exist"

    dest_file = "tests/output_volume.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Volume passed! Output: {dest_file}")
    return timeline

def test_rotate():
    print("\nTesting Rotate...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    rotate = Rotate(angle=45.0)
    timeline = rotate.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Rotate output file does not exist"

    dest_file = "tests/output_rotate.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Rotate passed! Output: {dest_file}")
    return timeline

def test_scale():
    print("\nTesting ScaleTransform...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    scale = ScaleTransform(scale_x=0.5, scale_y=0.5)
    timeline = scale.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "ScaleTransform output file does not exist"

    dest_file = "tests/output_scale.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"ScaleTransform passed! Output: {dest_file}")
    return timeline

def test_blend_videos():
    print("\nTesting BlendVideos...")
    timeline1 = QTimeLine()
    timeline1.setProperty("input_file", "tests/test_video.mp4")

    timeline2 = QTimeLine()
    timeline2.setProperty("input_file", "tests/sample_video.mp4")

    blend = BlendVideos(otherClip=timeline2, alpha=0.5, mode="overlay")
    timeline1 = blend.applyComposition(timeline1)

    output_file = timeline1.property("input_file")
    assert os.path.exists(output_file), "BlendVideos output file does not exist"

    dest_file = "tests/output_blend.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"BlendVideos passed! Output: {dest_file}")
    return timeline1

def test_noise_reduction():
    print("\nTesting NoiseReduction...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    noise = NoiseReduction(strength=5)
    timeline = noise.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "NoiseReduction output file does not exist"

    dest_file = "tests/output_noise_reduction.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"NoiseReduction passed! Output: {dest_file}")
    return timeline

def test_tempo():
    print("\nTesting Tempo...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    tempo = Tempo(factor=1.5)
    timeline = tempo.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Tempo output file does not exist"

    dest_file = "tests/output_tempo.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Tempo passed! Output: {dest_file}")
    return timeline

def test_kernel_filtering():
    print("\nTesting KernelFiltering...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    kernel = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
    kernel_filter = KernelFiltering(kernel=kernel)
    timeline = kernel_filter.applyFilter(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "KernelFiltering output file does not exist"

    dest_file = "tests/output_kernel.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"KernelFiltering passed! Output: {dest_file}")
    return timeline

def test_transpose():
    print("\nTesting Transpose...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    transpose = Transpose(mode="cclock_flip")
    timeline = transpose.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Transpose output file does not exist"

    dest_file = "tests/output_transpose.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Transpose passed! Output: {dest_file}")
    return timeline

def test_padding():
    print("\nTesting PaddingTransform...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    padding = PaddingTransform(top=50, bottom=50, left=100, right=100)
    timeline = padding.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "PaddingTransform output file does not exist"

    dest_file = "tests/output_padding.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"PaddingTransform passed! Output: {dest_file}")
    return timeline

def test_change_fps():
    print("\nTesting ChangeFPS...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    change_fps = ChangeFPS(fps=30)
    timeline = change_fps.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "ChangeFPS output file does not exist"

    dest_file = "tests/output_change_fps.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"ChangeFPS passed! Output: {dest_file}")
    return timeline

def test_playback_speed():
    print("\nTesting PlaybackSpeed...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    playback = PlaybackSpeed(factor=2.0)
    timeline = playback.applyTransformation(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "PlaybackSpeed output file does not exist"

    dest_file = "tests/output_playback_speed.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"PlaybackSpeed passed! Output: {dest_file}")
    return timeline

def test_chorus():
    print("\nTesting Chorus...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    chorus = Chorus(delay_ms=40, depth=0.3, mix=0.5)
    timeline = chorus.applyComposition(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Chorus output file does not exist"

    dest_file = "tests/output_chorus.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Chorus passed! Output: {dest_file}")
    return timeline

def test_delay():
    print("\nTesting Delay...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    delay = Delay(delay_ms=500, mix=0.5)
    timeline = delay.applyComposition(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Delay output file does not exist"

    dest_file = "tests/output_delay.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Delay passed! Output: {dest_file}")
    return timeline

def test_echo():
    print("\nTesting Echo...")
    timeline = QTimeLine()
    timeline.setProperty("input_file", "tests/test_video.mp4")

    echo = Echo(delay_ms=1000, decay=0.6)
    timeline = echo.applyComposition(timeline)

    output_file = timeline.property("input_file")
    assert os.path.exists(output_file), "Echo output file does not exist"

    dest_file = "tests/output_echo.mp4"
    shutil.copy2(output_file, dest_file)
    print(f"Echo passed! Output: {dest_file}")
    return timeline

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ALL MODULES")
    print("=" * 60)

    try:
        test_blur_filter()
        test_edge_detect()
        test_noise_reduction()
        test_volume()
        test_tempo()
        test_kernel_filtering()
        test_crop_transform()
        test_rotate()
        test_scale()
        test_transpose()
        test_padding()
        test_change_fps()
        test_playback_speed()
        test_fade_in_out()
        test_draw_text()
        test_cut_video()
        test_concat_video()
        test_overlay()
        test_blend_videos()
        test_chorus()
        test_delay()
        test_echo()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
