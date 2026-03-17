from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import os

from gesture_detector import GestureDetector
from camera_thread    import CameraThread
from transfer_manager import TransferManager

class AirSyncApp(App):

    def build(self):
        self.title            = "AirSync"
        self.selected_file    = None
        self.transfer_manager = TransferManager()
        self.gesture_detector = GestureDetector(
            model_path="gesture_model.tflite",
            on_gesture_detected=self._on_gesture
        )

        root = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.status_label  = Label(text="Select a file, then gesture", font_size="18sp")
        self.gesture_label = Label(text="Gesture: —", font_size="24sp", bold=True)
        self.my_ip_label   = Label(
            text=f"Your IP: {self.transfer_manager.get_my_ip()}",
            font_size="14sp"
        )
        
        self.camera_preview = Image(size_hint_y=None, height=400)
        
        self.ip_input = TextInput(
            hint_text="Enter receiver IP (e.g. 192.168.1.5)",
            multiline=False, size_hint_y=None, height=50
        )
        self.progress = ProgressBar(max=100, size_hint_y=None, height=30)

        btn_file    = Button(text="Select file",         size_hint_y=None, height=60)
        btn_receive = Button(text="Enter receive mode",  size_hint_y=None, height=60)

        btn_file.bind(on_press=self._pick_file)
        btn_receive.bind(on_press=lambda _: self._enter_receive_mode())

        for w in [self.status_label, self.my_ip_label, self.camera_preview, 
                  self.ip_input, self.gesture_label, self.progress, 
                  btn_file, btn_receive]:
            root.add_widget(w)

        self.camera_thread = CameraThread(self.gesture_detector, on_frame=self._update_camera)
        self.camera_thread.start()

        self.transfer_manager.on_file_received   = self._file_received
        self.transfer_manager.on_progress_update = self._update_progress

        return root

    def _update_camera(self, frame):
        # Update camera preview in main thread
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        Clock.schedule_once(lambda dt: setattr(self.camera_preview, 'texture', texture))

    def _on_gesture(self, gesture: str):
        Clock.schedule_once(lambda dt: self._handle_gesture(gesture))

    def _handle_gesture(self, gesture: str):
        self.gesture_label.text = f"Gesture: {gesture}"
        actions = {
            "SEND":    self._trigger_send,
            "RECEIVE": self._enter_receive_mode,
            "CANCEL":  lambda: setattr(self.status_label, "text", "Cancelled"),
            "CONFIRM": lambda: setattr(self.status_label, "text", "Confirmed!"),
        }
        action = actions.get(gesture)
        if action:
            action()

    def _pick_file(self, *args):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self._file_selected)
        except Exception:
            try:
                from tkinter import filedialog, Tk
                root = Tk()
                root.withdraw()
                path = filedialog.askopenfilename()
                root.destroy()
                if path:
                    self._file_selected([path])
            except ImportError:
                self.status_label.text = "File chooser not available"

    def _file_selected(self, selection):
        if selection:
            self.selected_file = selection[0]
            self.status_label.text = f"File: {os.path.basename(self.selected_file)}"

    def _trigger_send(self):
        if not self.selected_file:
            self.status_label.text = "No file selected!"
            return
        ip = self.ip_input.text.strip()
        if not ip:
            self.status_label.text = "Enter phone IP first"
            return
        self.status_label.text = f"Sending to {ip}..."
        self.transfer_manager.send_file(ip, self.selected_file)

    def _enter_receive_mode(self):
        # On laptop, save to Downloads
        save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(save_dir, exist_ok=True)
        self.status_label.text = f"Listening on {self.transfer_manager.get_my_ip()}..."
        self.transfer_manager.start_receiving(save_dir=save_dir)

    def _file_received(self, path):
        Clock.schedule_once(lambda dt: setattr(
            self.status_label, "text", f"Received: {os.path.basename(path)}"
        ))

    def _update_progress(self, pct):
        Clock.schedule_once(lambda dt: setattr(self.progress, "value", pct))

    def on_stop(self):
        if hasattr(self, 'camera_thread'):
            self.camera_thread.stop()
        if hasattr(self, 'gesture_detector'):
            self.gesture_detector.interpreter = None


if __name__ == "__main__":
    AirSyncApp().run()
