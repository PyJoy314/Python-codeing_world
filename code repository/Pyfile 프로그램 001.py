import os
import subprocess
import sys

def handle_file():
    """파일 경로를 입력받아 실행하거나 내용을 출력/수정하는 함수"""
    print("--- 파일 관리 프로그램 시작 ---")
    
    while True:
        # 파일 경로 입력 루틴 (오류 처리 포함)
        file_path = input("\n[1] 파일 경로를 입력하세요 (예: C:/my_file.py 또는 ./my_script.py): ").strip()
        
        # 'exit' 입력 시 프로그램 종료
        if file_path.lower() == 'exit':
            print("프로그램을 종료합니다.")
            break
            
        # 1. 파일 경로 유효성 및 존재 여부 확인
        if not file_path:
            print("❌ 오류: 파일 경로를 입력하지 않았습니다. 다시 입력해주세요.")
            continue
            
        if not os.path.exists(file_path):
            print(f"❌ 오류: '{file_path}' 경로에 파일이 존재하지 않습니다. 경로/파일명이 정확한지 확인해 주세요.")
            # 팁 제공: Pydroid3 사용자에게 유용한 팁
            if 'storage/emulated' in file_path:
                 print("💡 팁: Android(Pydroid3 등)에서는 경로가 정확해도 권한 문제로 접근이 안될 수 있습니다. 파일을 작업 폴더로 복사해 보세요.")
            continue
            
        # 2. 파일 처리 옵션 선택
        print(f"\n✅ 파일 확인됨: {os.path.abspath(file_path)}")
        
        while True:
            action = input(
                "[2] 원하는 작업을 선택하세요 (S: 실행, R: 읽기/출력, E: 수정, C: 경로 재입력): "
            ).strip().upper()
            
            if action == 'C':
                break # 상위 while 루프로 돌아가 경로를 재입력
                
            elif action == 'S':
                # 3. 파일 실행 (파이썬 파일에 주로 사용)
                try:
                    print(f"\n🚀 파일 실행 시작: {file_path}")
                    # subprocess.run을 사용하여 외부 프로그램처럼 실행
                    # sys.executable은 현재 파이썬 인터프리터를 사용
                    if file_path.lower().endswith(('.py', '.pyw')):
                        result = subprocess.run([sys.executable, file_path], check=True, capture_output=False, text=True)
                    else:
                        # 파이썬 파일이 아니면 기본 시스템 프로그램으로 열기 시도
                        os.startfile(file_path) if os.name == 'nt' else subprocess.run(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path], check=True)
                    print(f"\n✅ 파일 실행 완료 (종료 코드: {result.returncode if 'result' in locals() else 'N/A'})")
                except subprocess.CalledProcessError as e:
                    print(f"\n❌ 실행 오류 발생: \n{e.stderr}")
                except FileNotFoundError:
                    print(f"\n❌ 실행 오류: 파일 실행기를 찾을 수 없습니다.")
                except Exception as e:
                    print(f"\n❌ 실행 중 알 수 없는 오류 발생: {e}")
                break
                
            elif action == 'R':
                # 4. 파일 내용 읽기 및 출력
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contents = f.read()
                        print("\n================== 파일 내용 시작 ==================")
                        print(contents)
                        print("================== 파일 내용 끝 ==================")
                except UnicodeDecodeError:
                    print("❌ 오류: 파일을 'utf-8'로 읽을 수 없습니다. 다른 인코딩일 수 있습니다 (예: 'cp949').")
                except Exception as e:
                    print(f"❌ 읽기 오류 발생: {e}")
                break
                
            elif action == 'E':
                # 5. 파일 수정 (텍스트 에디터 실행)
                try:
                    # 'notepad' (윈도우), 'nano'/'vi' (리눅스/맥) 또는 기본 시스템 에디터 실행
                    editor = os.environ.get('EDITOR') or ('notepad' if os.name == 'nt' else ('code' if os.path.exists('/usr/bin/code') else 'nano'))
                    
                    print(f"\n🛠️ {editor}를 사용하여 파일 수정 시작: {file_path}")
                    # 파일 수정을 위해 에디터 실행
                    subprocess.run([editor, file_path])
                    
                    print("\n✅ 파일 수정 완료 (에디터 종료됨)")
                except FileNotFoundError:
                    print(f"\n❌ 오류: 텍스트 에디터 '{editor}'를 찾을 수 없습니다. 수동으로 파일을 여세요.")
                except Exception as e:
                    print(f"\n❌ 수정 중 알 수 없는 오류 발생: {e}")
                break
            
            else:
                print("❌ 오류: 올바른 작업을 선택하세요 (S, R, E, C).")

if __name__ == "__main__":
    handle_file()

#/storage/emulated/0/Android/data/ru.iiec.pydroid3/files/《☆나만의□채팅방-002☆》.py
