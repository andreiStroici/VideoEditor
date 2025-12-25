import sys
import os
import time

from PySide6.QtWidgets import QGridLayout, QWidget, QApplication, QListWidget
from PySide6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from Toolbar import Toolbar
from MediaTabs import MediaTabs
from VideoPreview import VideoPreview
from EnchancementsTabs import EnchancementsTabs
from TimelineAndTracks  import TimelineAndTracks
from VideoTabContent import VideoTabContent
from ImagePlayer import ImagePlayer

from ExportWorker import ExportWorker

class VideoEditorUI(QWidget):
    
    IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor Professional - Final Stable")
        self.showMaximized()

        SPACING = 8
        main = QGridLayout(self)
        main.setSpacing(SPACING*2)
        main.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.toolbar = Toolbar(SPACING)
        self.media_tabs = MediaTabs(SPACING)
        self.video_preview = VideoPreview(SPACING) 
        self.enchancements_tabs = EnchancementsTabs(SPACING)
        self.timeline_container = TimelineAndTracks(SPACING)

        main.addWidget(self.toolbar, 0, 0, 1, 2)
        main.addWidget(self.media_tabs, 1, 0)
        main.addWidget(self.video_preview, 1, 1)
        main.addWidget(self.enchancements_tabs, 2, 0)
        main.addWidget(self.timeline_container, 2, 1)
        
        main.setRowStretch(1, 2)
        main.setRowStretch(2, 1)
        main.setColumnStretch(0, 2)
        main.setColumnStretch(1, 5)

        self._connected_timeline_player = None
        self.auto_scroll_active = True 
        
        self.active_audio_players = {} 

        self.is_scrubbing = False 
        self.global_playback_speed = 1.0  
        self.global_playing_state = False 
        self.lazy_scrub_timer = QTimer()
        self.lazy_scrub_timer.setInterval(300) 
        self.lazy_scrub_timer.setSingleShot(True)
        self.lazy_scrub_timer.timeout.connect(self._perform_lazy_sync)
        self.pending_scrub_ms = -1
        self.reverse_timer = QTimer(self)
        self.reverse_timer.setInterval(33)
        self.reverse_timer.timeout.connect(self._on_reverse_tick)

        self.seek_timer = QTimer()
        self.seek_timer.setInterval(50) 
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self._execute_deferred_seek)
        self.pending_seek_val = -1

        self.toolbar.files_selected.connect(self.media_tabs.add_files)
        self.toolbar.folder_selected.connect(self.media_tabs.add_folder)
        self.media_tabs.file_double_clicked.connect(self.video_preview.add_media_tab)

        self.timeline_container.place_button.clicked.connect(self._on_place_clicked)
        self.timeline_container.delete_button.clicked.connect(self._on_delete_clicked)

        self.toolbar.save_project_button.clicked.connect(self._on_save_project_clicked)
        self.video_preview.preview_tabs.currentChanged.connect(self._sync_timeline_connection)
        
        self.video_preview.timeline_action.connect(self._handle_timeline_action)

        self.timeline_container.time_slider.sliderPressed.connect(self._on_slider_pressed)
        self.timeline_container.time_slider.sliderReleased.connect(self._on_slider_released)
        self.timeline_container.time_slider.sliderMoved.connect(self._on_slider_user_moved)
        
        self.timeline_container.seek_request.connect(self._on_timeline_seek)

        self.timeline_container.timeline_structure_changed.connect(self._on_timeline_structure_changed)
        self.timeline_container.track_clicked_signal.connect(lambda: self._handle_timeline_action('toggle_play', 0) if self.global_playing_state else None)

        h_scrollbar = self.timeline_container.scroll_area.horizontalScrollBar()
        h_scrollbar.sliderPressed.connect(self._on_user_scroll_start)
        h_scrollbar.sliderMoved.connect(self._on_user_scroll_start)

        self._sync_timeline_connection(0)

        self.enchancements_tabs.apply_filters_signal.connect(self.timeline_container.handle_apply_filters)
        self.timeline_container.clip_selected_for_filters.connect(self.enchancements_tabs.load_clip_data)
        self.export_worker = None
        self.progress_dialog = None

    def _on_timeline_structure_changed(self):
        self._refresh_slider()
        current_pos = self.timeline_container.time_slider.value()
        self._synchronize_preview_with_timeline(current_pos)

    def _perform_lazy_sync(self):
        if self.pending_scrub_ms != -1 and not self.global_playing_state:
            self._synchronize_preview_with_timeline(self.pending_scrub_ms)
            self.pending_scrub_ms = -1

    def _on_slider_user_moved(self, val):
        self.timeline_container.set_global_playhead(val)
        self.auto_scroll_active = False 
        self.pending_scrub_ms = val
        self.lazy_scrub_timer.start()

    def _handle_timeline_action(self, action, value):
        slider = self.timeline_container.time_slider
        
        if action == 'toggle_play':
            if self.global_playing_state:
                self.global_playing_state = False
                self._apply_global_state_to_preview()
            else:
                self.global_playing_state = True
                self.global_playback_speed = 1.0 
                self._apply_global_state_to_preview()

        elif action == 'start':
            slider.setValue(0)
            self.timeline_container.set_global_playhead(0)
            self.global_playing_state = False 
            self.global_playback_speed = 1.0
            self._synchronize_preview_with_timeline(0)
            
        elif action == 'end':
            maxim = slider.maximum()
            slider.setValue(maxim)
            self.timeline_container.set_global_playhead(maxim)
            self.global_playing_state = False 
            self.global_playback_speed = 1.0
            self._synchronize_preview_with_timeline(maxim)

        elif action == 'step':
            self.global_playing_state = False
            current = slider.value()
            step_size = 33 
            new_val = current + int(value * step_size)
            new_val = max(0, min(new_val, slider.maximum()))
            
            slider.blockSignals(True)
            slider.setValue(new_val)
            slider.blockSignals(False)
            
            self.timeline_container.set_global_playhead(new_val)
            self._synchronize_preview_with_timeline(new_val)
            
        elif action == 'speed':
            current_tab = self.video_preview.preview_tabs.currentWidget()
            if isinstance(current_tab, VideoTabContent):
                direction = "forward" if value > 0 else "backward"
                temp_rate = self.global_playback_speed
                if direction == "forward":
                    if temp_rate < 0: temp_rate = 1.0
                    else:
                        if temp_rate == 1.0: temp_rate = 1.5
                        elif temp_rate == 1.5: temp_rate = 2.0
                        elif temp_rate == 2.0: temp_rate = 0.5
                        elif temp_rate == 0.5: temp_rate = 1.0
                        else: temp_rate = 1.0
                else: 
                    if temp_rate > 0: temp_rate = -0.5
                    else:
                        if temp_rate == -0.5: temp_rate = -1.0
                        elif temp_rate == -1.0: temp_rate = -1.5
                        elif temp_rate == -1.5: temp_rate = -2.0
                        elif temp_rate == -2.0: temp_rate = -0.5
                        else: temp_rate = -0.5
                
                self.global_playback_speed = temp_rate
                self.global_playing_state = True 
                self._apply_global_state_to_preview()


    def _apply_global_state_to_preview(self):
        target_icon_state = QMediaPlayer.PlayingState if self.global_playing_state else QMediaPlayer.PausedState
        self.video_preview._update_play_button_icon(target_icon_state)
            
        should_mute = (self.global_playback_speed < 0)
        current_pos = self.timeline_container.time_slider.value()
        self._update_audio_mixer(current_pos, was_playing=self.global_playing_state, mute=should_mute)

        current_tab = self.video_preview.preview_tabs.currentWidget()
        if isinstance(current_tab, VideoTabContent) and current_tab.player:
            
            current_tab._logical_rate = self.global_playback_speed
            
            if self.global_playback_speed < 0:
                if self.global_playing_state:
                    if not self.reverse_timer.isActive():
                        self.reverse_timer.start()
                    current_tab.player.blockSignals(True)
                    current_tab.player.pause() 
                    current_tab.player.blockSignals(False)
                else:
                    self.reverse_timer.stop()
                    current_tab.player.pause()
            else:
                self.reverse_timer.stop()
                if isinstance(current_tab.player, QMediaPlayer):
                    current_tab.player.setPlaybackRate(abs(self.global_playback_speed))
                elif isinstance(current_tab.player, ImagePlayer):
                    current_tab.player.setPlaybackRate(abs(self.global_playback_speed))
                
                if self.global_playing_state:
                    current_tab.player.play()
                else:
                    current_tab.player.pause()

    def _on_reverse_tick(self):
        slider = self.timeline_container.time_slider
        current_val = slider.value()
        step = int(33 * abs(self.global_playback_speed))
        new_val = current_val - step
        
        if new_val <= 0:
            new_val = 0
            self.global_playing_state = False
            self._apply_global_state_to_preview()
        slider.blockSignals(True)
        slider.setValue(new_val)
        slider.blockSignals(False)
        self.timeline_container.set_global_playhead(new_val)
        self._synchronize_preview_with_timeline(new_val)
        
        if self.auto_scroll_active:
             self.timeline_container.ensure_cursor_visible(self.timeline_container.track_widgets[0].ms_to_px(new_val))
             
        self._update_audio_mixer(new_val, was_playing=False, mute=True)

    def closeEvent(self, event):
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.cancel()
            self.export_worker.wait()

        for key, player in self.active_audio_players.items():
            try:
                player.stop()
                player.setSource(QUrl())
            except: pass
        self.active_audio_players.clear()
        
        count = self.video_preview.preview_tabs.count()
        for i in range(count):
            widget = self.video_preview.preview_tabs.widget(i)
            if isinstance(widget, VideoTabContent):
                widget.cleanup()
        super().closeEvent(event)
    
    def _on_slider_pressed(self):
        self.is_scrubbing = True
        self.auto_scroll_active = False
        self.global_playing_state = False
        self._apply_global_state_to_preview()

    def _on_slider_released(self):
        self.is_scrubbing = False
        self.lazy_scrub_timer.stop()
        final_val = self.timeline_container.time_slider.value()
        self._synchronize_preview_with_timeline(final_val)

    def _on_delete_clicked(self):
        active_track = self.timeline_container.get_active_track()
        if not active_track: return
        
        self.global_playing_state = False
        self._apply_global_state_to_preview()
        
        deleted = active_track.delete_selected_clip()
        if deleted:
            self._refresh_slider()
            
            content_end = self.timeline_container.get_content_end_all_tracks()
            
            if content_end == 0:
                self.timeline_container.time_slider.setValue(0)
                self.timeline_container.set_global_playhead(0)
                self.timeline_container.scroll_area.horizontalScrollBar().setValue(0)
                self._synchronize_preview_with_timeline(0)
            else:
                self._synchronize_preview_with_timeline(active_track.playhead_pos_ms)

    def _on_user_scroll_start(self):
        self.auto_scroll_active = False

    def _on_place_clicked(self):
        current_list_widget = self.media_tabs.media_tabs.currentWidget()
        if not isinstance(current_list_widget, QListWidget): return
        selected_items = current_list_widget.selectedItems()
        if not selected_items: return
        
        insert_file_path = selected_items[0].data(Qt.UserRole)
        
        result_pos = self.timeline_container.insert_media_at_playhead(insert_file_path)
        
        if result_pos != -1:
            self._refresh_slider()
            self.timeline_container.time_slider.setValue(result_pos)
            self._synchronize_preview_with_timeline(result_pos)

    def _refresh_slider(self):
        content_end = self.timeline_container.get_content_end_all_tracks()
        
        if content_end > 0:
            self.timeline_container.time_slider.setMaximum(content_end)
            self.timeline_container.set_global_duration(content_end)
        else:
            self.timeline_container.time_slider.setMaximum(0) 
            self.timeline_container.set_global_duration(0)

    def _on_media_status_changed_ui(self, status):
        if status == QMediaPlayer.LoadedMedia or status == QMediaPlayer.BufferedMedia:
            player = self.sender()
            if isinstance(player, QMediaPlayer):
                pending_pos = player.property("pending_seek_ms")
                if pending_pos is not None:
                    player.setPosition(int(pending_pos))
                    player.setProperty("pending_seek_ms", None) 

        if status == QMediaPlayer.EndOfMedia:
            if self.global_playing_state and self.global_playback_speed > 0:
                slider = self.timeline_container.time_slider
                current_pos = slider.value()
                active_clip = None
                for track in self.timeline_container.track_widgets:
                    clip = track.get_clip_at_ms(current_pos)
                    if clip and not clip.get('is_auto_gap', False):
                        active_clip = clip
                        break
                if active_clip:
                    clip_end_time = int(active_clip['start'] + active_clip['duration'])
                    if abs(current_pos - clip_end_time) < 300:
                        next_pos = clip_end_time + 5 
                        slider.blockSignals(True)
                        slider.setValue(next_pos)
                        slider.blockSignals(False)
                        self.timeline_container.set_global_playhead(next_pos)
                        self._synchronize_preview_with_timeline(next_pos)
                else:
                    next_pos = current_pos + 33 
                    if next_pos < slider.maximum():
                        slider.blockSignals(True)
                        slider.setValue(next_pos)
                        slider.blockSignals(False)
                        self.timeline_container.set_global_playhead(next_pos)
                        self._synchronize_preview_with_timeline(next_pos)
                    else:
                        self.global_playing_state = False
                        self._apply_global_state_to_preview()

    def _sync_timeline_connection(self, index):
        if self._connected_timeline_player:
            try:
                self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.disconnect(self._on_playback_state_changed)
                self._connected_timeline_player.mediaStatusChanged.disconnect(self._on_media_status_changed_ui)
            except: pass
            self._connected_timeline_player = None

        current_widget = self.video_preview.preview_tabs.widget(index)
        slider = self.timeline_container.time_slider

        if index == 0:
            slider.setEnabled(True)
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                self._connected_timeline_player = current_widget.player
                self._connected_timeline_player.positionChanged.connect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.connect(self._on_playback_state_changed)
                self._connected_timeline_player.mediaStatusChanged.connect(self._on_media_status_changed_ui)
            self._refresh_slider()
        else:
            slider.setEnabled(False)
            for p in self.active_audio_players.values(): p.stop()

    def _on_playback_state_changed(self, state):
        if self.is_scrubbing: return
        
        if state == QMediaPlayer.PausedState and self.global_playing_state:
            sender = self.sender()
            if sender and hasattr(sender, "mediaStatus"):
                if sender.mediaStatus() == QMediaPlayer.EndOfMedia:
                    return 

        if state == QMediaPlayer.PlayingState:
            self.auto_scroll_active = True
        
        should_play_audio = self.global_playing_state and (self.global_playback_speed > 0)
        
        for player in self.active_audio_players.values():
            if should_play_audio:
                player.play()
            else:
                player.pause()

    def _update_timeline_ui(self, ms):
        if self.is_scrubbing: return
        ms = int(ms)
        if self.timeline_container.time_slider.isSliderDown(): return
        if self.global_playing_state and self.global_playback_speed < 0:
            return

        slider = self.timeline_container.time_slider
        if not self.timeline_container.track_widgets: return
        
        approx_global_pos = self.timeline_container.track_widgets[0].playhead_pos_ms
        current_widget = self.video_preview.preview_tabs.widget(0)
        should_mute = (self.global_playback_speed < 0) or (not self.global_playing_state)
        max_slider_val = slider.maximum()
        if approx_global_pos >= max_slider_val - 50 and self.global_playback_speed > 0:
             if self.global_playing_state:
                   self.global_playing_state = False
                   self._apply_global_state_to_preview()
                   slider.setValue(max_slider_val)
                   self.timeline_container.set_global_playhead(max_slider_val)
                   return

        target_clip = None
        for track in self.timeline_container.track_widgets:
            clip = track.get_clip_at_ms(approx_global_pos)
            if clip and not clip.get('is_auto_gap', False):
                target_clip = clip
                break
        
        if isinstance(current_widget.player, ImagePlayer) and self.global_playing_state:
            dur = current_widget.player.duration()
            pos = current_widget.player.position()
            threshold = 40 * abs(self.global_playback_speed)
            if threshold < 40: threshold = 40

            if pos >= dur - threshold:
                jump_to = (target_clip['start'] + target_clip['duration'] + 5) if target_clip else (slider.value() + 50)
                slider.blockSignals(True)
                slider.setValue(jump_to)
                slider.blockSignals(False)
                self.timeline_container.set_global_playhead(jump_to)
                self._synchronize_preview_with_timeline(jump_to)
                return

        if target_clip and os.path.abspath(target_clip['path']) == os.path.abspath(current_widget.file_path):
            expected_local_time = approx_global_pos - target_clip['start']
            if abs(ms - expected_local_time) < 1000:
                global_pos = int(target_clip['start'] + ms)
                slider.blockSignals(True)
                slider.setValue(global_pos)
                slider.blockSignals(False)
                self.timeline_container.set_global_playhead(global_pos)
                if self.auto_scroll_active:
                    self.timeline_container.ensure_cursor_visible(self.timeline_container.track_widgets[0].ms_to_px(global_pos))
                self._update_audio_mixer(global_pos, was_playing=self.global_playing_state, mute=should_mute)
                return 

        if "blackCat.jpg" in current_widget.file_path:
            step = int(33 * self.global_playback_speed)
            next_val = slider.value() + step
            slider.blockSignals(True)
            slider.setValue(next_val)
            slider.blockSignals(False)
            self.timeline_container.set_global_playhead(next_val)
            
            upcoming_clip = None
            for track in self.timeline_container.track_widgets:
                c = track.get_clip_at_ms(next_val)
                if c and not c.get('is_auto_gap', False):
                    upcoming_clip = c
                    break
            
            if upcoming_clip:
                self._synchronize_preview_with_timeline(next_val)
            else:
                self._update_audio_mixer(next_val, was_playing=self.global_playing_state, mute=should_mute)
        else:
            if target_clip:
                self._synchronize_preview_with_timeline(approx_global_pos)

    def _on_timeline_seek(self, ms):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        if ms < 0: ms = 0 
        self.timeline_container.time_slider.setValue(ms)
        self.timeline_container.set_global_playhead(ms)
        self.auto_scroll_active = True
        if self.timeline_container.track_widgets:
            cursor_x = self.timeline_container.track_widgets[0].ms_to_px(ms)
            self.timeline_container.ensure_cursor_visible(cursor_x)
        self.global_playing_state = False
        self.pending_scrub_ms = ms
        self.lazy_scrub_timer.start()

    def _execute_deferred_seek(self):
        if self.pending_seek_val != -1:
            self._synchronize_preview_with_timeline(self.pending_seek_val)
            self.pending_seek_val = -1

    def _update_audio_mixer(self, global_ms, was_playing, mute=False):
        if self.is_scrubbing: 
            was_playing = False
            mute = True 

        clips_to_play = []
        visual_clip = None
        
        if hasattr(self.timeline_container, 'track_widgets'):
            for track in self.timeline_container.track_widgets:
                clip = track.get_clip_at_ms(global_ms)
                if clip and not clip.get('is_auto_gap', False):
                    if visual_clip is None:
                        visual_clip = clip
                    clips_to_play.append(clip)

        needed_ids = set()
        for clip in clips_to_play:
            _, ext = os.path.splitext(clip['path'])
            if ext.lower() in self.IMG_EXT: continue
            
            if visual_clip and clip == visual_clip: continue
            
            clip_id = f"{clip['path']}_{clip['start']}"
            needed_ids.add(clip_id)
            
            if clip_id not in self.active_audio_players:
                player = QMediaPlayer(self)
                audio = QAudioOutput(self)
                player.setAudioOutput(audio)
                
                vol = 0.0 if mute else 0.7
                audio.setVolume(vol)
                
                player.setSource(QUrl.fromLocalFile(clip['path']))
                self.active_audio_players[clip_id] = player
                
                target_local_pos = int(max(0, global_ms - clip['start']))
                player.waiting_pos = target_local_pos
                player.mediaStatusChanged.connect(lambda s, p=player: self._on_player_loaded(s, p))
            else:
                player = self.active_audio_players[clip_id]
                if player.audioOutput():
                    vol = 0.0 if mute else 0.7
                    player.audioOutput().setVolume(vol)

                target_local_pos = int(max(0, global_ms - clip['start']))
                
                if player.mediaStatus() in [QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia, QMediaPlayer.EndOfMedia]:
                    if abs(player.position() - target_local_pos) > 150:
                        player.setPosition(target_local_pos)
                    
                    if was_playing and player.playbackState() != QMediaPlayer.PlayingState:
                        player.play()
                    elif not was_playing and player.playbackState() == QMediaPlayer.PlayingState:
                        player.pause()

        for clip_id, player in self.active_audio_players.items():
            if clip_id not in needed_ids:
                if player.playbackState() != QMediaPlayer.StoppedState:
                    player.stop() 

    def _on_player_loaded(self, status, player):
        if status == QMediaPlayer.LoadedMedia or status == QMediaPlayer.BufferedMedia:
            if hasattr(player, "waiting_pos"):
                pos = player.waiting_pos
                player.setPosition(pos)
                del player.waiting_pos

                if not self.is_scrubbing and self._connected_timeline_player and self._connected_timeline_player.playbackState() == QMediaPlayer.PlayingState:
                    player.play()

    def _synchronize_preview_with_timeline(self, global_ms):
        global_ms = int(global_ms)
        
        visual_clip = None
        if hasattr(self.timeline_container, 'track_widgets'):
            for track in self.timeline_container.track_widgets:
                clip = track.get_clip_at_ms(global_ms)
                if clip and not clip.get('is_auto_gap', False):
                    visual_clip = clip
                    break
        
        current_widget = self.video_preview.preview_tabs.widget(0)

        final_path = ""
        final_start = 0
        final_dur = 5000
        
        if visual_clip:
            final_path = visual_clip['path']
            final_start = int(visual_clip['start'])
            final_dur = int(visual_clip['duration'])
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            final_path = os.path.join(base_dir, "icons", "blackCat.jpg")
            final_start = global_ms
            final_dur = 5000

        local_pos = int(max(0, global_ms - final_start))
        
        need_reload = True
        if isinstance(current_widget, VideoTabContent):
            if os.path.abspath(current_widget.file_path) == os.path.abspath(final_path):
                need_reload = False
        
        if need_reload:
            if self._connected_timeline_player:
                try: self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                except: pass
                self._connected_timeline_player = None
            
            new_tab = self.video_preview.load_into_timeline_tab(final_path)
            self._sync_timeline_connection(0)
            new_tab.set_explicit_duration(final_dur)
            
            if new_tab.player:
                new_tab.player.setProperty("pending_seek_ms", local_pos)
                new_tab.player.setPosition(local_pos)

        else:
            if self._connected_timeline_player:
                is_reversing = (self.global_playing_state and self.global_playback_speed < 0)
                
                if is_reversing or abs(self._connected_timeline_player.position() - local_pos) > 60:
                     self._connected_timeline_player.setPosition(local_pos)

        self._apply_global_state_to_preview()

    def _force_update_position(self, pos):
        self.timeline_container.time_slider.blockSignals(True)
        self.timeline_container.time_slider.setValue(pos)
        self.timeline_container.time_slider.blockSignals(False)
        self.timeline_container.set_global_playhead(pos)

    def _normal_update_position(self, pos):
        self.timeline_container.time_slider.blockSignals(True)
        self.timeline_container.time_slider.setValue(pos)
        self.timeline_container.time_slider.blockSignals(False)
        self.timeline_container.set_global_playhead(pos)

    def _on_save_project_clicked(self):
        self.global_playing_state = False
        self._apply_global_state_to_preview()

        if not self.timeline_container.track_widgets:
            QMessageBox.warning(self, "No Tracks", "There are no tracks to export.")
            return
        content_end = self.timeline_container.get_content_end_all_tracks()
        if content_end < 100:
             QMessageBox.warning(self, "Empty Project", "The project appears to be empty (0 duration). Please add clips.")
             return

        all_tracks = self.timeline_container.track_widgets

        filters = "Video Files (*.mp4)"
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Project As Video", os.path.expanduser("~"), filters)
        
        if not output_path:
            return 
        
        if not output_path.lower().endswith(".mp4"):
            output_path += ".mp4"

        base_dir = os.path.dirname(os.path.abspath(__file__))
        temp_render_dir = os.path.join(base_dir, "temp_render")
        os.makedirs(temp_render_dir, exist_ok=True)
        
        total_items = 0
        for t in all_tracks: total_items += len(t.clips)

        self.progress_dialog = QProgressDialog("Rendering Project...", "Cancel", 0, total_items + 5, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        
        self.export_worker = ExportWorker(all_tracks, output_path, temp_render_dir, self.IMG_EXT)
        
        self.export_worker.progress_update.connect(self._on_export_progress)
        self.export_worker.finished_success.connect(self._on_export_success)
        self.export_worker.finished_error.connect(self._on_export_error)
        
        self.progress_dialog.canceled.connect(self.export_worker.cancel)
        
        self.export_worker.start()
        self.progress_dialog.show()

    def _on_export_progress(self, val, msg):
        if self.progress_dialog:
            self.progress_dialog.setValue(val)
            self.progress_dialog.setLabelText(msg)

    def _on_export_success(self, path):
        if self.progress_dialog:
            self.progress_dialog.close()
        QMessageBox.information(self, "Success", f"Video exported successfully to:\n{path}")
        self.export_worker = None

    def _on_export_error(self, msg):
        if self.progress_dialog:
            self.progress_dialog.close()
        if "Cancelled" not in msg:
            QMessageBox.critical(self, "Export Error", f"An error occurred:\n{msg}")
        self.export_worker = None
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())