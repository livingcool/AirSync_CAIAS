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
    private static final long GESTURE_WINDOW_MS = 800; // Time window to detect a transition

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
            
            // Analyze Hand Landmarks for temporal transitions (Grab/Release)
            if (result.landmarks() != null && !result.landmarks().isEmpty()) {
                analyzeLandmarks(result.landmarks().get(0));
            }
        } else {
            currentState = State.IDLE;
        }

        return gestureLabel + " | State: " + currentState.name();
    }

    private void analyzeLandmarks(List<NormalizedLandmark> landmarks) {
        // Landmarks for Grab/Release logic:
        // 0: Wrist, 4: Thumb Tip, 8: Index Tip, 12: Middle Tip, 16: Ring Tip, 20: Pinky Tip
        
        boolean isOpen = isHandOpen(landmarks);
        long currentTime = System.currentTimeMillis();

        switch (currentState) {
            case IDLE:
                if (isOpen) {
                    currentState = State.OPEN_PALM;
                    lastStateChangeTime = currentTime;
                }
                break;

            case OPEN_PALM:
                if (!isOpen) {
                    // Transition: OPEN -> CLOSED within window = GRAB
                    if (currentTime - lastStateChangeTime < GESTURE_WINDOW_MS) {
                        triggerGesture("GRAB");
                    }
                    currentState = State.CLOSED_FIST;
                    lastStateChangeTime = currentTime;
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
                }
                break;
        }
    }

    private boolean isHandOpen(List<NormalizedLandmark> landmarks) {
        // Simple heuristic: if fingertips are significantly further from the wrist than middle joints
        // landmarks.get(0) is wrist
        float wristY = landmarks.get(0).y();
        
        // Check Index (8), Middle (12), Ring (16)
        return landmarks.get(8).y() < landmarks.get(6).y() &&
               landmarks.get(12).y() < landmarks.get(10).y() &&
               landmarks.get(16).y() < landmarks.get(14).y();
    }

    private void triggerGesture(String gesture) {
        Log.d("AirSync", "Triggered Gesture: " + gesture);
        if (listener != null) {
            listener.onGestureDetected(gesture);
        }
    }
}
