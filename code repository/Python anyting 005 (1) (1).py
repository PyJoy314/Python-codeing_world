# main.py
import sys

M = []
i = []

def MPER_main():
    # Read everything that comes from stdin.
    # If nothing is piped, fall back to a default string.
    try:
        input_data = sys.stdin.read().strip()
        if input_data:
            M.append(input_data)
        else:
            M.append("default text")
    except:
        M.append("default text")

    length = len(M)

    # The required output format
    for aed in M:
        print("[:[^].[-]:]", length, "$", aed)

for J in i:
    i.append(MPER_main()) # Call the function directly
    print(J)
MPER_main()
