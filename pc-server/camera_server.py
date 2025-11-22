"""
Camera Server.
Receives an image and creates a virtual camera.
"""

import socket
import struct
import sys
import os

from dotenv import load_dotenv
import cv2
import numpy as np
import pyvirtualcam

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
try:
    PORT = int(os.getenv("PORT", "5000"))
except ValueError:
    PORT = 5000

DEVICE_CAM = "/dev/video20"
WIDTH, HEIGHT = 640, 480

print(f"CAMERA SERVER INITIALIZED: {HOST}:{PORT} -> {DEVICE_CAM}", flush=True)

if not os.path.exists(DEVICE_CAM):
    print(f"FATAL ERROR: {DEVICE_CAM} Doesnt exist", flush=True)
    print(
        "   Try: sudo modprobe v4l2loopback devices=1 "
        'video_nr=20 card_label="camera" exclusive_caps=1'
    )
    sys.exit(1)


def main():
    """Main Camera Function. Gets camera in a loop"""
    try:
        with pyvirtualcam.Camera(
            width=WIDTH,
            height=HEIGHT,
            fps=30,
            device=DEVICE_CAM,
            fmt=pyvirtualcam.PixelFormat.BGR,
        ) as cam:
            print(f" Camera Device: {cam.device}", flush=True)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((HOST, PORT))
                server_socket.listen()
                print("Waiting for connection...", flush=True)

                conn, addr = server_socket.accept()
                with conn:
                    print(f"Connected! : {addr}", flush=True)

                    data = b""
                    payload_size = struct.calcsize("!I")

                    while True:
                        while len(data) < payload_size:
                            packet = conn.recv(4096)
                            if not packet:
                                raise ConnectionError("Client Disconnected")
                            data += packet

                        packed_msg_size = data[:payload_size]
                        data = data[payload_size:]
                        msg_size = struct.unpack("!I", packed_msg_size)[0]

                        while len(data) < msg_size:
                            packet = conn.recv(4096)
                            if not packet:
                                raise ConnectionError("Client Disconnected")
                            data += packet

                        frame_data = data[:msg_size]
                        data = data[msg_size:]

                        frame = cv2.imdecode(
                            np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR
                        )

                        if frame is not None:
                            if frame.shape[1] != WIDTH or frame.shape[0] != HEIGHT:
                                frame = cv2.resize(frame, (WIDTH, HEIGHT))

                            cam.send(frame)
                            cam.sleep_until_next_frame()
                        else:
                            print("Error in receiving frame", flush=True)

    except struct.error as err:
        print(f"Struct Error: {err}", flush=True)
    except Exception as err:
        print(f"Loop Error: {err}", flush=True)

    print("Server ended.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal Error in Server: {e}", flush=True)
