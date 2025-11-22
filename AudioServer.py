import socket
import pyaudio
import os
import sys
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def ignore_stderr():
    original_stderr_fd = None
    saved_stderr_fd = None
    try:
        original_stderr_fd = sys.stderr.fileno()
        saved_stderr_fd = os.dup(original_stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, original_stderr_fd)
        os.close(devnull)
        yield
    finally:
        if original_stderr_fd is not None and saved_stderr_fd is not None:
            os.dup2(saved_stderr_fd, original_stderr_fd)
            os.close(saved_stderr_fd)


HOST = "0.0.0.0"
PORT = 5001

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

with ignore_stderr():
    p = pyaudio.PyAudio()

stream = None

print(f"🎧 AUDIO SERVER INITIALIZED: {HOST}:{PORT}")

try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        server_socket.settimeout(1.0)

        print("🎤 Waiting for connection...")

        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"🎤 Connected Microphone: {addr}")
                    conn.settimeout(None)

                    while True:
                        data = conn.recv(CHUNK)
                        if not data:
                            break
                        stream.write(data)

                    print("🎤 Microphone disconnected. Waiting again...")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Connection error: {e}")

except KeyboardInterrupt:
    print("\n🛑 Stopping Audio Server...")
except Exception as e:
    print(f"\n❌ Fatal error: {e}")
finally:
    if stream is not None:
        stream.stop_stream()
        stream.close()
    p.terminate()
