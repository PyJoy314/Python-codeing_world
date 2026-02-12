MCAT = []
MePy = 0
print("어서오십시오 저의 체팅방에 온 걸 환영합니다~")

while True:
    MCAT = input("체팅 내용 임력(나가려면 'exit'를 임력)")
    if MCAT.lower() == 'exit':
        break
    MePy += len(MCAT)
    print("[:[^].[-]:]", [MePy,"₩"], " : ", MCAT)