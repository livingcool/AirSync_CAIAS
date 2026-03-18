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
    AirGestureClientScreen:
    GameSteeringScreen:
    GestureOptionScreen:
    AirGestureServerScreen:

<ProfileScreen>:
    name: "profile"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.05,0.05,0.05,1  # Darker background
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            orientation: "vertical"
            padding: 20
            spacing: 20

            MDCard:
                size_hint: None, None
                size: 300, 200
                pos_hint: {"center_x": 0.5}
                md_bg_color: 0.1,0.1,0.1,1
                radius: [20]

                BoxLayout:
                    orientation: "vertical"
                    padding: 20

                    MDLabel:
                        text: "AKATSUKI"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 1,0.8,0,1
                        font_style: "H3"

                    MDLabel:
                        text: "HAND GESTURE CONTROL"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.3,0.6,1,1
                        font_style: "H6"

            MDLabel:
                text: "Choose an Option"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,1,1,1
                font_style: "H5"

            BoxLayout:
                orientation: "vertical"
                spacing: 15
                size_hint_y: None
                height: 220
                pos_hint: {"center_x": 0.5}

                MDRaisedButton:
                    text: "AirSync"
                    md_bg_color: 1,0.8,0,1
                    text_color: 0,0,0,1
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    font_size: "18sp"
                    on_release: app.run_airsync()

                MDRaisedButton:
                    text: "VolumeGesture"
                    md_bg_color: 0.2,0.6,1,1
                    text_color: 1,1,1,1
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    font_size: "18sp"
                    on_release: app.VolumeOption()

                MDRaisedButton:
                    text: "GameSteeringWheelControl"
                    md_bg_color: 0.5,0.2,1,1
                    text_color: 1,1,1,1
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    font_size: "18sp"
                    on_release: app.GestureOption()

<ServerScreen>:
    name: "server"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        canvas.before:
            Color:
                rgba: 0.95,0.95,0.95,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint_y: 0.35
            padding: 20
            md_bg_color: 1,1,1,1
            orientation: "vertical"
            spacing: 10
            elevation: 10
            radius: [15]

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
                rgba: 0.95,0.95,0.95,1
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
                rgba: 0.95,0.95,0.95,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.9, 0.25
            pos_hint: {"center_x": 0.5, "center_y": 0.85}
            padding: 15
            spacing: 10
            orientation: "vertical"
            md_bg_color: 1,1,1,1
            elevation: 10
            radius: [15]

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

<AirGestureClientScreen>:
    status_label: status_label
    gesture_label: gesture_label
    ip_input: ip_input
    port_input: port_input
    name: "AirGestureClient"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.05,0.05,0.05,1  # Dark background
            Rectangle:
                pos: self.pos
                size: self.size

        # Logo/Header Card
        MDCard:
            size_hint: 0.9, 0.2
            pos_hint: {"center_x": 0.5, "center_y": 0.9}
            md_bg_color: 0.15,0.15,0.15,1
            padding: 15
            radius: [25,25,0,0]
            elevation: 10

            BoxLayout:
                orientation: "vertical"

                MDLabel:
                    text: "AIR GESTURE CLIENT"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 1,0.8,0,1
                    font_style: "H5"
                    size_hint_y: 0.5

                MDLabel:
                    text: "Remote Media Control"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.5,0.8,1,1
                    font_style: "Body1"
                    size_hint_y: 0.3

        # Connection Card
        MDCard:
            size_hint: 0.9, 0.25
            pos_hint: {"center_x": 0.5, "center_y": 0.65}
            md_bg_color: 0.2,0.2,0.2,1
            padding: 20
            spacing: 15
            orientation: "vertical"
            radius: [20]
            elevation: 8

            MDTextField:
                id: ip_input
                hint_text: "Server IP Address"
                text: "192.168.0.103"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1
                font_size: "16sp"

            MDTextField:
                id: port_input
                hint_text: "Port Number"
                text: "5005"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.4
                input_filter: "int"
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1
                font_size: "16sp"

        # Status Card
        MDCard:
            size_hint: 0.9, 0.25
            pos_hint: {"center_x": 0.5, "center_y": 0.35}
            orientation: "vertical"
            padding: 20
            spacing: 10
            md_bg_color: 0.15,0.15,0.15,1
            radius: [20]
            elevation: 8

            MDLabel:
                text: "Connection Status"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.7,0.7,0.7,1
                font_style: "Body1"
                size_hint_y: 0.2

            MDLabel:
                id: status_label
                text: "Not Connected"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.2,0,1
                font_style: "H6"
                size_hint_y: 0.3

            MDLabel:
                id: gesture_label
                text: "Gesture: None"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.5,0.8,1,1
                font_style: "Body1"
                size_hint_y: 0.2

        # Control Buttons
        BoxLayout:
            orientation: "horizontal"
            size_hint: 0.9, 0.1
            pos_hint: {"center_x": 0.5, "y": 0.1}
            spacing: 15

            MDRaisedButton:
                text: "CONNECT"
                md_bg_color: 0.2,0.8,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                font_size: "16sp"
                on_release: app.connect_air_gesture_client()

            MDRaisedButton:
                text: "DISCONNECT"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                font_size: "16sp"
                on_release: app.disconnect_air_gesture_client()

        MDRaisedButton:
            text: "BACK TO PROFILE"
            md_bg_color: 0.5,0.5,0.5,1
            text_color: 1,1,1,1
            size_hint: 0.9, 0.07
            pos_hint: {"center_x": 0.5, "y": 0.02}
            font_size: "14sp"
            on_release: app.go_back_to_profile_from_air_gesture_client()

