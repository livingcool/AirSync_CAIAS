import socket
import threading
import os

TRANSFER_PORT = 54321
BUFFER_SIZE   = 65536

class TransferManager:

    def __init__(self):
        self.on_file_received   = None
        self.on_progress_update = None

    def send_file(self, host_ip: str, filepath: str):
        def _send():
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(10)
                    s.connect((host_ip, TRANSFER_PORT))
                    header = f"{filename}|{filesize}".encode()
                    s.sendall(len(header).to_bytes(4, "big") + header)
                    sent = 0
                    with open(filepath, "rb") as f:
                        while chunk := f.read(BUFFER_SIZE):
                            s.sendall(chunk)
                            sent += len(chunk)
                            if self.on_progress_update:
                                self.on_progress_update(int(sent / filesize * 100))
            except Exception as e:
                print(f"Send error: {e}")
        threading.Thread(target=_send, daemon=True).start()

    def start_receiving(self, save_dir: str = "."):
        def _listen():
            try:
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    server.bind(("0.0.0.0", TRANSFER_PORT))
                    server.listen(1)
                    conn, _ = server.accept()
                    with conn:
                        header_len = int.from_bytes(conn.recv(4), "big")
                        header     = conn.recv(header_len).decode()
                        filename, filesize = header.split("|")
                        filesize   = int(filesize)
                        save_path  = os.path.join(save_dir, filename)
                        received   = 0
                        with open(save_path, "wb") as f:
                            while received < filesize:
                                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                                if not chunk:
                                    break
                                f.write(chunk)
                                received += len(chunk)
                                if self.on_progress_update:
                                    self.on_progress_update(int(received / filesize * 100))
                        if self.on_file_received:
                            self.on_file_received(save_path)
            except Exception as e:
                print(f"Receive error: {e}")
        threading.Thread(target=_listen, daemon=True).start()

    def get_my_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
