import socket

# 서버 설정
HOST = '127.0.0.1'  # 로컬호스트 주소 (동일 컴퓨터 내 통신)
PORT = 65432        # 사용할 포트 번호 (1024 이상의 사용되지 않는 포트 권장)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"서버가 {HOST}:{PORT} 에서 대기 중입니다.")
    conn, addr = s.accept() # 클라이언트 연결 수락
    with conn:
        print(f"연결됨: {addr}")
        while True:
            data = conn.recv(1024) # 데이터 수신 (최대 1024 바이트)
            if not data:
                break
            print(f"수신된 데이터: {data.decode('utf-8')}")
            conn.sendall(data) # 데이터 그대로 회신