<GameSteeringScreen>:
    camera_view: camera_view
    gesture_label: gesture_label
    name: "GameSteering"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.05,0.05,0.05,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.95, 0.15
            pos_hint: {"center_x": 0.5, "center_y": 0.9}
            md_bg_color: 0.15,0.15,0.15,1
            padding: 10
            radius: [15]

            MDLabel:
                text: "HAND GESTURE CONTROL"
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
            md_bg_color: 0.5,0.5,0.5,1
            text_color: 1,1,1,1
            size_hint: 0.9, 0.08
            pos_hint: {"center_x": 0.5, "y": 0.05}
            on_release: app.go_back_to_profile_from_game()

<AirGestureServerScreen>:
    camera_view: camera_view
    status_label: status_label
    gesture_label: gesture_label
    ip_input: ip_input
    port_input: port_input
    client_status_label: client_status_label
    name: "AirGestureServer"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.05,0.05,0.05,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.9, 0.3
            pos_hint: {"center_x": 0.5, "center_y": 0.85}
            padding: 15
            spacing: 10
            orientation: "vertical"
            md_bg_color: 0.15,0.15,0.15,1
            radius: [20]
            elevation: 10

            MDLabel:
                text: "AIR GESTURE SERVER"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.8,0,1
                font_style: "H6"
                size_hint_y: 0.15

            MDTextField:
                id: ip_input
                hint_text: "Server IP Address"
                text: "192.168.0.103"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.2
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1

            MDTextField:
                id: port_input
                hint_text: "Port Number"
                text: "5005"
                mode: "rectangle"
                line_color_focus: 1,0.8,0,1
                size_hint_y: 0.2
                input_filter: "int"
                text_color: 1,1,1,1
                hint_text_color: 0.7,0.7,0.7,1

            MDLabel:
                id: client_status_label
                text: "Waiting for client..."
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.5,0,1
                font_style: "Body1"
                size_hint_y: 0.15

        Image:
            id: camera_view
            size_hint: 1, 0.35
            pos_hint: {"center_x": 0.5, "center_y": 0.55}

        MDCard:
            size_hint: 0.9, 0.15
            pos_hint: {"center_x": 0.5, "center_y": 0.25}
            md_bg_color: 0.15,0.15,0.15,1
            padding: 10
            radius: [15]

            MDLabel:
                id: status_label
                text: "Server Stopped"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.2,0,1
                font_style: "H6"
                size_hint_y: 0.4

            MDLabel:
                id: gesture_label
                text: "No gesture detected"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.5,0.8,1,1
                font_style: "Body1"
                size_hint_y: 0.3

        BoxLayout:
            orientation: "horizontal"
            size_hint: 0.9, 0.1
            pos_hint: {"center_x": 0.5, "y": 0.08}
            spacing: 10

            MDRaisedButton:
                text: "Start Server"
                md_bg_color: 0.2,0.8,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.start_air_gesture_server()

            MDRaisedButton:
                text: "Stop Server"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                size_hint_x: 0.5
                on_release: app.stop_air_gesture_server()

        MDRaisedButton:
            text: "Back to Profile"
            md_bg_color: 0.5,0.5,0.5,1
            text_color: 1,1,1,1
            size_hint: 0.9, 0.07
            pos_hint: {"center_x": 0.5, "y": 0.02}
            on_release: app.go_back_to_profile_from_air_gesture()

