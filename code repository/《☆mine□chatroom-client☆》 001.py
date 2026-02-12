import socket

def start_client(host='127.0.0.1', port=5000, M=0):
    nickname = input("닉네임을 입력: ").strip()
    print(f"어서오십시오, {nickname}님! 채팅방에 오신 것을 환영합니다~\n")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        while True:
            msg = input("채팅 입력(나가려면 'exit'): ").strip()
            M += len(msg)
            if not msg:
                continue
            client_socket.sendall(f"{nickname} {M}₩/$ : {msg}".encode('utf-8'))
            if msg.lower() == 'exit':
                break
            response = client_socket.recv(1024).decode('utf-8')
            print(response)
    except ConnectionRefusedError:
        print("[에러] 서버에 연결할 수 없습니다.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()


