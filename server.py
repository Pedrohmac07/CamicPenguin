import socket
import struct
import cv2
import dotenv
import numpy as np
import pyvirtualcam

import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
"""WHY IT ISNT WORKING GODDAMIT"""

try: PORT


print(f"Initializing server on {HOST}, {PORT}")

W=640
H=480

with pyvirtualcam.Camera(width=640, height=480, fps=30, device='/dev/video0', fmt=pyvirtualcam.PixelFormat.BGR) as cam:
    print(f"Virtual Camera on {cam.device}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        conn, addr = server_socket.accept()
        with conn:
            print(f"Connected {addr}")

            data = b""
            payload_size = struct.calcsize("I")

            while True:
                try:
                    while len(data) < payload_size:
                        packet = conn.recv(4096)
                        if not packet: raise ConnectionError("Client Desconnected")
                        data += packet

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("I", packed_msg_size)[0]

                    while len(data) < msg_size:
                        packet = conn.recv(4096)
                        if not packet: raise ConnectionError("Client Desconnected")
                        data += packet

                    frame_data = data[:msg_size]
                    data = data[msg_size:]

                    frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                    if frame is not None:
                        frame = cv2.resize(frame, (W, H))
                        cam.send(frame)
                        cam.sleep_until_next_frame()
                    else:
                        print("Frame Error")

                except ConnectionError as e:
                    print(f"Error {e}")
                    break
                except Exception as e:
                    print(f"Error {e}")
                    continue

print("Server ended")