<GestureOptionScreen>:
    name: "GestureOption" 
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.05,0.05,0.05,1
            Rectangle:
                pos: self.pos
                size: self.size

        # Title Card
        MDCard:
            size_hint: 0.9, 0.15
            pos_hint: {"center_x": 0.5, "center_y": 0.9}
            md_bg_color: 0.15,0.15,0.15,1
            padding: 15
            radius: [20]

            MDLabel:
                text: "GESTURE CONTROL"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1,0.8,0,1
                font_style: "H5"
                size_hint_y: 0.6

            MDLabel:
                text: "Choose your mode"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.7,0.7,0.7,1
                font_style: "Body1"
                size_hint_y: 0.3

        # Option 1 - Single Camera Card
        MDCard:
            size_hint: 0.9, 0.2
            pos_hint: {"center_x": 0.5, "center_y": 0.65}
            md_bg_color: 0.2,0.2,0.2,1
            padding: 15
            radius: [20]
            ripple_behavior: True
            elevation: 5
            on_release: app.go_to_game_steering()

            BoxLayout:
                orientation: "horizontal"
                spacing: 15

                MDIcon:
                    icon: "camera"
                    size_hint: None, None
                    size: 48, 48
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1,0.8,0,1

                BoxLayout:
                    orientation: "vertical"
                    size_hint_x: 0.7

                    MDLabel:
                        text: "Single Camera"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        font_style: "H6"

                    MDLabel:
                        text: "Direct hand gesture control"
                        theme_text_color: "Custom"
                        text_color: 0.6,0.6,0.6,1
                        font_style: "Caption"

                MDRaisedButton:
                    text: "START"
                    md_bg_color: 0.2,0.8,0,1
                    text_color: 1,1,1,1
                    size_hint: None, None
                    size: 80, 40
                    pos_hint: {"center_y": 0.5}
                    on_release: app.go_to_game_steering()

        # Option 2 - AirGesture Server Card
        MDCard:
            size_hint: 0.9, 0.2
            pos_hint: {"center_x": 0.5, "center_y": 0.4}
            md_bg_color: 0.2,0.2,0.2,1
            padding: 15
            radius: [20]
            ripple_behavior: True
            elevation: 5
            on_release: app.go_to_air_gesture_server()

            BoxLayout:
                orientation: "horizontal"
                spacing: 15

                MDIcon:
                    icon: "server-network"
                    size_hint: None, None
                    size: 48, 48
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1,0.2,0,1

                BoxLayout:
                    orientation: "vertical"
                    size_hint_x: 0.7

                    MDLabel:
                        text: "AirGesture Server"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        font_style: "H6"

                    MDLabel:
                        text: "Send gestures to clients"
                        theme_text_color: "Custom"
                        text_color: 0.6,0.6,0.6,1
                        font_style: "Caption"

                MDRaisedButton:
                    text: "OPEN"
                    md_bg_color: 1,0.2,0,1
                    text_color: 1,1,1,1
                    size_hint: None, None
                    size: 80, 40
                    pos_hint: {"center_y": 0.5}
                    on_release: app.go_to_air_gesture_server()

        # Option 3 - AirGesture Client Card
        MDCard:
            size_hint: 0.9, 0.2
            pos_hint: {"center_x": 0.5, "center_y": 0.15}
            md_bg_color: 0.2,0.2,0.2,1
            padding: 15
            radius: [20]
            ripple_behavior: True
            elevation: 5
            on_release: app.go_to_air_gesture_client()

            BoxLayout:
                orientation: "horizontal"
                spacing: 15

                MDIcon:
                    icon: "remote"
                    size_hint: None, None
                    size: 48, 48
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 0.2,0.6,1,1

                BoxLayout:
                    orientation: "vertical"
                    size_hint_x: 0.7

                    MDLabel:
                        text: "AirGesture Client"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        font_style: "H6"

                    MDLabel:
                        text: "Control media remotely"
                        theme_text_color: "Custom"
                        text_color: 0.6,0.6,0.6,1
                        font_style: "Caption"

                MDRaisedButton:
                    text: "OPEN"
                    md_bg_color: 0.2,0.6,1,1
                    text_color: 1,1,1,1
                    size_hint: None, None
                    size: 80, 40
                    pos_hint: {"center_y": 0.5}
                    on_release: app.go_to_air_gesture_client()

        # Back Button at Bottom
        MDRaisedButton:
            text: "Back to Profile"
            md_bg_color: 0.5,0.5,0.5,1
            text_color: 1,1,1,1
            size_hint: 0.9, 0.07
            pos_hint: {"center_x": 0.5, "y": 0.02}
            on_release: app.go_back_to_profile()

