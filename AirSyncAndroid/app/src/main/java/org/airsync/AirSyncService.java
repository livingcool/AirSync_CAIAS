package org.airsync;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.lifecycle.LifecycleService;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.core.content.ContextCompat;
import com.google.common.util.concurrent.ListenableFuture;
import android.graphics.Bitmap;
import android.graphics.Matrix;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AirSyncService extends LifecycleService {
    private static final String CHANNEL_ID = "AirSyncGestureService";
    private static final int NOTIFICATION_ID = 1;

    private GestureDetector gestureDetector;
    private NearbyManager nearbyManager;
    private ExecutorService cameraExecutor;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        cameraExecutor = Executors.newSingleThreadExecutor();
        
        gestureDetector = new GestureDetector(this, gesture -> {
            Log.d("AirSync", "Service detected gesture: " + gesture);
            handleGesture(gesture);
        });

        nearbyManager = new NearbyManager(this, android.os.Build.MODEL + "_BG");
    }

    public static final String ACTION_START_MONITORING = "org.airsync.action.START_MONITORING";
    public static final String ACTION_STOP_MONITORING = "org.airsync.action.STOP_MONITORING";

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        super.onStartCommand(intent, flags, startId);
        
        if (intent != null && ACTION_STOP_MONITORING.equals(intent.getAction())) {
            Log.d("AirSync", "Stopping background camera monitoring");
            stopCamera();
        } else {
            Log.d("AirSync", "Starting background foreground service");
            startMonitoring();
        }

        return START_STICKY;
    }

    private void startMonitoring() {
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("AirSync Radar Active")
                .setContentText("Hands-free transfer ready. Monitoring for gestures...")
                .setSmallIcon(android.R.drawable.ic_menu_camera)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();

        startForeground(NOTIFICATION_ID, notification);
        startCamera();
    }

    private void stopCamera() {
        Log.d("AirSync", "Service: Releasing camera resource...");
        try {
            ProcessCameraProvider cameraProvider = ProcessCameraProvider.getInstance(this).get();
            cameraProvider.unbindAll();
            Log.d("AirSync", "Service: Camera unbind complete");
        } catch (Exception e) {
            Log.e("AirSync", "Failed to stop camera", e);
        }
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture = ProcessCameraProvider.getInstance(this);
        cameraProviderFuture.addListener(() -> {
            try {
                ProcessCameraProvider cameraProvider = cameraProviderFuture.get();
                ImageAnalysis imageAnalysis = new ImageAnalysis.Builder()
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build();

                imageAnalysis.setAnalyzer(cameraExecutor, image -> {
                    Bitmap bitmap = toBitmap(image);
                    if (bitmap != null && gestureDetector != null) {
                        gestureDetector.processFrame(bitmap);
                    }
                    image.close();
                });

                CameraSelector cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA;
                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, cameraSelector, imageAnalysis);
            } catch (Exception e) {
                Log.e("AirSync", "Background Camera failed", e);
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void handleGesture(String gesture) {
        if (gesture.equals("GRAB")) {
            Log.d("AirSync", "GRAB detected - Visualizing and Advertising...");
            showSystemOverlayAnimation(0xFFBB86FC); // Purple Flash
            nearbyManager.startAdvertising();
        } else if (gesture.equals("RELEASE")) {
            Log.d("AirSync", "RELEASE detected - Visualizing and Discovering...");
            showSystemOverlayAnimation(0xFF03DAC6); // Teal Flash
            nearbyManager.startDiscovery();
        }
    }

    private void showSystemOverlayAnimation(int color) {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M &&
                !android.provider.Settings.canDrawOverlays(this)) {
            return;
        }

        final android.view.WindowManager windowManager = (android.view.WindowManager) getSystemService(WINDOW_SERVICE);
        if (windowManager == null) return;

        final android.view.View overlay = new android.view.View(this);
        overlay.setBackgroundColor(color);
        overlay.setAlpha(0.4f);

        int type = android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O ?
                android.view.WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY :
                android.view.WindowManager.LayoutParams.TYPE_PHONE;

        final android.view.WindowManager.LayoutParams params = new android.view.WindowManager.LayoutParams(
                android.view.WindowManager.LayoutParams.MATCH_PARENT,
                android.view.WindowManager.LayoutParams.MATCH_PARENT,
                type,
                android.view.WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        android.view.WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE |
                        android.view.WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                android.graphics.PixelFormat.TRANSLUCENT
        );

        try {
            windowManager.addView(overlay, params);
            overlay.animate().alpha(0f).setDuration(600).withEndAction(() -> {
                try {
                    windowManager.removeView(overlay);
                } catch (Exception ignored) {}
            });
        } catch (Exception e) {
            Log.e("AirSync", "Overlay failed", e);
        }
    }

    private Bitmap toBitmap(androidx.camera.core.ImageProxy image) {
        try {
            androidx.camera.core.ImageProxy.PlaneProxy[] planes = image.getPlanes();
            if (planes.length < 3) return null;
            
            java.nio.ByteBuffer yBuffer = planes[0].getBuffer();
            java.nio.ByteBuffer uBuffer = planes[1].getBuffer();
            java.nio.ByteBuffer vBuffer = planes[2].getBuffer();

            int ySize = yBuffer.remaining();
            int uSize = uBuffer.remaining();
            int vSize = vBuffer.remaining();

            byte[] nv21 = new byte[ySize + uSize + vSize];
            yBuffer.get(nv21, 0, ySize);
            vBuffer.get(nv21, ySize, vSize);
            uBuffer.get(nv21, ySize + vSize, uSize);

            android.graphics.YuvImage yuvImage = new android.graphics.YuvImage(nv21, android.graphics.ImageFormat.NV21, image.getWidth(), image.getHeight(), null);
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            yuvImage.compressToJpeg(new android.graphics.Rect(0, 0, yuvImage.getWidth(), yuvImage.getHeight()), 100, out);
            byte[] imageBytes = out.toByteArray();
            Bitmap bitmap = android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);

            int rotation = image.getImageInfo().getRotationDegrees();
            Matrix matrix = new Matrix();
            matrix.postRotate(rotation);
            matrix.postScale(-1, 1, bitmap.getWidth() / 2f, bitmap.getHeight() / 2f);

            return Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
        } catch (Exception e) {
            return null;
        }
    }

    private void createNotificationChannel() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID,
                    "AirSync Gesture Service Channel",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(serviceChannel);
            }
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (cameraExecutor != null) cameraExecutor.shutdown();
        Log.d("AirSync", "Foreground Service Destroyed");
    }
}
