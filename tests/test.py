import os
import sys
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QTimeLine
from filters import BlurFilter
from transformations import CropTransform
from timing import FadeInOut
from text_operation import DrawText
from timeline_operation import CutVideo, ConcatVideo
from composition import Overlay

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

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ALL MODULES")
    print("=" * 60)

    try:
        test_blur_filter()
        test_crop_transform()
        test_fade_in_out()
        test_draw_text()
        test_cut_video()
        test_concat_video()
        test_overlay()

        test_concat_video()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
