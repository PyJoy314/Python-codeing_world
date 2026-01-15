import socketio
import serial
import time

SERVER_URL = "https://crispiest-crunchingly-dani.ngrok-free.dev"
SERIAL_PORT = "COM6"
BAUDRATE = 115200

# ======================
# micro:bit 연결
# ======================
ser = None

try:
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    time.sleep(2)
    print("✅ micro:bit 연결 성공")
except Exception as e:
    print("❌ micro:bit 연결 실패:", e)


# ======================
# Socket.IO 클라이언트
# ======================
socketio= socketio.Client()

@socketio.event
def connect():
    print("🌐 서버 연결 성공")

@socketio.event
def disconnect():
    print("⚠️ 서버 연결 끊김")

@socketio.on("microbit_event")
def on_microbit_event(data):
    if not ser:
        return

    mtype = data.get("type")
    payload = data.get("payload", "")

    if mtype == "IMG":
        ser.write(f"IMG:{payload}\n".encode())

    elif mtype == "TEXT":
        ser.write(f"TEXT:{payload}\n".encode())

    elif mtype == "BEEP":
        ser.write(b"BEEP\n")

    print("➡ micro:bit 전송:", mtype, payload)

print("🔌 서버 연결 중...")
socketio.connect(SERVER_URL)

while True:
    time.sleep(1)
