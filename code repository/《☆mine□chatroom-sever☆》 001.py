import socket
import threading

# 클라이언트 연결을 처리하는 함수
def handle_client(conn, addr):
    print(f"[접속] {addr} 연결됨")
    try:
        while True:
            msg = conn.recv(1024).decode('utf-8')
            if not msg or msg.lower() == 'exit':
                print(f"[종료] {addr} 연결 종료")
                break
            print(f"[{addr}] {msg}")
            conn.sendall(f"{msg}".encode('utf-8'))
    except Exception as e:
        print(f"[에러] {addr} : {e}")
    finally:
        conn.close()

def start_server(host='127.0.0.1', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"[서버 시작] {host}:{port} 에서 대기 중...")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[서버 종료]")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
