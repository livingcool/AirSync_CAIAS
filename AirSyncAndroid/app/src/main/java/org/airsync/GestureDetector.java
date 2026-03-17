package org.airsync;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.graphics.Bitmap;
import android.util.Log;
import org.tensorflow.lite.Interpreter;
import org.tensorflow.lite.support.common.ops.NormalizeOp;
import org.tensorflow.lite.support.image.ImageProcessor;
import org.tensorflow.lite.support.image.TensorImage;
import org.tensorflow.lite.support.image.ops.ResizeOp;
import org.tensorflow.lite.support.common.FileUtil;
import java.io.IOException;
import java.nio.MappedByteBuffer;
import java.util.HashMap;
import java.util.Map;

public class GestureDetector {
    private final Interpreter interpreter;
    private final String[] labels = {"CANCEL", "CONFIRM", "RECEIVE", "SEND", "UNKNOWN"};
    private String lastGesture = "";
    private final Map<String, Integer> frameCounts = new HashMap<>();
    private static final int THRESHOLD_FRAMES = 3;
    private static final float CONFIDENCE_MIN = 0.75f;
    private final OnGestureListener listener;

    public interface OnGestureListener {
        void onGestureDetected(String gesture);
    }

    public GestureDetector(Context context, String modelPath, OnGestureListener listener) throws IOException {
        this.listener = listener;
        MappedByteBuffer buffer = FileUtil.loadMappedFile(context, modelPath);
        if (buffer == null) throw new IOException("Failed to load model buffer");
        try {
            interpreter = new Interpreter(buffer);
            Log.d("AirSync", "TFLite Interpreter created successfully");
        } catch (Exception e) {
            Log.e("AirSync", "Failed to create TFLite Interpreter", e);
            throw e;
        }
    }

    public String processFrame(Bitmap bitmap) {
        ImageProcessor imageProcessor = new ImageProcessor.Builder()
                .add(new ResizeOp(224, 224, ResizeOp.ResizeMethod.BILINEAR))
                .add(new NormalizeOp(0f, 255f)) // Normalize to [0,1]
                .build();

        TensorImage tensorImage = new TensorImage(org.tensorflow.lite.DataType.FLOAT32);
        tensorImage.load(bitmap);
        tensorImage = imageProcessor.process(tensorImage);

        float[][] output = new float[1][labels.length];
        interpreter.run(tensorImage.getBuffer(), output);

        int bestIdx = 0;
        float maxProb = output[0][0];
        for (int i = 1; i < labels.length; i++) {
            if (output[0][i] > maxProb) {
                maxProb = output[0][i];
                bestIdx = i;
            }
        }

        String gesture = labels[bestIdx];
        String debugInfo = gesture + " (" + (int)(maxProb * 100) + "%)";
        
        if (maxProb < CONFIDENCE_MIN) {
            gesture = "UNKNOWN";
        }

        applyThreshold(gesture);
        return debugInfo;
    }

    private void applyThreshold(String gesture) {
        for (String g : labels) {
            if (!g.equals(gesture)) frameCounts.put(g, 0);
        }
        int count = frameCounts.getOrDefault(gesture, 0) + 1;
        frameCounts.put(gesture, count);

        if (count >= THRESHOLD_FRAMES && !gesture.equals(lastGesture) && !gesture.equals("UNKNOWN")) {
            lastGesture = gesture;
            if (listener != null) {
                listener.onGestureDetected(gesture);
            }
        }
    }
}
