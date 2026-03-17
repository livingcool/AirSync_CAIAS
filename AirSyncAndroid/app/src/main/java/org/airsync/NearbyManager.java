package org.airsync;

import android.content.Context;
import android.net.Uri;
import android.util.Log;
import androidx.annotation.NonNull;
import com.google.android.gms.nearby.Nearby;
import com.google.android.gms.nearby.connection.*;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.OnSuccessListener;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Collections;

public class NearbyManager {
    private static final String SERVICE_ID = "org.airsync.TRANSFER_SERVICE";
    private static final Strategy STRATEGY = Strategy.P2P_STAR;
    private final Context context;
    private final ConnectionsClient connectionsClient;
    private final String nickname;
    private String connectedEndpointId;

    public interface NearbyListener {
        void onFileReceived(String path);
        void onTransferProgress(long bytesTransferred, long totalBytes);
        void onStatusUpdate(String status);
    }

    private NearbyListener listener;

    public NearbyManager(Context context, String nickname) {
        this.context = context;
        this.connectionsClient = Nearby.getConnectionsClient(context);
        this.nickname = nickname;
    }

    public void setListener(NearbyListener listener) {
        this.listener = listener;
    }

    public void startAdvertising() {
        AdvertisingOptions advertisingOptions = new AdvertisingOptions.Builder().setStrategy(STRATEGY).build();
        connectionsClient.startAdvertising(nickname, SERVICE_ID, connectionLifecycleCallback, advertisingOptions)
                .addOnSuccessListener(unused -> Log.d("AirSync", "Advertising started"))
                .addOnFailureListener(e -> Log.e("AirSync", "Advertising failed", e));
    }

    public void startDiscovery() {
        DiscoveryOptions discoveryOptions = new DiscoveryOptions.Builder().setStrategy(STRATEGY).build();
        connectionsClient.startDiscovery(SERVICE_ID, endpointDiscoveryCallback, discoveryOptions)
                .addOnSuccessListener(unused -> Log.d("AirSync", "Discovery started"))
                .addOnFailureListener(e -> Log.e("AirSync", "Discovery failed", e));
    }

    public void sendFile(File file) {
        if (connectedEndpointId == null) {
            Log.e("AirSync", "No connected endpoint");
            return;
        }

        try {
            Payload payload = Payload.fromFile(file);
            connectionsClient.sendPayload(connectedEndpointId, payload)
                    .addOnSuccessListener(unused -> Log.d("AirSync", "Payload send started"))
                    .addOnFailureListener(e -> Log.e("AirSync", "Payload send failed", e));
        } catch (FileNotFoundException e) {
            Log.e("AirSync", "File not found", e);
        }
    }

    private final ConnectionLifecycleCallback connectionLifecycleCallback = new ConnectionLifecycleCallback() {
        @Override
        public void onConnectionInitiated(@NonNull String endpointId, @NonNull ConnectionInfo info) {
            connectionsClient.acceptConnection(endpointId, payloadCallback);
            Log.d("AirSync", "Connection initiated with " + info.getEndpointName());
        }

        @Override
        public void onConnectionResult(@NonNull String endpointId, @NonNull ConnectionResolution result) {
            if (result.getStatus().isSuccess()) {
                connectedEndpointId = endpointId;
                Log.d("AirSync", "Connected to " + endpointId);
            }
        }

        @Override
        public void onDisconnected(@NonNull String endpointId) {
            connectedEndpointId = null;
            Log.d("AirSync", "Disconnected from " + endpointId);
        }
    };

    private final EndpointDiscoveryCallback endpointDiscoveryCallback = new EndpointDiscoveryCallback() {
        @Override
        public void onEndpointFound(@NonNull String endpointId, @NonNull DiscoveredEndpointInfo info) {
            connectionsClient.requestConnection(nickname, endpointId, connectionLifecycleCallback)
                    .addOnSuccessListener(unused -> Log.d("AirSync", "Connection requested to " + endpointId))
                    .addOnFailureListener(e -> Log.e("AirSync", "Connection request failed", e));
        }

        @Override
        public void onEndpointLost(@NonNull String endpointId) {
            Log.d("AirSync", "Endpoint lost: " + endpointId);
        }
    };

    private final PayloadCallback payloadCallback = new PayloadCallback() {
        @Override
        public void onPayloadReceived(@NonNull String endpointId, @NonNull Payload payload) {
            if (payload.getType() == Payload.Type.FILE) {
                // Handle file reception
                File file = payload.asFile().asJavaFile();
                if (listener != null) listener.onFileReceived(file.getAbsolutePath());
            }
        }

        @Override
        public void onPayloadTransferUpdate(@NonNull String endpointId, @NonNull PayloadTransferUpdate update) {
            if (listener != null) {
                listener.onTransferProgress(update.getBytesTransferred(), update.getTotalBytes());
            }
        }
    };
}
