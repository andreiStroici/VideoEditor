# Video Processing Modules - Usage Guide

## Overview

This project provides a modular system for video and audio processing using FFmpeg. 

## Project Structure

```
/
├── base/                  # Common base processor <- let's consider turning all interfaces into abstract classes thtat inherit from base processor
├── filters/              
├── transformations/      
├── timing/               
├── text_operation/      
└── composition/         
```

## Core Concepts

### QTimeLine 

All operations use `QTimeLine` as a container to pass file information:

```python
from PySide6.QtCore import QTimeLine

timeline = QTimeLine()
timeline.setProperty("input_file", "path/to/video.mp4")
```

### Automatic Cleanup

The system automatically:
- Tracks the original file
- Deletes intermediate temporary files
- Preserves only the final output

Original files are never modified


### Method Naming Convention

- **Filters**: `applyFilter(qTimeLine) -> QTimeLine`
- **Transformations**: `applyTransformation(qTimeLine) -> QTimeLine`
- **Timing**: `applyOperation(qTimeLine) -> QTimeLine`
- **Text**: `applyText(videoClip) -> QTimeLine`
- **Composition**: `applyComposition(videoClip) -> QTimeLine`

## Module Usage

### 1. Filters Module

Apply visual and audio filters to video.

```python
from filters import BlurFilter, EdgeDetect, Volume
from PySide6.QtCore import QTimeLine

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

blur = BlurFilter(radius=15)
timeline = blur.applyFilter(timeline)

edge = EdgeDetect(method="sobel", threshold=0.2)
timeline = edge.applyFilter(timeline)

volume = Volume(gain_db=5.0)
timeline = volume.applyFilter(timeline)

output_file = timeline.property("input_file")
print(f"Result: {output_file}")
```

**Available Filters:**
- `BlurFilter(radius: int)` - Gaussian blur
- `EdgeDetect(method: str, threshold: float)` - Edge detection (sobel, canny, roberts, prewitt)
- `KernelFiltering(kernel: List[List[float]], normalize: bool)` - Custom convolution
- `NoiseReduction(strength: float, method: str)` - Reduce video noise
- `Volume(gain_db: float)` - Audio volume adjustment
- `Tempo(factor: float)` - Audio tempo change

### 2. Transformations Module


```python
from transformations import CropTransform, Rotate, ScaleTransform, PlaybackSpeed

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

crop = CropTransform(x=100, y=50, width=1280, height=720)
timeline = crop.applyTransformation(timeline)

rotate = Rotate(angle=45)
timeline = rotate.applyTransformation(timeline)

scale = ScaleTransform(scale_x=0.5, scale_y=0.5)
timeline = scale.applyTransformation(timeline)

speed = PlaybackSpeed(factor=1.5)
timeline = speed.applyTransformation(timeline)
```

**Available Transformations:**
- `PaddingTransform(top, bottom, left, right, color)` - Add padding
- `ChangeFPS(fps: int)` - Change frame rate
- `CropTransform(x, y, width, height)` - Crop video
- `PlaybackSpeed(factor: float)` - Change playback speed
- `Rotate(angle: float)` - Rotate video
- `Transpose(mode: str)` - Flip/rotate (clock, cclock, hflip, vflip)
- `ScaleTransform(scale_x, scale_y)` - Resize video

### 3. Timing Module

Time-based effects.

```python
from timing import FadeInOut

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

fade_in = FadeInOut(duration=2, type="in")
timeline = fade_in.applyOperation(timeline)

fade_out = FadeInOut(duration=3, type="out")
timeline = fade_out.applyOperation(timeline)

fade_both = FadeInOut(duration=1, type="both")
timeline = fade_both.applyOperation(timeline)
```

**Available Operations:**
- `FadeInOut(duration: int, type: str)` - Fade effects (in, out, both)

### 4. Text Operations Module

Add text overlays to video.

```python
from text_operation import DrawText

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

text = DrawText(
    text="Hello World!",
    position=(100, 50),
    font="Arial",
    size=48,
    color="white",
    opacity=0.9
)

timeline = text.applyText(timeline)
```

**Parameters:**
- `text: str` - Text to display
- `position: Tuple[int, int]` - (x, y) coordinates
- `font: str` - Font name
- `size: int` - Font size in pixels
- `color: str` - Color name or hex (#FF0000)
- `opacity: float` - Transparency (0.0 - 1.0)

### 5. Composition Module

Combine multiple clips or add audio effects.

```python
from composition import BlendVideos, Overlay, Echo
from PySide6.QtCore import QTimeLine

clip1 = QTimeLine()
clip1.setProperty("input_file", "video1.mp4")

clip2 = QTimeLine()
clip2.setProperty("input_file", "video2.mp4")

blend = BlendVideos(
    otherClip=clip2,
    alpha=0.5,
    mode="overlay"
)
result = blend.applyComposition(clip1)

overlay = Overlay(
    otherClip=clip2,
    alpha=0.8,
    position=(100, 50)
)
result = overlay.applyComposition(clip1)

echo = Echo(delay_ms=500, decay=0.6, mix=0.5)
result = echo.applyComposition(clip1)
```

**Available Compositions:**
- `BlendVideos(otherClip, alpha, mode)` - Blend two videos
- `Overlay(otherClip, alpha, position)` - Overlay video on another
- `Chorus(delay_ms, depth, mix)` - Chorus audio effect
- `Delay(delay_ms, mix)` - Simple audio delay
- `Echo(delay_ms, decay, mix)` - Audio echo with decay

## Chaining Operations

Operations can be chained together:

```python
from filters import BlurFilter, Volume
from transformations import CropTransform
from timing import FadeInOut
from text_operation import DrawText

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

blur = BlurFilter(radius=10)
timeline = blur.applyFilter(timeline)

crop = CropTransform(x=0, y=0, width=1920, height=1080)
timeline = crop.applyTransformation(timeline)

fade = FadeInOut(duration=2, type="both")
timeline = fade.applyOperation(timeline)

text = DrawText(text="My Video", position=(50, 50), size=36, color="white")
timeline = text.applyText(timeline)

volume = Volume(gain_db=3.0)
timeline = volume.applyFilter(timeline)

final_output = timeline.property("input_file")
print(f"Final video: {final_output}")
```

## Saving Final Output

To save the final result to a specific location:

```python
import shutil

timeline = QTimeLine()
timeline.setProperty("input_file", "input.mp4")

blur = BlurFilter(radius=10)
timeline = blur.applyFilter(timeline)

temp_output = timeline.property("input_file")

shutil.copy2(temp_output, "output/final_video.mp4")
```