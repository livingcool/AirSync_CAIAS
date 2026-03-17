package org.airsync;

import android.content.Context;
import android.graphics.Bitmap;
import android.util.Log;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.framework.image.MPImage;
import com.google.mediapipe.tasks.core.BaseOptions;
import com.google.mediapipe.tasks.vision.gesturerecognizer.GestureRecognizer;
import com.google.mediapipe.tasks.vision.gesturerecognizer.GestureRecognizerResult;
import com.google.mediapipe.tasks.vision.core.RunningMode;

import java.util.HashMap;
import java.util.Map;

public class GestureDetector {
    private GestureRecognizer gestureRecognizer;
    private final OnGestureListener listener;
    private String lastGesture = "";
    private final Map<String, Integer> frameCounts = new HashMap<>();
    private static final int THRESHOLD_FRAMES = 2; // MediaPipe is very stable, can use lower threshold

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

        String detectedGesture = "UNKNOWN";
        float confidence = 0f;

        if (result.gestures() != null && !result.gestures().isEmpty()) {
            // Get the top gesture from the first detected hand
            com.google.mediapipe.tasks.components.containers.Category category = result.gestures().get(0).get(0);
            String rawLabel = category.categoryName();
            confidence = category.score();

            // Map MediaPipe gestures to AirSync actions
            detectedGesture = mapGesture(rawLabel);
        }

        applyThreshold(detectedGesture);
        
        return detectedGesture + " (" + (int)(confidence * 100) + "%)";
    }

    private String mapGesture(String raw) {
        switch (raw) {
            case "Thumb_Up":    return "CONFIRM";
            case "Closed_Fist": return "CANCEL";
            case "Victory":     return "SEND";
            case "ILoveYou":    return "RECEIVE";
            case "Pointing_Up": return "SEND"; // Alternative
            default:            return "UNKNOWN";
        }
    }

    private void applyThreshold(String gesture) {
        if (gesture.equals("UNKNOWN")) {
            frameCounts.clear();
            return;
        }

        int count = frameCounts.getOrDefault(gesture, 0) + 1;
        frameCounts.put(gesture, count);

        if (count >= THRESHOLD_FRAMES && !gesture.equals(lastGesture)) {
            lastGesture = gesture;
            if (listener != null) {
                listener.onGestureDetected(gesture);
            }
        }
    }
}