<VolumeOptionScreen>:
    name: "volumeoption"
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0.95,0.95,0.95,1
            Rectangle:
                pos: self.pos
                size: self.size

        MDCard:
            size_hint: 0.9, 0.2
            pos_hint: {"center_x": 0.5, "center_y": 0.8}
            md_bg_color: 1,1,1,1
            padding: 20
            elevation: 10
            radius: [15]

            MDLabel:
                text: "VOLUME CONTROL"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0,0,0,1
                font_style: "H5"

        BoxLayout:
            orientation: "vertical"
            size_hint: 0.9, 0.4
            pos_hint: {"center_x": 0.5, "center_y": 0.4}
            spacing: 15

            MDRaisedButton:
                text: "Single Camera"
                md_bg_color: 1,0.8,0,1
                text_color: 0,0,0,1
                size_hint_y: 0.3
                on_release: app.VolumeGesture()

            MDRaisedButton:
                text: "AirVolume Server"
                md_bg_color: 1,0.2,0,1
                text_color: 1,1,1,1
                size_hint_y: 0.3
                on_release: app.AirVolume()

            MDRaisedButton:
                text: "Back"
                md_bg_color: 0.7,0.7,0.7,1
                text_color: 0,0,0,1
                size_hint_y: 0.3
                on_release: app.go_back_to_profile()
