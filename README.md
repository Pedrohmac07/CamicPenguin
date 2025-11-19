# MicevErywhere

High-performance Android-to-Linux Webcam and Microphone bridge using raw TCP Sockets.

## 📖 Overview

MicevErywhere is an open-source engineering solution designed to transform an Android device into a low-latency peripheral (Webcam and Microphone) for Linux systems.

Unlike commercial solutions that rely on heavy proprietary protocols, this project implements a lightweight TCP Socket architecture. It captures raw hardware streams on Android, processes them, and injects them directly into the Linux Kernel via v4l2loopback and PulseAudio/PyAudio, making the device available to any software like Zoom, OBS, Discord, or Chrome.

## Key Features

Real-Time Video: High-throughput video streaming from Android CameraX to Linux V4L2.

Real-Time Audio: 16-bit PCM Mono audio streaming.

Dual Connectivity:

USB Mode: Zero-latency connection using ADB Reverse tunneling.

Wi-Fi Mode: Standard local network connection.

Camera Switching: Support for both front and back cameras.

Linux Native: Acts as a native /dev/video device.

## 🛠️ Architecture

The system follows a strict Client-Server architecture over TCP/IP:

Video Pipeline (Port 5000):

Android: Captures YUV_420_888 frames via CameraX, converts to JPEG, and appends a 4-byte Big Endian header indicating payload size.

Linux: Python server reads the header, buffers the exact payload, decodes via OpenCV, and writes to the virtual video device (/dev/videoX).

Audio Pipeline (Port 5001):

Android: Captures raw PCM audio (16-bit, 44.1kHz).

Linux: Python server receives the stream and writes directly to the system audio output via PyAudio.

Thread Management:

Video and Audio run on separate threads to prevent blocking.

Network operations use Coroutines (Kotlin) to ensure UI responsiveness.

## 💻 Technology Stack

Android (Client)

Kotlin

Jetpack CameraX (ImageAnalysis)

Coroutines (Dispatchers.IO)

Java Sockets (DataOutputStream)

Linux (Server)

Python 3

OpenCV (cv2) - Image Decoding

PyVirtualCam - V4L2 Interfacing

PyAudio - PCM Audio Playback

v4l2loopback - Kernel Module

## ⚙️ Installation

Prerequisites (Arch Linux)

System Dependencies:

sudo pacman -S v4l2loopback-dkms linux-headers portaudio android-tools


Python Dependencies:

pip install opencv-python-headless pyvirtualcam pyaudio numpy python-dotenv


Kernel Module Setup:
Enable the virtual camera device (video20) to prevent conflicts with internal webcams.

sudo modprobe v4l2loopback devices=1 video_nr=20 card_label="Webdroid" exclusive_caps=1


Android Setup

Clone the repository.

Open the android folder in Android Studio.

Build and install the APK on your physical device.

## 🚀 Usage Guide

### 1. Start the Servers

Open two terminal windows:

Terminal 1 (Video):

python cameraServer.py


Terminal 2 (Audio):

python audioServer.py


### 2. Connect the Device

Option A: USB Mode (Recommended for Latency)

Use ADB to create a reverse tunnel. This allows the phone to reach the PC via localhost.

Connect phone via USB (USB Debugging enabled).

Run:

adb reverse tcp:5000 tcp:5000
adb reverse tcp:5001 tcp:5001


In the App, enter IP: 127.0.0.1 and click Connect.

Option B: Wi-Fi Mode

Ensure both devices are on the same network.

Find your PC's local IP (e.g., 192.168.1.15) using ip addr.

In the App, enter the IP and click Connect.

### 3. Verification

Open a browser and test the feed at webcamtests.com. Select Webdroid as your camera.

### 4. Enjoy!

Your microphone and camera is working! Use it on Discord, Zoom, anywhere you need!

## 🤝 Contributing

Contributions are welcome. Please follow the standard fork-and-pull request workflow.

Fork the project.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

## 📄 License

Distributed under the MIT License. See LICENSE for more information.
