
import socket
import threading
MePy = 0

# 서버 설정
HOST = '127.0.0.1'  # 서버 주소
PORT = 64624        # 서버 포트 번호

# 메시지 수신 함수
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(["[:[^].[-]:]",[MePy,"₩"], message])
        except:
            print("서버 연결이 끊어졌습니다.")
            client_socket.close()
            break

# 클라이언트 시작
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# 수신 스레드 시작
threading.Thread(target=receive_messages, args=(client,)).start()

# 메시지 전송
while True:
    message = input()
    MePy += len(message)
    client.send(message.encode('utf-8'))