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
    
    private enum State { IDLE, OPEN_PALM, CLOSED_FIST }
    private State currentState = State.IDLE;
    private long lastStateChangeTime = 0;
    private static final long GESTURE_WINDOW_MS = 1200; // Increased for better tolerance

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
            Log.d("AirSync", "MediaPipe Label: " + gestureLabel);
            analyzeTransitions(gestureLabel);
        }

        return gestureLabel + " | State: " + currentState.name();
    }

    private void analyzeTransitions(String label) {
        boolean isOpen = label.equalsIgnoreCase("Open_Palm");
        boolean isClosed = label.equalsIgnoreCase("Closed_Fist");
        long currentTime = System.currentTimeMillis();

        switch (currentState) {
            case IDLE:
                if (isOpen) {
                    currentState = State.OPEN_PALM;
                    lastStateChangeTime = currentTime;
                } else if (isClosed) {
                    currentState = State.CLOSED_FIST;
                    lastStateChangeTime = currentTime;
                }
                break;

            case OPEN_PALM:
                if (isClosed) {
                    // Transition: OPEN -> CLOSED within window = GRAB
                    if (currentTime - lastStateChangeTime < GESTURE_WINDOW_MS) {
                        triggerGesture("GRAB");
                    }
                    currentState = State.CLOSED_FIST;
                    lastStateChangeTime = currentTime;
                } else if (!isOpen) {
                    currentState = State.IDLE;
                }
                break;

            case CLOSED_FIST:
                if (isOpen) {
                    // Transition: CLOSED -> OPEN within window = RELEASE
                    if (currentTime - lastStateChangeTime < GESTURE_WINDOW_MS) {
                        triggerGesture("RELEASE");
                    }
                    currentState = State.OPEN_PALM;
                    lastStateChangeTime = currentTime;
                } else if (!isClosed) {
                    currentState = State.IDLE;
                }
                break;
        }
    }

    private void triggerGesture(String gesture) {
        Log.d("AirSync", "Triggered Gesture: " + gesture);
        if (listener != null) {
            listener.onGestureDetected(gesture);
        }
    }
}
