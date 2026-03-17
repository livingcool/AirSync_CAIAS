package org.airsync;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.camera.core.ImageProxy;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;

import java.io.File;
import java.io.IOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final int PERMISSION_REQ_CODE = 10;
    private static final int FILE_PICKER_CODE = 100;

    private TextView statusLabel, IPLabel, gestureLabel;
    private EditText ipInput;
    private ProgressBar progressBar;
    private PreviewView viewFinder;
    private String selectedFilePath;
    private NearbyManager nearbyManager;
    private GestureDetector gestureDetector;
    private ExecutorService cameraExecutor;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusLabel = findViewById(R.id.statusLabel);
        IPLabel = findViewById(R.id.ipLabel);
        gestureLabel = findViewById(R.id.gestureLabel);
        ipInput = findViewById(R.id.ipInput);
        progressBar = findViewById(R.id.progressBar);
        viewFinder = findViewById(R.id.viewFinder);

        // Hide IP fields as Nearby doesn't need them
        IPLabel.setVisibility(View.GONE);
        ipInput.setVisibility(View.GONE);

        // Start AirSync Background Service
        Intent serviceIntent = new Intent(this, AirSyncService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }

        nearbyManager = new NearbyManager(this, Build.MODEL);
        nearbyManager.setListener(new NearbyManager.NearbyListener() {
            @Override
            public void onFileReceived(String path) {
                runOnUiThread(() -> statusLabel.setText("Caught file: " + path));
            }

            @Override
            public void onTransferProgress(long bytesTransferred, long totalBytes) {
                runOnUiThread(() -> {
                    int percent = (int) (bytesTransferred * 100 / totalBytes);
                    progressBar.setProgress(percent);
                });
            }

            @Override
            public void onStatusUpdate(String status) {
                runOnUiThread(() -> statusLabel.setText(status));
            }
        });

        findViewById(R.id.btnSelectFile).setOnClickListener(v -> pickFile());
        findViewById(R.id.btnReceiveMode).setOnClickListener(v -> nearbyManager.startDiscovery());

        if (allPermissionsGranted()) {
            Toast.makeText(this, "DEBUG: Permissions already granted", Toast.LENGTH_SHORT).show();
            startCamera();
        } else {
            Toast.makeText(this, "DEBUG: Requesting permissions", Toast.LENGTH_SHORT).show();
            ActivityCompat.requestPermissions(this, new String[]{
                    Manifest.permission.CAMERA}, PERMISSION_REQ_CODE);
        }

        cameraExecutor = Executors.newSingleThreadExecutor();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQ_CODE) {
            if (allPermissionsGranted()) {
                startCamera();
            } else {
                Toast.makeText(this, "Camera permission is required for gesture detection", Toast.LENGTH_LONG).show();
            }
        }
    }

    private void startCamera() {
        Log.d("AirSync", "Initializing Camera and GestureDetector...");
        try {
            // Initialize MediaPipe GestureDetector
            gestureDetector = new GestureDetector(this, gesture -> {
                runOnUiThread(() -> {
                    gestureLabel.setText("Gesture: " + gesture);
                    handleGesture(gesture);
                });
            });
            Toast.makeText(this, "MediaPipe Model Loaded", Toast.LENGTH_SHORT).show();

            // Start Camera Use Cases
            ListenableFuture<ProcessCameraProvider> cameraProviderFuture = ProcessCameraProvider.getInstance(this);
            cameraProviderFuture.addListener(() -> {
                try {
                    ProcessCameraProvider cameraProvider = cameraProviderFuture.get();

                    Preview preview = new Preview.Builder().build();
                    preview.setSurfaceProvider(viewFinder.getSurfaceProvider());

                    ImageAnalysis imageAnalysis = new ImageAnalysis.Builder()
                            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                            .build();

                    imageAnalysis.setAnalyzer(cameraExecutor, image -> {
                        Bitmap bitmap = toBitmap(image);
                        if (bitmap != null) {
                            if (gestureDetector != null) {
                                final String debugResult = gestureDetector.processFrame(bitmap);
                                runOnUiThread(() -> {
                                    if (debugResult.startsWith("UNKNOWN")) {
                                        gestureLabel.setText("Gesture: None");
                                    } else {
                                        gestureLabel.setText("Detected: " + debugResult);
                                    }
                                });
                            }
                        }
                        image.close();
                    });

                    CameraSelector cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA;
                    cameraProvider.unbindAll();
                    cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalysis);
                    Log.d("AirSync", "Camera bound to lifecycle");
                } catch (Exception e) {
                    Log.e("AirSync", "Camera initialization failed", e);
                    runOnUiThread(() -> Toast.makeText(MainActivity.this, "Camera Error: " + e.getMessage(), Toast.LENGTH_LONG).show());
                }
            }, ContextCompat.getMainExecutor(this));

        } catch (Exception e) {
            Log.e("AirSync", "GestureDetector Init Failed", e);
            e.printStackTrace();
            Toast.makeText(this, "Model Load Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void handleGesture(String gesture) {
        // Visual Feedback on Gesture Detection
        View overlay = findViewById(R.id.gestureOverlay);
        if (overlay != null) {
            overlay.setAlpha(0.6f);
            overlay.animate().alpha(0.1f).setDuration(400);
        }

        switch (gesture) {
            case "GRAB":
                triggerSend();
                break;
            case "RELEASE":
                enterReceiveMode();
                break;
            case "CANCEL":
                statusLabel.setText("Operation Cancelled");
                break;
            case "CONFIRM":
                statusLabel.setText("Action Confirmed!");
                break;
        }
    }

    private void pickFile() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*");
        startActivityForResult(intent, FILE_PICKER_CODE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_PICKER_CODE && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            selectedFilePath = uri.getPath(); // Simplified; real path needs resolving
            statusLabel.setText("File: " + selectedFilePath);
        }
    }

    private void triggerSend() {
        if (selectedFilePath == null) {
            statusLabel.setText("No file selected!");
            return;
        }
        
        File file = new File(selectedFilePath);
        statusLabel.setText("Grabbing " + file.getName() + "...");
        nearbyManager.startAdvertising();
    }

    private void enterReceiveMode() {
        statusLabel.setText("Ready to catch...");
        nearbyManager.startDiscovery();
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

            // Handle Rotation and Mirroring
            int rotation = image.getImageInfo().getRotationDegrees();
            android.graphics.Matrix matrix = new android.graphics.Matrix();
            matrix.postRotate(rotation);
            
            // Mirroring for Front Camera (Crucial for matching user gestures)
            matrix.postScale(-1, 1, bitmap.getWidth() / 2f, bitmap.getHeight() / 2f);

            return Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
        } catch (Exception e) {
            Log.e("AirSync", "Bitmap conversion failed", e);
            return null;
        }
    }

    private boolean allPermissionsGranted() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        cameraExecutor.shutdown();
    }
}
