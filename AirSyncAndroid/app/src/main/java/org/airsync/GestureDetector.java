package org.airsync;

import android.content.Context;
import android.graphics.Bitmap;
import android.util.Log;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.framework.image.MPImage;
import com.google.mediapipe.tasks.components.containers.NormalizedLandmark;
import com.google.mediapipe.tasks.core.BaseOptions;
import com.google.mediapipe.tasks.vision.gesturerecognizer.GestureRecognizer;
import com.google.mediapipe.tasks.vision.gesturerecognizer.GestureRecognizerResult;
import com.google.mediapipe.tasks.vision.core.RunningMode;

import java.util.List;

public class GestureDetector {
    private GestureRecognizer gestureRecognizer;
    private final OnGestureListener listener;
    
    private enum State { IDLE, PALM_DETECTED, FIST_DETECTED }
    private State currentState = State.IDLE;
    private long lastTriggerTime = 0;
    private long stateEntryTime = 0;
    private static final long GESTURE_WINDOW_MS = 1500;
    private static final long COOLDOWN_MS = 3000;

    public interface OnGestureListener {
        void onGestureDetected(String gesture);
    }

    public GestureDetector(Context context, OnGestureListener listener) {
        this.listener = listener;
        try {
            BaseOptions baseOptions = BaseOptions.builder()
                    .setModelAssetPath("gesture_recognizer.task")
                    .build();

            GestureRecognizer.GestureRecognizerOptions options = GestureRecognizer.GestureRecognizerOptions.builder()
                    .setBaseOptions(baseOptions)
                    .setRunningMode(RunningMode.IMAGE)
                    .build();

            gestureRecognizer = GestureRecognizer.createFromOptions(context, options);
            Log.d("AirSync", "MediaPipe GestureRecognizer created successfully");
        } catch (Exception e) {
            Log.e("AirSync", "Failed to create MediaPipe GestureRecognizer", e);
        }
    }

    public String processFrame(Bitmap bitmap) {
        if (gestureRecognizer == null) return "Error: Recognizer null";

        MPImage mpImage = new BitmapImageBuilder(bitmap).build();
        GestureRecognizerResult result = gestureRecognizer.recognize(mpImage);

        String gestureLabel = "NONE";
        if (result.gestures() != null && !result.gestures().isEmpty()) {
            gestureLabel = result.gestures().get(0).get(0).categoryName();
            analyzeMotion(gestureLabel);
        }

        return gestureLabel + " | Motion: " + currentState.name();
    }

    private void analyzeMotion(String label) {
        long currentTime = System.currentTimeMillis();
        
        // Cooldown check: Prevent accidental multiple triggers
        if (currentTime - lastTriggerTime < COOLDOWN_MS) {
            return;
        }

        boolean isOpen = label.equalsIgnoreCase("Open_Palm");
        boolean isClosed = label.equalsIgnoreCase("Closed_Fist");

        switch (currentState) {
            case IDLE:
                if (isOpen) {
                    currentState = State.PALM_DETECTED;
                    stateEntryTime = currentTime;
                    Log.d("AirSync", "Motion Start: Palm Detected");
                } else if (isClosed) {
                    currentState = State.FIST_DETECTED;
                    stateEntryTime = currentTime;
                    Log.d("AirSync", "Motion Start: Fist Detected");
                }
                break;

            case PALM_DETECTED:
                if (isClosed) {
                    // Sequence: PALM -> FIST = GRAB
                    if (currentTime - stateEntryTime < GESTURE_WINDOW_MS) {
                        triggerGesture("GRAB");
                        lastTriggerTime = currentTime;
                    }
                    currentState = State.IDLE;
                } else if (!isOpen && (currentTime - stateEntryTime > GESTURE_WINDOW_MS)) {
                    currentState = State.IDLE;
                }
                break;

            case FIST_DETECTED:
                if (isOpen) {
                    // Sequence: FIST -> PALM = RELEASE
                    if (currentTime - stateEntryTime < GESTURE_WINDOW_MS) {
                        triggerGesture("RELEASE");
                        lastTriggerTime = currentTime;
                    }
                    currentState = State.IDLE;
                } else if (!isClosed && (currentTime - stateEntryTime > GESTURE_WINDOW_MS)) {
                    currentState = State.IDLE;
                }
                break;
        }
    }

    private void triggerGesture(String gesture) {
        Log.d("AirSync", "MATCHED MOTION: " + gesture);
        if (listener != null) {
            listener.onGestureDetected(gesture);
        }
    }
}
