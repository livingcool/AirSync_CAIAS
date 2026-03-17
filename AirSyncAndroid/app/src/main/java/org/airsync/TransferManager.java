package org.airsync;

import android.os.Handler;
import android.os.Looper;
import java.io.*;
import java.net.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class TransferManager {
    private static final int TRANSFER_PORT = 54321;
    private static final int BUFFER_SIZE = 65536;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private TransferListener listener;

    public interface TransferListener {
        void onFileReceived(String path);
        void onProgressUpdate(int percent);
    }

    public void setListener(TransferListener listener) {
        this.listener = listener;
    }

    public void sendFile(String hostIp, String filePath) {
        executor.execute(() -> {
            File file = new File(filePath);
            long fileSize = file.length();
            String fileName = file.getName();

            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(hostIp, TRANSFER_PORT), 10000);
                DataOutputStream dos = new DataOutputStream(socket.getOutputStream());

                String header = fileName + "|" + fileSize;
                byte[] headerBytes = header.getBytes();
                dos.writeInt(headerBytes.length);
                dos.write(headerBytes);

                FileInputStream fis = new FileInputStream(file);
                byte[] buffer = new byte[BUFFER_SIZE];
                int read;
                long sent = 0;
                while ((read = fis.read(buffer)) != -1) {
                    dos.write(buffer, 0, read);
                    sent += read;
                    int progress = (int) ((sent * 100) / fileSize);
                    mainHandler.post(() -> listener.onProgressUpdate(progress));
                }
                dos.flush();
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }

    public void startReceiving(String saveDir) {
        executor.execute(() -> {
            try (ServerSocket serverSocket = new ServerSocket(TRANSFER_PORT)) {
                Socket clientSocket = serverSocket.accept();
                DataInputStream dis = new DataInputStream(clientSocket.getInputStream());

                int headerLen = dis.readInt();
                byte[] headerBytes = new byte[headerLen];
                dis.readFully(headerBytes);
                String header = new String(headerBytes);
                String[] parts = header.split("\\|");
                String fileName = parts[0];
                long fileSize = Long.parseLong(parts[1]);

                File file = new File(saveDir, fileName);
                try (FileOutputStream fos = new FileOutputStream(file)) {
                    byte[] buffer = new byte[BUFFER_SIZE];
                    int read;
                    long received = 0;
                    while (received < fileSize && (read = dis.read(buffer, 0, (int) Math.min(buffer.length, fileSize - received))) != -1) {
                        fos.write(buffer, 0, read);
                        received += read;
                        int progress = (int) ((received * 100) / fileSize);
                        mainHandler.post(() -> listener.onProgressUpdate(progress));
                    }
                }
                mainHandler.post(() -> listener.onFileReceived(file.getAbsolutePath()));
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }

    public String getMyIp() {
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.connect(InetAddress.getByName("8.8.8.8"), 80);
            return socket.getLocalAddress().getHostAddress();
        } catch (Exception e) {
            return "127.0.0.1";
        }
    }
}
