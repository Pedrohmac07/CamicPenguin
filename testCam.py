import pyvirtualcam
import numpy as np
import random

with pyvirtualcam.Camera(width=1280, height=720, device="/dev/video0", fps=30) as cam:
    print(f"Usando dispositivo: {cam.device}")

    frame = np.zeros((cam.height, cam.width, 3), dtype=np.uint8)
    frame[:, :, 0] = 255

    print("Está funcionando!")

    while True:
        cam.send(frame)
        cam.sleep_until_next_frame()
