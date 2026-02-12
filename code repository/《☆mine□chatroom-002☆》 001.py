def Chat():
    MCAT = []
    C = {}
    CM = 0
    M = 0
    Nick = input("닉네임을 임력 : ")
    print(Nick,"님, 제 채팅방에 오신 걸 환영합니다~")
    print()

    while True:
        MCAT = input("txt를 입력(나가려면 'exit를 임력) : ")
        C[CM] = MCAT
        M += len(MCAT)
        if MCAT.lower() == 'exit':
            break
        print(Nick,M,'₩/$ : ',C[CM])
        CM += 1

Chat()
