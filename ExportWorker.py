import os
import subprocess
import shutil
from PySide6.QtCore import QThread, Signal

class ExportWorker(QThread):
    progress_update = Signal(int, str) 
    finished_success = Signal(str)     
    finished_error = Signal(str)       

    def __init__(self, all_tracks, output_path, temp_folder, img_exts):
        super().__init__()

        self.tracks = all_tracks 
        self.output_path = output_path
        self.temp_render_dir = temp_folder
        self.img_exts = img_exts
        self.is_cancelled = False

    def run(self):
        try:
            video_parts_dir = os.path.join(self.temp_render_dir, "video_parts")
            os.makedirs(video_parts_dir, exist_ok=True)
            
            final_video_silent = os.path.join(self.temp_render_dir, "final_silent.mp4")
            final_audio_mixed = os.path.join(self.temp_render_dir, "final_mixed.aac")
            print("--- START FLATTENING ---")
            render_segments = self._calculate_flattened_timeline()
            total_segments = len(render_segments)
            video_chunks_list = []

            for i, segment in enumerate(render_segments):
                if self.is_cancelled: return
                self.progress_update.emit(i, f"Rendering Visual Segment {i+1}/{total_segments}")
                
                chunk_name = f"v_chunk_{i:03d}.mp4"
                chunk_path = os.path.join(video_parts_dir, chunk_name)
                
                # Debug info
                print(f"Segment {i}: {segment['duration_ms']}ms | Source: {segment['path']} | StartInSrc: {segment['source_start_ms']}")

                self._render_video_segment(segment, chunk_path)
                
                safe_path = chunk_path.replace("\\", "/")
                video_chunks_list.append(f"file '{safe_path}'")

            self.progress_update.emit(total_segments, "Stitching Visual Track...")
            list_txt = os.path.join(video_parts_dir, "list.txt")
            with open(list_txt, "w", encoding='utf-8') as f:
                f.write("\n".join(video_chunks_list))
            
            subprocess.run(
                f'ffmpeg -y -f concat -safe 0 -i "{list_txt}" -c copy "{final_video_silent}"',
                shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            self.progress_update.emit(total_segments + 1, "Mixing Audio Layers...")
            
            audio_inputs = []
            filter_complex_parts = []
            input_idx = 0
            
            for track in self.tracks:
                for clip in track.clips:
                    if clip.get('is_auto_gap', False): continue
                    path = clip['path']
                    if path.lower().endswith(tuple(self.img_exts)): continue
                    
                    start_ms = clip['start']
                    audio_inputs.extend(['-i', path])
                    filter_complex_parts.append(f"[{input_idx}:a]adelay={start_ms}|{start_ms}[a{input_idx}]")
                    input_idx += 1
            
            has_audio = (input_idx > 0)
            
            if has_audio:
                inputs_tags = "".join([f"[a{i}]" for i in range(input_idx)])
                mix_cmd = f"{inputs_tags}amix=inputs={input_idx}:dropout_transition=0:normalize=0[aout]"
                
                full_filter = ";".join(filter_complex_parts) + ";" + mix_cmd
                
                cmd_audio = [
                    'ffmpeg', '-y',
                    *audio_inputs,
                    '-filter_complex', full_filter,
                    '-map', '[aout]',
                    '-vn', 
                    '-c:a', 'aac', '-b:a', '192k',
                    final_audio_mixed
                ]
                subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.progress_update.emit(total_segments + 2, "Final Muxing...")
            
            if has_audio:
                cmd_merge = (
                    f'ffmpeg -y -i "{final_video_silent}" -i "{final_audio_mixed}" '
                    f'-c:v copy -c:a copy -shortest "{self.output_path}"'
                )
            else:
                cmd_merge = f'ffmpeg -y -i "{final_video_silent}" -c copy "{self.output_path}"'
                
            subprocess.run(cmd_merge, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.finished_success.emit(self.output_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_error.emit(str(e))
        finally:
            try:
                shutil.rmtree(self.temp_render_dir)
            except: pass

    def cancel(self):
        self.is_cancelled = True

    def _calculate_flattened_timeline(self):
        cut_points = set()
        cut_points.add(0)
        
        visual_clips_map = [] 

        for track_idx, track in enumerate(self.tracks):
            for clip in track.clips:
                cut_points.add(clip['start'])
                cut_points.add(clip['start'] + clip['duration'])
                
                path = clip['path']
                if path.lower().endswith(('.mp3', '.wav', '.flac')):
                    continue
                
                visual_clips_map.append({
                    'track_idx': track_idx,
                    'start': clip['start'],
                    'end': clip['start'] + clip['duration'],
                    'data': clip
                })
        
        sorted_points = sorted(list(cut_points))
        segments = []
        
        for i in range(len(sorted_points) - 1):
            t_start = sorted_points[i]
            t_end = sorted_points[i+1]
            duration = t_end - t_start
            
            if duration <= 0: continue
            
            winner_clip_data = None
            
            candidates = []
            for item in visual_clips_map:
                if item['start'] <= t_start and item['end'] >= t_end:
                    candidates.append(item)
            
            candidates.sort(key=lambda x: x['track_idx'])
            for cand in candidates:
                clip_info = cand['data']
                if not clip_info.get('is_auto_gap', False):
                    winner_clip_data = clip_info
                    break 
            
            if winner_clip_data:
                offset_in_clip = t_start - winner_clip_data['start']
                seg = {
                    'path': winner_clip_data['path'],
                    'source_start_ms': offset_in_clip,
                    'duration_ms': duration,
                    'is_gap': False
                }
            else:
                seg = {
                    'path': None,
                    'source_start_ms': 0,
                    'duration_ms': duration,
                    'is_gap': True
                }
                
            segments.append(seg)
            
        return segments

    def _render_video_segment(self, segment, output_path):
        duration_sec = segment['duration_ms'] / 1000.0
        start_sec = segment['source_start_ms'] / 1000.0
        path = segment['path']
        is_gap = segment['is_gap']
        
        vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
        
        cmd = ""
        if is_gap or not path:
             cmd = (
                f'ffmpeg -y -f lavfi -i color=c=black:s=1920x1080:r=30 '
                f'-t {duration_sec} -an '
                f'-c:v libx264 -preset ultrafast -pix_fmt yuv420p '
                f'"{output_path}"'
            )
        elif path.lower().endswith(tuple(self.img_exts)):
            cmd = (
                f'ffmpeg -y -loop 1 -i "{path}" '
                f'-t {duration_sec} -vf "{vf}" -an '
                f'-c:v libx264 -preset ultrafast -pix_fmt yuv420p '
                f'"{output_path}"'
            )
        else:
            cmd = (
                f'ffmpeg -y -ss {start_sec} -i "{path}" '
                f'-t {duration_sec} -vf "{vf}" -an '
                f'-c:v libx264 -preset ultrafast -pix_fmt yuv420p '
                f'"{output_path}"'
            )
            
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)