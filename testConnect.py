import socket
import struct
import time
import cv2
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

try:
    PORT = int(os.getenv("PORT", "5000"))
except (TypeError, ValueError):
    PORT = 5000

HOST = os.getenv("HOST_TARGET", "127.0.0.1")

print("Connecting")

"""TEST IMAGE"""

try:
    img = cv2.imread("test.jpg")
    if img is None:
        raise FileNotFoundError("File not found")
    print(f"Using {img} as frame")
except:
    print("File not found. Using a red frame")
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (0, 255, 0)

ret, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
if not ret:
    print("Coding image error")
    exit()


data_bytes = buffer.tobytes()
print(f"Image size {len(data_bytes)}")


"""Connect to server"""

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Server Connected")

    while True:
        size = len(data_bytes)

        header = struct.pack("I", size)
        client_socket.sendall(header + data_bytes)

        time.sleep(1 / 30)
except ConnectionRefusedError:
    print(f"Connection refused. try re-lauching server")
except Exception as e:
    print(f"{e}")


print("Finished client")
