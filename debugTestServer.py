import socket
import struct
import time
import cv2
import numpy as np
import os
import sys
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")  # Teste local
try:
    PORT = int(os.getenv("PORT", "5000"))
except:
    PORT = 5000

print(f"Tentando conectar em {HOST}:{PORT}...", flush=True)

# Cria imagem de teste (Ruído aleatório para garantir que muda)
img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

# Codifica
ret, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
data_bytes = buffer.tobytes()
size = len(data_bytes)

print(f"Tamanho do pacote: {size} bytes", flush=True)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        print("✅ Conectado ao Servidor! Enviando dados...", flush=True)

        while True:
            # '!I' garante compatibilidade com o servidor novo
            header = struct.pack("!I", size)

            try:
                client_socket.sendall(header + data_bytes)
                # print(".", end="", flush=True) # Imprime um ponto a cada envio
                time.sleep(1 / 30)
            except BrokenPipeError:
                print(
                    "\n❌ ERRO: Broken Pipe. O servidor fechou a conexão.", flush=True
                )
                break

except ConnectionRefusedError:
    print("❌ ERRO: Não foi possível conectar. O servidor está rodando?", flush=True)
except Exception as e:
    print(f"\n❌ ERRO: {e}", flush=True)
