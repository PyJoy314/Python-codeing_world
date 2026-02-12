A = input().strip()
A = list(A)
M = 0
while True:
    M += 6
    print((f'[:[^].[-]:]~[:[{A}].[{M}₩]:]' * 4624).join(A))