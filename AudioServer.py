import socket
import pyaudio
import os
from dotenv import load_dotenv

load_dotenv()

HOST = "0.0.0.0"
PORT = 5001

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()
stream = None

print(f"AUDIO SERVER INITIALIZED: {HOST}:{PORT}")

try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print("Waiting for connection...")
        conn, addr = server_socket.accept()

        with conn:
            print(f"Connected Microphone: {addr}")

            while True:
                try:
                    data = conn.recv(CHUNK)
                    if not data:
                        break
                    stream.write(data)
                except Exception as e:
                    print(f"Error: {e}")
                    break

except KeyboardInterrupt:
    print("\nStopping Audio...")
except Exception as e:
    print(f"\nfatal error : {e}")
finally:
    if stream is not None:
        stream.stop_stream()
        stream.close()
    p.terminate()
