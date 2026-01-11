import os
import shutil
import hashlib
import subprocess
import tempfile
# New Block
import atexit
import sys
# End OF Block
from PySide6.QtCore import QObject, Signal, QTimeLine
try:
    from transformations.crop_transform import CropTransform
    from transformations.change_fps import ChangeFPS
    from transformations.padding_transform import PaddingTransform
    from transformations.playback_speed import PlaybackSpeed
    from transformations.rotate_transform import Rotate
    from transformations.scale_transform import ScaleTransform
    from transformations.transpose_transform import Transpose
    from timing.fade_in_out import FadeInOut
    from text_operation.draw_text import DrawText
    from filters.tempo_filter import Tempo
    from filters.kernel_filtering import KernelFiltering
    from filters.edge_detect_filter import EdgeDetect
    from filters.blur_filter import BlurFilter
    from filters.volume_filter import Volume
    from filters.noise_reduction_filter import NoiseReduction
    from composition.overlay import Overlay
    from composition.blend_videos import BlendVideos
    from composition.echo import Echo
    from composition.delay import Delay
    from composition.chorus import Chorus
except ImportError as e:
    print(f"Eroare import module externe:{e}")

class FilterBridge(QObject):
    processing_finished = Signal(str, dict) 
    processing_error = Signal(str)

    def __init__(self, cache_dir):
        super().__init__()
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        atexit.register(self._cleanup_on_exit)

    def _cleanup_on_exit(self):

        try:
            current_pid = os.getpid()
            
            if sys.platform == 'win32':
                subprocess.run(
                    f'taskkill /F /FI "PARENTPROCESSID eq {current_pid}" /IM ffmpeg.exe', 
                    shell=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(
                    f'pkill -P {current_pid} ffmpeg', 
                    shell=True,
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass 


    def get_file_duration(self, file_path):
        if not os.path.exists(file_path): return 0
        try:
            cmd = [
                'ffprobe', '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                file_path
            ]
            result = subprocess.check_output(cmd, encoding='utf-8').strip()
            return int(float(result) * 1000)
        except:
            return 0

    def get_video_dimensions(self, file_path):
        if not os.path.exists(file_path): 
            return 0, 0
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-select_streams', 'v:0', 
                '-show_entries', 'stream=width,height', 
                '-of', 'csv=s=x:p=0', 
                file_path
            ]
            result = subprocess.check_output(cmd, encoding='utf-8').strip()
            parts = result.split('x')
            if len(parts) == 2: 
                return int(parts[0]), int(parts[1])
        except Exception as e:
            pass
        return 1920, 1080

    def _prepare_secondary_clip(self, secondary_path, target_w, target_h):
        sec_w, sec_h = self.get_video_dimensions(secondary_path)
        if sec_w == target_w and sec_h == target_h:
            return secondary_path
        
        temp_resized = tempfile.NamedTemporaryFile(delete=False, suffix="_resized.mp4").name
        
        cmd = [
            'ffmpeg', '-y',
            '-i', secondary_path,
            '-vf', f'scale={target_w}:{target_h},format=yuv420p',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-c:a', 'copy',
            temp_resized
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return temp_resized

    def process_clip(self, original_path, filter_stack):
        if not os.path.exists(original_path):
            self.processing_error.emit("Fisierul sursa nu exista.")
            return

        qt_timeline = QTimeLine()
        qt_timeline.setProperty("input_file", original_path)
        qt_timeline.setProperty("original_file", original_path) 

        try:
            main_w, main_h = self.get_video_dimensions(original_path)
            transforms = filter_stack.get('Transforms', {}).get('Video', {})
            fps_data = transforms.get('Change FPS', {})
            if fps_data.get('enabled', False):
                target_fps = int(fps_data.get('fps', 30))
                qt_timeline = ChangeFPS(fps=target_fps).applyTransformation(qt_timeline)
            speed_data = transforms.get('Playback speed', {})
            if speed_data.get('enabled', False):
                factor = float(speed_data.get('Factor', 1.0))
                if factor > 0.01:
                    qt_timeline = PlaybackSpeed(factor=factor).applyTransformation(qt_timeline)
            crop_data = transforms.get('Crop', {})
            if crop_data.get('enabled', False):
                req_w = int(crop_data.get('Width', 0))
                req_h = int(crop_data.get('Height', 0))
                req_x = int(crop_data.get('X', 0))
                req_y = int(crop_data.get('Y', 0))
                
                safe_w = min(req_w, main_w) if req_w > 0 else main_w
                safe_h = min(req_h, main_h) if req_h > 0 else main_h
                
                safe_x = req_x
                if safe_x + safe_w > main_w:
                    safe_x = max(0, main_w - safe_w)
                
                safe_y = req_y
                if safe_y + safe_h > main_h:
                    safe_y = max(0, main_h - safe_h)

                qt_timeline = CropTransform(
                    x=safe_x, 
                    y=safe_y, 
                    width=safe_w, 
                    height=safe_h
                ).applyTransformation(qt_timeline)
                
                main_w = safe_w
                main_h = safe_h

            pad_data = transforms.get('Padding', {})
            if pad_data.get('enabled', False):
                p_top = max(0, int(pad_data.get('Top', 0)))
                p_bottom = max(0, int(pad_data.get('Bottom', 0)))
                p_left = max(0, int(pad_data.get('Left', 0)))
                p_right = max(0, int(pad_data.get('Right', 0)))
                p_color = pad_data.get('Color', 'black')

                if p_top > 0 or p_bottom > 0 or p_left > 0 or p_right > 0:
                    qt_timeline = PaddingTransform(
                        top=p_top, 
                        bottom=p_bottom, 
                        left=p_left, 
                        right=p_right, 
                        color=p_color
                    ).applyTransformation(qt_timeline)
                    main_w = main_w + p_left + p_right
                    main_h = main_h + p_top + p_bottom

            rot_data = transforms.get('Rotate', {})
            if rot_data.get('enabled', False):
                angle = float(rot_data.get('Angle', 0.0))
                qt_timeline = Rotate(angle=angle).applyTransformation(qt_timeline)

            scale_data = transforms.get('Scale', {})
            if scale_data.get('enabled', False):
                sx = float(scale_data.get('Scale x', 1.0))
                sy = float(scale_data.get('Scale y', 1.0))
                if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
                    qt_timeline = ScaleTransform(scale_x=sx, scale_y=sy).applyTransformation(qt_timeline)
                    main_w = int(main_w * sx)
                    main_h = int(main_h * sy)

            trans_data = transforms.get('Transpose', {})
            if trans_data.get('enabled', False):
                mode = trans_data.get('Mode', 'clock')
                qt_timeline = Transpose(mode=mode).applyTransformation(qt_timeline)
                if 'clock' in mode and 'flip' not in mode:
                     main_w, main_h = main_h, main_w

            timing_video = filter_stack.get('Timing', {}).get('Video', {})
            fade_data = timing_video.get('Fade in', {})
            if fade_data.get('enabled', False):
                duration = int(fade_data.get('Duration', 1))
                fade_type = fade_data.get('Type', 'both')
                qt_timeline = FadeInOut(duration=duration, type=fade_type).applyOperation(qt_timeline)

            text_ops = filter_stack.get('Text operation', {}).get('Video', {})
            text_data = text_ops.get('Text', {})
            if text_data.get('enabled', False):
                text_content = text_data.get('Text', "")
                position = text_data.get('Position', (10, 10))
                font = text_data.get('Font', "Arial")
                size = text_data.get('Size', 24)
                color = text_data.get('Color', "white")
                opacity = float(text_data.get('Opacity', 1.0))

                qt_timeline = DrawText(
                    text=text_content,
                    position=position,
                    font=font,
                    size=size,
                    color=color,
                    opacity=opacity
                ).applyText(qt_timeline)

            filters_video = filter_stack.get('Filters', {}).get('Video', {})
            tempo_data = filters_video.get('Tempo', {})
            if tempo_data.get('enabled', False):
                factor = float(tempo_data.get('Factor', 1.0))
                qt_timeline = Tempo(factor=factor).applyFilter(qt_timeline)
            
            kernel_data = filters_video.get('Kernel Filtering', {})
            if kernel_data.get('enabled', False):
                kernel_matrix = kernel_data.get('Kernel', [])
                normalize = kernel_data.get('Normalize', True)
                if kernel_matrix and len(kernel_matrix) > 0:
                    qt_timeline = KernelFiltering(kernel=kernel_matrix, normalize=normalize).applyFilter(qt_timeline)
            
            edge_data = filters_video.get('Edge Detect', {})
            if edge_data.get('enabled', False):
                method = edge_data.get('Method', 'sobel')
                thresh = float(edge_data.get('Threshold', 0.1))
                qt_timeline = EdgeDetect(method=method, threshold=thresh).applyFilter(qt_timeline)

            blur_data = filters_video.get('Blur', {})
            if blur_data.get('enabled', False):
                radius = int(blur_data.get('Radius', 10))
                qt_timeline = BlurFilter(radius=radius).applyFilter(qt_timeline)
            
            vol_data = filters_video.get('Volume', {})
            if vol_data.get('enabled', False):
                gain = float(vol_data.get('Gain', 0.0))
                qt_timeline = Volume(gain_db=gain).applyFilter(qt_timeline)

            noise_data = filters_video.get('Noise Reduction', {})
            if noise_data.get('enabled', False):
                strength = float(noise_data.get('Strength', 1.0))
                method = noise_data.get('Method', 'hqdn3d')
                qt_timeline = NoiseReduction(strength=strength, method=method).applyFilter(qt_timeline)

            comp_data = filter_stack.get('Composition', {}).get('Video', {})
            overlay_data = comp_data.get('Overlay', {})
            
            if overlay_data.get('enabled', False):
                ov_path = overlay_data.get('overlay_path')
                if ov_path and os.path.exists(ov_path):
                    alpha = float(overlay_data.get('Alpha', 1.0))
                    pos = overlay_data.get('Position', (0,0))
                    
                    dummy_other_clip = QTimeLine()
                    dummy_other_clip.setProperty("input_file", ov_path)
                    
                    qt_timeline = Overlay(otherClip=dummy_other_clip, alpha=alpha, position=pos).applyComposition(qt_timeline)

            blend_data = comp_data.get('Blend videos', {})
            if blend_data.get('enabled', False):
                bl_path = blend_data.get('blend_path')
                if bl_path and os.path.exists(bl_path):
                    alpha = float(blend_data.get('Alpha', 0.5))
                    mode = blend_data.get('Mode', 'overlay')
                    
                    prepared_path = self._prepare_secondary_clip(bl_path, main_w, main_h)
                    
                    dummy_blend_clip = QTimeLine()
                    dummy_blend_clip.setProperty("input_file", prepared_path)
                    
                    qt_timeline = BlendVideos(otherClip=dummy_blend_clip, alpha=alpha, mode=mode).applyComposition(qt_timeline)

            comp_audio = filter_stack.get('Composition', {}).get('Audio', {})
            
            echo_data = comp_audio.get('Echo', {})
            if echo_data.get('enabled', False):
                delay = int(echo_data.get('Delay', 500))
                decay = float(echo_data.get('Decay', 0.6))
                mix = float(echo_data.get('Mix', 0.5))
                qt_timeline = Echo(delay_ms=delay, decay=decay, mix=mix).applyComposition(qt_timeline)

            delay_data = comp_audio.get('Delay', {})
            if delay_data.get('enabled', False):
                d_ms = int(delay_data.get('Delay', 500))
                d_mix = float(delay_data.get('Mix', 0.5))
                qt_timeline = Delay(delay_ms=d_ms, mix=d_mix).applyComposition(qt_timeline)

            chorus_data = comp_audio.get('Chorus', {})
            if chorus_data.get('enabled', False):
                c_delay = int(chorus_data.get('Delay', 40))
                c_depth = float(chorus_data.get('Depth', 0.3))
                c_mix = float(chorus_data.get('Mix', 0.5))
                qt_timeline = Chorus(delay_ms=c_delay, depth=c_depth, mix=c_mix).applyComposition(qt_timeline)

            
            final_temp_path = qt_timeline.property("input_file")
            
            if final_temp_path and final_temp_path != original_path and os.path.exists(final_temp_path):
                stack_hash = hashlib.md5(str(filter_stack).encode()).hexdigest()[:8]
                base_name = os.path.basename(original_path)
                name, ext = os.path.splitext(base_name)
                
                final_path = os.path.join(self.cache_dir, f"{name}_FX_{stack_hash}{ext}")
                
                shutil.move(final_temp_path, final_path)
                self.processing_finished.emit(final_path, filter_stack)
            else:
                self.processing_finished.emit(original_path, filter_stack)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.processing_error.emit(str(e))