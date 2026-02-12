MePy = 0
print("어서오십시오 저의 체팅방에 온 걸 환영합니다~")

import socket

# 서버 설정과 동일하게 지정
HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT)) # 서버에 연결
    print(f"서버 {HOST}:{PORT} 에 연결되었습니다.")
    
    message = input("체팅 내용 임력 : ")
    MePy += len(message)
    s.sendall(message.encode('utf-8')) # 메시지 전송
    print("[:[^].[-]:]", [MePy,"₩"], " : ", message)
    data = s.recv(1024) # 서버로부터 응답 수신
    print(f"서버로부터 수신된 응답: {data.decode('utf-8')}")
