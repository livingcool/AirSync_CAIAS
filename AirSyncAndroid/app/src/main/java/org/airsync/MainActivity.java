package org.airsync;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
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
    private static final String[] REQUIRED_PERMISSIONS;
    static {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            REQUIRED_PERMISSIONS = new String[]{
                Manifest.permission.CAMERA,
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_ADVERTISE,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.NEARBY_WIFI_DEVICES,
                Manifest.permission.POST_NOTIFICATIONS,
                Manifest.permission.ACCESS_FINE_LOCATION
            };
        } else if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
            REQUIRED_PERMISSIONS = new String[]{
                Manifest.permission.CAMERA,
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_ADVERTISE,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.ACCESS_FINE_LOCATION
            };
        } else {
            REQUIRED_PERMISSIONS = new String[]{
                Manifest.permission.CAMERA,
                Manifest.permission.ACCESS_FINE_LOCATION
            };
        }
    }

    private TextView statusLabel;
    private TextView IPLabel;
    private TextView gestureLabel;
    private EditText ipInput;
    private ProgressBar progressBar;
    private PreviewView viewFinder;
    private NearbyManager nearbyManager;
    private GestureDetector gestureDetector;
    private ExecutorService cameraExecutor;
    private String selectedFilePath;

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

        // Check for System Overlay Permission (Settings prompt)
        if (!android.provider.Settings.canDrawOverlays(this)) {
            Intent intent = new Intent(android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        }

        // Hide IP fields as Nearby doesn't need them
        IPLabel.setVisibility(View.GONE);
        ipInput.setVisibility(View.GONE);

        nearbyManager = new NearbyManager(this, android.os.Build.MODEL);
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

        // Hide IP fields as Nearby doesn't need them
        IPLabel.setVisibility(View.GONE);
        ipInput.setVisibility(View.GONE);

        cameraExecutor = Executors.newSingleThreadExecutor();

        if (allPermissionsGranted()) {
            startCamera();
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, PERMISSION_REQ_CODE);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQ_CODE) {
            if (allPermissionsGranted()) {
                startCamera();
            } else {
                Toast.makeText(this, "Permissions are required for gesture transfer to work.", Toast.LENGTH_LONG).show();
            }
        }
    }

    private void startCamera() {
        Log.d("AirSync", "Initializing Camera and GestureDetector...");
        gestureLabel.setText("Gesture: Initializing...");

        // Start AirSync Background Service with STOP_MONITORING to release camera
        Intent serviceIntent = new Intent(this, AirSyncService.class);
        serviceIntent.setAction(AirSyncService.ACTION_STOP_MONITORING);
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }

        // Delay camera binding to ensure service had time to release it
        viewFinder.postDelayed(() -> {
            try {
                // Initialize MediaPipe GestureDetector
                gestureDetector = new GestureDetector(this, gesture -> {
                    runOnUiThread(() -> {
                        gestureLabel.setText("Gesture: " + gesture);
                        handleGesture(gesture);
                    });
                });

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
                            if (bitmap != null && gestureDetector != null) {
                                final String debugResult = gestureDetector.processFrame(bitmap);
                                runOnUiThread(() -> {
                                    if (debugResult.startsWith("NONE")) {
                                        gestureLabel.setText("Gesture: Waiting...");
                                    } else {
                                        gestureLabel.setText("Detected: " + debugResult);
                                    }
                                });
                            }
                            image.close();
                        });

                        CameraSelector cameraSelector = new CameraSelector.Builder()
                                .requireLensFacing(CameraSelector.LENS_FACING_FRONT)
                                .build();

                        cameraProvider.unbindAll();
                        cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalysis);
                        
                        runOnUiThread(() -> {
                            gestureLabel.setText("Gesture: Ready");
                            Toast.makeText(this, "Camera & AI Active", Toast.LENGTH_SHORT).show();
                        });

                    } catch (Exception e) {
                        Log.e("AirSync", "Camera Binding Failed", e);
                        runOnUiThread(() -> Toast.makeText(MainActivity.this, "Camera Error: " + e.getMessage(), Toast.LENGTH_LONG).show());
                    }
                }, ContextCompat.getMainExecutor(this));

            } catch (Exception e) {
                Log.e("AirSync", "Camera Setup Failed", e);
                runOnUiThread(() -> Toast.makeText(this, "Setup Error: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }, 800); // 800ms delay for handover
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
            if (planes.length < 3) {
                Log.w("AirSync", "Insufficient planes: " + planes.length);
                return null;
            }
            
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
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    @Override
    protected void onStart() {
        super.onStart();
        // Tell service to release camera
        Intent intent = new Intent(this, AirSyncService.class);
        intent.setAction(AirSyncService.ACTION_STOP_MONITORING);
        startService(intent);
    }

    @Override
    protected void onStop() {
        super.onStop();
        // Tell service to resume background monitoring
        Intent intent = new Intent(this, AirSyncService.class);
        intent.setAction(AirSyncService.ACTION_START_MONITORING);
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(intent);
        } else {
            startService(intent);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        cameraExecutor.shutdown();
    }
}
