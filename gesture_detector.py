import cv2
import numpy as np
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        from tensorflow import lite as tflite
    except ImportError:
        tflite = None

class GestureDetector:

    # Must match exactly how your model was trained
    GESTURE_LABELS = ["CANCEL", "CONFIRM", "RECEIVE", "SEND", "UNKNOWN"]

    # Input size your TFLite model expects
    INPUT_SIZE = (224, 224)

    def __init__(self, model_path: str = "gesture_model.tflite",
                 on_gesture_detected=None):
        self.on_gesture_detected = on_gesture_detected
        self.last_gesture = ""
        self.frame_counts = {}
        self.THRESHOLD_FRAMES = 3       # hold gesture for 3 frames to fire
        self.CONFIDENCE_MIN   = 0.75    # ignore predictions below 75%

        # Load TFLite model
        try:
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()

            self.input_details  = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            # Check if model expects float32 or uint8 (quantized)
            self.is_quantized = (
                self.input_details[0]["dtype"] == np.uint8
            )
        except Exception as e:
            print(f"Error loading TFLite model: {e}")
            self.interpreter = None

    def process_frame(self, frame: np.ndarray):
        """
        Call with each raw OpenCV BGR frame.
        Preprocesses → runs TFLite inference → classifies gesture.
        """
        if self.interpreter is None:
            return

        preprocessed = self._preprocess(frame)
        gesture, confidence = self._run_inference(preprocessed)
        self._apply_threshold(gesture, confidence)

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize, normalize, and batch the frame for TFLite input."""
        # Resize to model's expected input
        resized = cv2.resize(frame, self.INPUT_SIZE)

        # Convert BGR (OpenCV default) to RGB (model expects RGB)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        if self.is_quantized:
            # Quantized model: keep as uint8 [0-255]
            img = rgb.astype(np.uint8)
        else:
            # Float model: normalize to [0.0 - 1.0]
            img = rgb.astype(np.float32) / 255.0

        # Add batch dimension: (224, 224, 3) → (1, 224, 224, 3)
        return np.expand_dims(img, axis=0)

    def _run_inference(self, input_data: np.ndarray):
        """Run TFLite interpreter and return (gesture_label, confidence)."""
        self.interpreter.set_tensor(
            self.input_details[0]["index"], input_data
        )
        self.interpreter.invoke()

        # Output is shape [1, num_classes] — softmax probabilities
        output = self.interpreter.get_tensor(
            self.output_details[0]["index"]
        )[0]  # remove batch dim → shape [num_classes]

        best_idx    = int(np.argmax(output))
        confidence  = float(output[best_idx])
        gesture     = self.GESTURE_LABELS[best_idx]

        return gesture, confidence

    def _apply_threshold(self, gesture: str, confidence: float):
        """
        Only fire callback after:
        - confidence >= CONFIDENCE_MIN (75%)
        - same gesture held for THRESHOLD_FRAMES (3) consecutive frames
        - gesture actually changed from last fired gesture
        """
        if confidence < self.CONFIDENCE_MIN:
            gesture = "UNKNOWN"

        # Increment count for current gesture, reset all others
        for g in list(self.frame_counts.keys()):
            if g != gesture:
                self.frame_counts[g] = 0
        self.frame_counts[gesture] = self.frame_counts.get(gesture, 0) + 1

        if (self.frame_counts[gesture] >= self.THRESHOLD_FRAMES
                and gesture != self.last_gesture
                and gesture != "UNKNOWN"):
            self.last_gesture = gesture
            if self.on_gesture_detected:
                self.on_gesture_detected(gesture)
