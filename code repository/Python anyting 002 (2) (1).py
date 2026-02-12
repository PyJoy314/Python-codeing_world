
import socket
import threading

# 서버 설정
HOST = '127.0.0.1'  # 로컬호스트
PORT = 64624        # 사용할 포트 번호

# 클라이언트 목록 저장
clients = []

# 메시지 브로드캐스트 함수
def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                clients.remove(client)

# 클라이언트 처리 함수
def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            broadcast(message, client_socket)
        except:
            clients.remove(client_socket)
            client_socket.close()
            break

# 서버 시작
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"서버가 {HOST}:{PORT}에서 실행 중입니다...")

while True:
    client_socket, client_address = server.accept()
    print(f"{client_address} 연결됨.")
    clients.append(client_socket)
    threading.Thread(target=handle_client, args=(client_socket,)).start()