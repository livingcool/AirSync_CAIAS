import cv2
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras import layers, models

# ── CONFIG ────────────────────────────────────────────────────
GESTURES     = ["CANCEL", "CONFIRM", "RECEIVE", "SEND", "UNKNOWN"]
SAMPLES_EACH = 300       # Increased for better accuracy
IMG_SIZE     = 224
DATA_DIR     = "gesture_data"
MODEL_OUT    = "gesture_model.tflite"

# ── STEP 1: COLLECT TRAINING DATA ─────────────────────────────
def collect_data():
    cap = cv2.VideoCapture(0)
    os.makedirs(DATA_DIR, exist_ok=True)

    for gesture in GESTURES:
        gesture_dir = os.path.join(DATA_DIR, gesture)
        os.makedirs(gesture_dir, exist_ok=True)
        print(f"\n--- Show gesture: {gesture} ---")
        print("Press SPACE to start collecting, Q to skip")

        # Wait for space
        while True:
            ret, frame = cap.read()
            if not ret: continue
            text = f"Ready for: {gesture} (SPACE to start)"
            if gesture == "UNKNOWN":
                text = "Collect background (various distances/lighting)"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.imshow("Collecting", frame)
            key = cv2.waitKey(1)
            if key == ord(" "):
                break
            if key == ord("q"):
                break

        # Collect samples
        count = 0
        while count < SAMPLES_EACH:
            ret, frame = cap.read()
            if not ret: continue
            img_path = os.path.join(gesture_dir, f"{count:04d}.jpg")
            cv2.imwrite(img_path, frame)
            count += 1
            cv2.putText(frame, f"{gesture}: {count}/{SAMPLES_EACH}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.imshow("Collecting", frame)
            if cv2.waitKey(1) == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("\nData collection complete!")

# ── STEP 2: TRAIN MODEL ───────────────────────────────────────
def train_model():
    # Load dataset using Keras image generator
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0/255,
        validation_split=0.2,
        rotation_range=20,      # Increased
        width_shift_range=0.2,   # Increased
        height_shift_range=0.2,  # Increased
        zoom_range=0.2,          # Added zoom
        brightness_range=[0.8, 1.2], # Added brightness variety
        horizontal_flip=True
    )

    train_data = datagen.flow_from_directory(
        DATA_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=32,
        class_mode="categorical",
        subset="training"
    )

    val_data = datagen.flow_from_directory(
        DATA_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=32,
        class_mode="categorical",
        subset="validation"
    )

    # Transfer learning: MobileNetV2 base (fast + lightweight)
    # This weights="imagenet" includes the pre-trained model knowledge
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False   # freeze base, only train top layers

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(len(GESTURES), activation="softmax")
    ])

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.fit(
        train_data,
        validation_data=val_data,
        epochs=10,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)
        ]
    )

    return model

# ── STEP 3: CONVERT TO TFLITE ─────────────────────────────────
def export_tflite(model):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Quantize for smaller size + faster inference on Android
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    with open(MODEL_OUT, "wb") as f:
        f.write(tflite_model)

    print(f"\nModel saved: {MODEL_OUT}  ({os.path.getsize(MODEL_OUT)//1024} KB)")

# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(DATA_DIR) or len(os.listdir(DATA_DIR)) < len(GESTURES):
        print("Step 1: Collecting gesture data...")
        collect_data()

    print("\nStep 2: Training model...")
    model = train_model()

    print("\nStep 3: Exporting to TFLite...")
    export_tflite(model)
