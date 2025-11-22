"""
Audio Server
Receives Audio and transmits it to pc.
"""

import os
import sys
import socket

from contextlib import contextmanager
from dotenv import load_dotenv
import pyaudio

load_dotenv()


@contextmanager
def ignore_stderr():
    """Supress uselless PyAudio errors"""
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


def main():
    """Main Audio Function"""
    with ignore_stderr():
        p_audio = pyaudio.PyAudio()

    stream = None
    print(f"INITIALIZED AUDIO SERVER: {HOST}:{PORT}")

    try:
        stream = p_audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            server_socket.settimeout(1.0)

            print("Waiting for connection...")

            while True:
                try:
                    conn, addr = server_socket.accept()
                    with conn:
                        print(f"Connected: {addr}")
                        conn.settimeout(None)

                        while True:
                            data = conn.recv(CHUNK)
                            if not data:
                                break
                            stream.write(data)
                        print("Disconnected, waiting for new connection...")

                except socket.timeout:
                    continue
                except Exception as error:
                    print(f"Connection error: {error}")

    except KeyboardInterrupt:
        print("\nStopping Audio Server...")
    except Exception as error:
        print(f"\nFatal error: {error}")
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        p_audio.terminate()


if __name__ == "__main__":
    main()
