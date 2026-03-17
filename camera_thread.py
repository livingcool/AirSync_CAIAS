import cv2
import threading

class CameraThread(threading.Thread):

    def __init__(self, gesture_detector, on_frame=None):
        super().__init__(daemon=True)
        self.gesture_detector = gesture_detector
        self.on_frame  = on_frame
        self.running   = False

    def run(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            self.gesture_detector.process_frame(frame)
            if self.on_frame:
                self.on_frame(frame)

        self.cap.release()

    def stop(self):
        self.running = False