"""


# --- Screens ---
class ProfileScreen(Screen):
    pass


class ServerScreen(Screen):
    pass


class CameraScreen(Screen):
    pass


class GestureOptionScreen(Screen):
    pass


class VolumeScreen(Screen):
    camera_view = ObjectProperty(None)


class AirVolumeScreen(Screen):
    camera_view = ObjectProperty(None)
    status_label = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)


class AirGestureClientScreen(Screen):
    status_label = ObjectProperty(None)
    gesture_label = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)


class GameSteeringScreen(Screen):
    camera_view = ObjectProperty(None)
    gesture_label = ObjectProperty(None)


class AirGestureServerScreen(Screen):
    camera_view = ObjectProperty(None)
    status_label = ObjectProperty(None)
    gesture_label = ObjectProperty(None)
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)
    client_status_label = ObjectProperty(None)


class VolumeOptionScreen(Screen):
    pass


# --- App ---
class HandServerApp(MDApp):
    def build(self):
        self.sent_file = False
        self.capture = None
        self.air_capture = None
        self.game_capture = None
        self.air_gesture_capture = None
        self.hands = None
        self.air_hands = None
        self.game_hands = None
        self.air_gesture_hands = None
        self.mp_draw = None
        self.mp_hands = mp.solutions.hands
        self.camera_running = False
        self.air_camera_running = False
        self.game_camera_running = False
        self.air_gesture_camera_running = False
        self.air_server_socket = None
        self.air_client_socket = None
        self.air_server_running = False
        self.air_server_thread = None
        self.air_gesture_server_socket = None
        self.air_gesture_client_socket = None
        self.air_gesture_server_running = False
        self.air_gesture_server_thread = None

        # Air Gesture Client variables
        self.air_gesture_client_socket = None
        self.air_gesture_client_connected = False
        self.air_gesture_client_running = False
        self.air_gesture_client_thread = None

        # Game steering variables
        self.game_last_action_time = 0
        self.game_action_delay = 1

        # Air gesture server variables
        self.air_gesture_last_action_time = 0
        self.air_gesture_action_delay = 1

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

    def GameSteeringOption(self):
        print("Game Steering Option clicked - showing GameSteering screen")
        self.root.current = "GameSteering"

    def GameSteeringWheelControl(self):
        print("Game Steering Wheel Control clicked")
        self.root.current = "GameSteering"

    def GestureOption(self):
        self.root.current = "GestureOption"

    def go_to_game_steering(self):
        """Navigate to GameSteering screen"""
        print("Going to Game Steering screen")
        self.root.current = "GameSteering"

    def go_to_air_gesture_server(self):
        """Navigate to AirGestureServer screen"""
        print("Going to Air Gesture Server screen")
        self.root.current = "AirGestureServer"

    def go_to_air_gesture_client(self):
        """Navigate to AirGestureClient screen"""
        print("Going to Air Gesture Client screen")
        self.root.current = "AirGestureClient"

    # --- Game Steering Camera (Hand Gesture Play/Pause) ---
    def start_game_steering(self):
        if self.game_camera_running:
            return
        print("Starting game steering camera")
        self.game_capture = cv2.VideoCapture(0)
        if not self.game_capture.isOpened():
            if self.root and self.root.current == "GameSteering":
                screen = self.root.get_screen("GameSteering")
                if screen and hasattr(screen, 'gesture_label'):
                    screen.gesture_label.text = "Failed to open camera"
            return

        self.game_hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.game_camera_running = True
        self.game_last_action_time = 0
        Clock.schedule_interval(self.update_game_steering, 1 / 30)

        # Update gesture label
        if self.root and self.root.current == "GameSteering":
            screen = self.root.get_screen("GameSteering")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = "Camera started - Show your hand"

    def stop_game_steering(self):
        self.game_camera_running = False
        if self.game_capture:
            self.game_capture.release()
            self.game_capture = None
        if self.root and self.root.current == "GameSteering":
            screen = self.root.get_screen("GameSteering")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = "Camera Stopped"

    # --- Game Steering Update ---
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

    # --- Air Gesture Server (Networked Hand Gesture) ---
    def start_air_gesture_server(self):
        if self.air_gesture_server_running:
            return

        # Get IP and Port from text inputs
        try:
            server_ip = self.root.get_screen("AirGestureServer").ip_input.text
            server_port = int(self.root.get_screen("AirGestureServer").port_input.text)

            if server_ip == "":
                self.update_air_gesture_client_status("Please enter an IP address", (1, 0, 0, 1))
                return

            if server_port < 1024 or server_port > 65535:
                self.update_air_gesture_client_status("Port must be between 1024-65535", (1, 0, 0, 1))
                return

        except ValueError:
            self.update_air_gesture_client_status("Invalid port number", (1, 0, 0, 1))
            return
        except:
            self.update_air_gesture_client_status("Invalid IP or Port", (1, 0, 0, 1))
            return

        self.air_gesture_server_thread = Thread(target=self.run_air_gesture_server, args=(server_ip, server_port),
                                                daemon=True)
        self.air_gesture_server_thread.start()

    def run_air_gesture_server(self, server_ip, server_port):
        try:
            self.air_gesture_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.air_gesture_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.air_gesture_server_socket.bind((server_ip, server_port))
            self.air_gesture_server_socket.listen(1)

            # Update status - waiting for client
            Clock.schedule_once(lambda dt: self.update_air_gesture_client_status(
                f"Waiting for client on {server_ip}:{server_port}...", (1, 0.5, 0, 1)))
            Clock.schedule_once(
                lambda dt: self.update_air_gesture_status("Server Running - Waiting for Client", (1, 0.5, 0, 1)))
            print(f"Waiting for client connection on {server_ip}:{server_port}...")

            # Wait for client connection
            self.air_gesture_client_socket, addr = self.air_gesture_server_socket.accept()
            print(f"Connected to {addr}")

            # Update status - client connected
            Clock.schedule_once(lambda dt: self.update_air_gesture_client_status(
                f"Connected to {addr[0]}:{addr[1]}", (0, 1, 0, 1)))
            Clock.schedule_once(
                lambda dt: self.update_air_gesture_status("Client Connected - Camera Starting", (0, 1, 0, 1)))

            # Start camera AFTER client connects
            self.air_gesture_capture = cv2.VideoCapture(0)
            if not self.air_gesture_capture.isOpened():
                Clock.schedule_once(lambda dt: self.update_air_gesture_status("Failed to open camera", (1, 0, 0, 1)))
                return

            self.air_gesture_hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
            self.air_gesture_server_running = True
            self.air_gesture_last_action_time = 0
            Clock.schedule_interval(self.update_air_gesture_server, 1 / 30)

            Clock.schedule_once(
                lambda dt: self.update_air_gesture_status("Camera Running - Detecting Gestures", (0, 1, 0, 1)))

        except Exception as e:
            error_msg = str(e)[:20]
            print(f"Server error: {e}")
            Clock.schedule_once(
                lambda dt, msg=error_msg: self.update_air_gesture_client_status(f"Error: {msg}", (1, 0, 0, 1)))
            Clock.schedule_once(lambda dt, msg=error_msg: self.update_air_gesture_status(f"Error: {msg}", (1, 0, 0, 1)))
            self.air_gesture_server_running = False

    def update_air_gesture_server(self, dt):
        if not self.air_gesture_server_running or not self.air_gesture_capture:
            return

        ret, frame = self.air_gesture_capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.air_gesture_hands.process(rgb_frame)

        gesture_text = "No hand detected"
        gesture = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                fingers = self.count_fingers(hand_landmarks)
                current_time = time.time()

                if current_time - self.air_gesture_last_action_time > self.air_gesture_action_delay:
                    if fingers == 0:  # Fist
                        gesture = 'play'
                        gesture_text = "Fist detected: PLAY"
                        self.air_gesture_last_action_time = current_time
                    elif fingers == 5:  # Open hand
                        gesture = 'pause'
                        gesture_text = "Open hand detected: PAUSE"
                        self.air_gesture_last_action_time = current_time
                    else:
                        gesture_text = f"{fingers} fingers detected"
                else:
                    gesture_text = f"Cooldown: {fingers} fingers"

        # Update gesture label
        if self.root and self.root.current == "AirGestureServer":
            screen = self.root.get_screen("AirGestureServer")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = gesture_text

        # Send gesture to client if detected and client is connected
        if gesture and hasattr(self, 'air_gesture_client_socket') and self.air_gesture_client_socket:
            try:
                data = pickle.dumps(gesture)
                self.air_gesture_client_socket.sendall(data)
                print(f"Sent gesture to client: {gesture}")
            except:
                print("Client disconnected")
                self.air_gesture_client_socket = None
                Clock.schedule_once(lambda dt: self.update_air_gesture_client_status(
                    "Client disconnected", (1, 0, 0, 1)))
                Clock.schedule_once(lambda dt: self.update_air_gesture_status(
                    "Client Disconnected", (1, 0, 0, 1)))

        # Update Kivy Image
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        if self.root and self.root.current == "AirGestureServer":
            screen = self.root.get_screen("AirGestureServer")
            if screen and hasattr(screen, 'camera_view'):
                screen.camera_view.texture = texture

    def update_air_gesture_client_status(self, text, color):
        if self.root and self.root.current == "AirGestureServer":
            screen = self.root.get_screen("AirGestureServer")
            if screen and hasattr(screen, 'client_status_label'):
                screen.client_status_label.text = text
                screen.client_status_label.color = color

    def update_air_gesture_status(self, text, color):
        if self.root and self.root.current == "AirGestureServer":
            screen = self.root.get_screen("AirGestureServer")
            if screen and hasattr(screen, 'status_label'):
                screen.status_label.text = text
                screen.status_label.color = color

    def stop_air_gesture_server(self):
        self.air_gesture_server_running = False
        if hasattr(self, 'air_gesture_capture') and self.air_gesture_capture:
            self.air_gesture_capture.release()
            self.air_gesture_capture = None
        if hasattr(self, 'air_gesture_client_socket') and self.air_gesture_client_socket:
            try:
                self.air_gesture_client_socket.close()
            except:
                pass
            self.air_gesture_client_socket = None
        if hasattr(self, 'air_gesture_server_socket') and self.air_gesture_server_socket:
            try:
                self.air_gesture_server_socket.close()
            except:
                pass
            self.air_gesture_server_socket = None
        self.update_air_gesture_client_status("Server Stopped", (1, 0, 0, 1))
        self.update_air_gesture_status("Server Stopped", (1, 0, 0, 1))
        if self.root and self.root.current == "AirGestureServer":
            screen = self.root.get_screen("AirGestureServer")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = "No gesture detected"

    # --- Air Gesture Client (Your exact client code) ---
    def connect_air_gesture_client(self):
        if self.air_gesture_client_connected:
            return

        # Get IP and Port from text inputs
        try:
            server_ip = self.root.get_screen("AirGestureClient").ip_input.text
            server_port = int(self.root.get_screen("AirGestureClient").port_input.text)

            if server_ip == "":
                self.update_air_gesture_client_connection_status("Please enter IP address", (1, 0, 0, 1))
                return

            if server_port < 1024 or server_port > 65535:
                self.update_air_gesture_client_connection_status("Port must be 1024-65535", (1, 0, 0, 1))
                return

        except ValueError:
            self.update_air_gesture_client_connection_status("Invalid port number", (1, 0, 0, 1))
            return
        except:
            self.update_air_gesture_client_connection_status("Invalid IP or Port", (1, 0, 0, 1))
            return

        self.air_gesture_client_thread = Thread(target=self.run_air_gesture_client, args=(server_ip, server_port),
                                                daemon=True)
        self.air_gesture_client_thread.start()

    def run_air_gesture_client(self, server_ip, server_port):
        """Your exact client code"""
        try:
            # Update status
            Clock.schedule_once(lambda dt: self.update_air_gesture_client_connection_status(
                f"Connecting to {server_ip}:{server_port}...", (1, 0.5, 0, 1)))

            # Your original socket connection code
            self.air_gesture_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.air_gesture_client_socket.connect((server_ip, server_port))

            self.air_gesture_client_connected = True
            self.air_gesture_client_running = True

            Clock.schedule_once(lambda dt: self.update_air_gesture_client_connection_status(
                "Connected to server", (0, 1, 0, 1)))
            Clock.schedule_once(lambda dt: self.update_air_gesture_client_gesture("Gesture: None"))
            print(f"Connected to server {server_ip}:{server_port}...")

            # Your original while loop
            while self.air_gesture_client_running:
                try:
                    data = self.air_gesture_client_socket.recv(1024)
                    if data:
                        gesture = pickle.loads(data)
                        if gesture == 'play':
                            print("Play command received")
                            pyautogui.press('space')
                            Clock.schedule_once(lambda dt: self.update_air_gesture_client_gesture("Gesture: PLAY"))
                        elif gesture == 'pause':
                            print("Pause command received")
                            pyautogui.press('space')
                            Clock.schedule_once(lambda dt: self.update_air_gesture_client_gesture("Gesture: PAUSE"))
                except:
                    print("Connection lost")
                    break

        except Exception as e:
            error_msg = str(e)[:30]
            print(f"Client error: {e}")
            Clock.schedule_once(lambda dt, msg=error_msg: self.update_air_gesture_client_connection_status(
                f"Error: {msg}", (1, 0, 0, 1)))
        finally:
            self.disconnect_air_gesture_client()

    def update_air_gesture_client_connection_status(self, text, color):
        if self.root and self.root.current == "AirGestureClient":
            screen = self.root.get_screen("AirGestureClient")
            if screen and hasattr(screen, 'status_label'):
                screen.status_label.text = text
                screen.status_label.color = color

    def update_air_gesture_client_gesture(self, text):
        if self.root and self.root.current == "AirGestureClient":
            screen = self.root.get_screen("AirGestureClient")
            if screen and hasattr(screen, 'gesture_label'):
                screen.gesture_label.text = text

    def disconnect_air_gesture_client(self):
        self.air_gesture_client_running = False
        self.air_gesture_client_connected = False
        if hasattr(self, 'air_gesture_client_socket') and self.air_gesture_client_socket:
            try:
                self.air_gesture_client_socket.close()
            except:
                pass
            self.air_gesture_client_socket = None
        self.update_air_gesture_client_connection_status("Disconnected", (1, 0, 0, 1))
        self.update_air_gesture_client_gesture("Gesture: None")

    def count_fingers(self, hand_landmarks):
        """Returns number of fingers open (0-5)"""
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        count = 0
        for tip, pip in zip(tips, pips):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                count += 1
        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
            count += 1
        return count

    # --- Volume Camera ---
    def start_volume_camera(self):
        if self.camera_running:
            return
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            return

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
        if not self.camera_running or not self.capture:
            return
        ret, frame = self.capture.read()
        if not ret:
            return
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
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.root.get_screen("volumecamera").camera_view.texture = texture

    # --- Air Volume Gesture Server ---
    def start_air_volume_server(self):
        if self.air_server_running:
            return

        try:
            server_ip = self.root.get_screen("AirVolume").ip_input.text
            server_port = int(self.root.get_screen("AirVolume").port_input.text)

            if server_ip == "":
                self.update_air_status("Please enter IP address")
                return

            if server_port < 1024 or server_port > 65535:
                self.update_air_status("Port must be 1024-65535")
                return

        except ValueError:
            self.update_air_status("Invalid port number")
            return
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

            Clock.schedule_once(
                lambda dt: self.update_air_status(f"Waiting for client on {server_ip}:{server_port}..."))
            print(f"Waiting for client connection on {server_ip}:{server_port}...")

            try:
                self.air_client_socket, addr = self.air_server_socket.accept()
                print(f"Connected to {addr}")
                Clock.schedule_once(lambda dt: self.update_air_status(f"Connected to {addr[0]}:{addr[1]}"))

                self.air_capture = cv2.VideoCapture(0)
                if not self.air_capture.isOpened():
                    Clock.schedule_once(lambda dt: self.update_air_status("Failed to open camera"))
                    return

                self.air_hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
                self.air_server_running = True
                Clock.schedule_interval(self.update_air_volume_server, 1 / 30)

            except socket.timeout:
                if not self.air_server_running:
                    return

        except Exception as e:
            error_msg = str(e)[:20]
            print(f"Server error: {e}")
            Clock.schedule_once(lambda dt, msg=error_msg: self.update_air_status(f"Error: {msg}"))
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

            if hasattr(self, 'air_client_socket') and self.air_client_socket:
                try:
                    data = pickle.dumps(length)
                    self.air_client_socket.sendall(data)
                except:
                    print("Client disconnected")
                    self.air_client_socket = None
                    Clock.schedule_once(lambda dt: self.update_air_status("Client disconnected - waiting"))

            cv2.circle(frame, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

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

    # --- Navigation ---
    def go_back_to_profile(self):
        self.stop_volume_camera()
        self.stop_air_volume_server()
        self.stop_game_steering()
        self.stop_air_gesture_server()
        self.disconnect_air_gesture_client()
        self.root.current = "profile"

    def go_back_to_profile_from_game(self):
        self.stop_game_steering()
        self.root.current = "profile"

    def go_back_to_profile_from_air_gesture(self):
        self.stop_air_gesture_server()
        self.root.current = "profile"

    def go_back_to_profile_from_air_gesture_client(self):
        self.disconnect_air_gesture_client()
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

    def on_back_button(self, window, key, *args):
        current = self.root.current
        if key == 27:  # Hardware back
            if current in ["server", "volumecamera", "volumeoption", "AirVolume", "AirGestureClient", "GameSteering",
                           "GestureOption", "AirGestureServer"]:
                if current == "AirGestureClient":
                    self.disconnect_air_gesture_client()
                elif current == "AirVolume":
                    self.stop_air_volume_server()
                elif current == "GameSteering":
                    self.stop_game_steering()
                elif current == "AirGestureServer":
                    self.stop_air_gesture_server()
                self.root.current = "profile"
                return True
            elif current == "camera":
                self.root.current = "server"
                return True
        return False

    def on_stop(self):
        self.stop_volume_camera()
        self.stop_air_volume_server()
        self.stop_game_steering()
        self.stop_air_gesture_server()
        self.disconnect_air_gesture_client()


if __name__ == "__main__":
    HandServerApp().run()