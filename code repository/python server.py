# ==============================================================================
# 💻 server.py: Gemini 멀티버스 채팅방 서버 로직
# ==============================================================================
import sqlite3
import random
import os
import threading
import sys
import json
import time
import subprocess

# 1. 필수 라이브러리 설치 (Flask, SocketIO, Eventlet)
try:
    print("🚀 필수 라이브러리 설치 중...")
    # -q 옵션을 사용하여 출력 최소화
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "Flask-SocketIO", "eventlet", "-q"])
    print("✅ 라이브러리 설치 완료.")
except Exception as e:
    print(f"❌ 라이브러리 설치 오류: {e}")
    sys.exit(1) # 설치 실패 시 프로그램 종료

# ⭐ Flask, SocketIO, Eventlet (비동기 처리) 모듈 임포트
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# --- 1. 환경 설정 ---
ADMIN_NICKNAME = "Admin"
ADMIN_PASSWORD = "123" # 보안을 위해 실제 사용 시 복잡하게 설정해야 합니다!
POINT_PER_MESSAGE = 1   # 메시지당 적립 ₩
DB_FILE = "chat_data.db"
JSON_FILE = "user_data.json" # 마이그레이션용 레거시 파일
DB_LOCK = threading.Lock() # 데이터베이스 접근 스레드 안전성 락
ITEMS = {
    "닉네임변경권": {"price": 1000}
}
# 뇌절 방지 필터
MAX_MSG_LENGTH = 500
MAX_NEWLINES = 10

# --- 2. 전역 변수 ---
# {socket_id: nickname}
clients = {}
# {nickname: socket_id}
nicknames = {}
clients_lock = threading.Lock()


# --- 3. 유틸리티 함수 (DB 처리) ---

def init_db():
    """DB 초기화 및 테이블 생성, JSON 파일 데이터 마이그레이션 처리"""
    print("🛠️ 데이터베이스 초기화 및 마이그레이션 시작...")
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                nickname TEXT PRIMARY KEY,
                money INTEGER,
                is_admin INTEGER,
                has_ticket INTEGER
            )
        """)
        conn.commit()

        # 관리자 계정 생성 (없을 경우)
        cursor.execute("SELECT nickname FROM users WHERE nickname = ?", (ADMIN_NICKNAME,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (ADMIN_NICKNAME, 1000000, 1, 0))
            conn.commit()
            print(f"✅ 관리자 계정 '{ADMIN_NICKNAME}' 생성 완료.")

        # JSON 파일 -> DB 마이그레이션 (레거시 지원)
        if os.path.exists(JSON_FILE):
            print(f"⚠️ 레거시 JSON 파일({JSON_FILE}) 발견! DB로 마이그레이션 중...")
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    legacy_users = json.load(f)

                for nick, data in legacy_users.items():
                    # DB에 이미 존재하는 닉네임은 건너뜕니다.
                    cursor.execute("SELECT nickname FROM users WHERE nickname = ?", (nick,))
                    if cursor.fetchone() is None:
                        # is_admin, has_ticket은 기본적으로 False(0)로 설정
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                                       (nick, data.get('money', 0), int(data.get('is_admin', False)), int(data.get('has_nickname_change_ticket', False))))
                conn.commit()
                # 마이그레이션 후 레거시 파일 삭제를 원하면 아래 주석 해제
                # os.remove(JSON_FILE)
                print("✅ 마이그레이션 완료.")
            except Exception as e:
                print(f"❌ JSON 마이그레이션 중 오류 발생: {e}")

        conn.close()
    print("✅ 데이터베이스 준비 완료.")

def get_user_data(nickname):
    """특정 닉네임의 사용자 데이터를 DB에서 읽어옵니다."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, money, is_admin, has_ticket FROM users WHERE nickname = ?", (nickname,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'nickname': row[0],
                'money': row[1],
                'is_admin': bool(row[2]),
                'has_ticket': bool(row[3])
            }
        return None

def update_user_data(nickname, money=None, is_admin=None, has_ticket=None, old_nickname=None):
    """사용자 데이터를 DB에 업데이트하거나, 닉네임 변경 시 레코드를 업데이트합니다."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if old_nickname and nickname != old_nickname:
            # 닉네임 변경 처리: 기존 레코드를 삭제하고 새 닉네임으로 삽입
            user_data = get_user_data(old_nickname)
            if user_data:
                # 기존 레코드 삭제
                cursor.execute("DELETE FROM users WHERE nickname = ?", (old_nickname,))

                # 새 레코드 삽입: 변경되지 않은 값은 기존 값 유지
                new_money = money if money is not None else user_data['money']
                new_is_admin = is_admin if is_admin is not None else user_data['is_admin']
                new_has_ticket = has_ticket if has_ticket is not None else user_data['has_ticket']

                cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                               (nickname, new_money, int(new_is_admin), int(new_has_ticket)))
        else:
            # 일반 업데이트
            data = get_user_data(nickname)
            if data:
                # 변경되지 않은 값은 기존 값 유지
                new_money = money if money is not None else data['money']
                new_is_admin = is_admin if is_admin is not None else data['is_admin']
                new_has_ticket = has_ticket if has_ticket is not None else data['has_ticket']

                cursor.execute("""
                    UPDATE users
                    SET money = ?, is_admin = ?, has_ticket = ?
                    WHERE nickname = ?
                """, (new_money, int(new_is_admin), int(new_has_ticket), nickname))
            else:
                # 새 사용자 생성
                cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                               (nickname, money if money is not None else 0, int(is_admin if is_admin is not None else False), int(has_ticket if has_ticket is not None else False)))

        conn.commit()
        conn.close()

def get_top_users(limit=10):
    """₩ 잔액이 높은 사용자 순위표를 가져옵니다."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, money FROM users ORDER BY money DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

def get_all_users_data():
    """모든 사용자의 데이터를 가져옵니다."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, money, is_admin, has_ticket FROM users")
        rows = cursor.fetchall()
        conn.close()

        users_data = {}
        for row in rows:
            users_data[row[0]] = {
                'nickname': row[0],
                'money': row[1],
                'is_admin': bool(row[2]),
                'has_ticket': bool(row[3])
            }
        return users_data

# --- 4. 명령어 처리 함수 ---

def process_command(sid, client_nickname, message):
    """클라이언트가 보낸 명령어를 처리하는 함수"""

    parts = message.split(' ')
    command = parts[0]
    user_data = get_user_data(client_nickname)

    # 1. !잔액
    if command == '!잔액':
        money = user_data['money']
        emit('command_result', f"💰 현재 잔액: {money}₩\n📜 보유 아이템: {'닉네임변경권' if user_data['has_ticket'] else '없음'}", room=sid)
        return True

    # 2. !상점
    elif command == '!상점':
        store_list = "\n--- 상점 목록 ---\n"
        for item, data in ITEMS.items():
            store_list += f"- {item}: {data['price']}₩\n"
        store_list += "----------------\n"
        store_list += "구매: !구매 [아이템 이름]"
        emit('command_result', store_list, room=sid)
        return True

    # 3. !구매 [아이템]
    elif command == '!구매':
        if len(parts) < 2:
            emit('command_result', "⚠️ 사용법: !구매 [아이템 이름]", room=sid)
            return True
        item_name = parts[1]

        if item_name == '닉네임변경권':
            if user_data['has_ticket']:
                emit('command_result', "❌ 이미 닉네임 변경권을 보유하고 있습니다.", room=sid)
                return True

            price = ITEMS['닉네임변경권']['price']
            if user_data['money'] >= price:
                update_user_data(client_nickname, money=user_data['money'] - price, has_ticket=True)
                emit('command_result', f"✅ 닉네임변경권을 {price}₩에 구매했습니다. (!닉네임 [새닉]으로 사용)", room=sid)
            else:
                emit('command_result', f"❌ 잔액이 부족합니다. (현재 {user_data['money']}₩ / 필요 {price}₩)", room=sid)
        else:
            emit('command_result', f"❌ 알 수 없는 아이템입니다: {item_name}", room=sid)
        return True

    # 4. !닉네임 [새닉네임]
    elif command == '!닉네임':
        if len(parts) < 2:
            emit('command_result', "⚠️ 사용법: !닉네임 [새 닉네임]", room=sid)
            return True

        if not user_data['has_ticket']:
            emit('command_result', "❌ 닉네임 변경권이 없습니다. (!상점 에서 구매하세요.)", room=sid)
            return True

        new_nickname = parts[1].strip()
        if not new_nickname:
            emit('command_result', "❌ 새 닉네임을 입력해야 합니다.", room=sid)
            return True

        if new_nickname in nicknames or get_user_data(new_nickname):
            emit('command_result', f"❌ '{new_nickname}'은(는) 이미 사용 중인 닉네임입니다.", room=sid)
            return True

        old_nickname = client_nickname

        # DB 업데이트 및 닉네임 변경권 사용 처리
        update_user_data(new_nickname, has_ticket=False, old_nickname=old_nickname)

        # 서버 전역 변수 업데이트
        with clients_lock:
            clients[sid] = new_nickname
            if old_nickname in nicknames:
                 del nicknames[old_nickname]
            nicknames[new_nickname] = sid

        # 클라이언트에게 변경 알림 (자신, 다른 유저)
        emit('update_nickname', {'old_nickname': old_nickname, 'new_nickname': new_nickname}, room=sid)
        emit('status_message', f"✅ [시스템] '{old_nickname}'님께서 닉네임을 '{new_nickname}'으로 변경했습니다.", broadcast=True, include_self=False)
        emit('command_result', f"✅ 닉네임 변경권이 사용되었으며, 닉네임이 '{new_nickname}'으로 변경되었습니다.", room=sid)

        return True

    # 5. !랭킹
    elif command == '!랭킹':
        top_users = get_top_users()
        ranking_str = "\n🏆 ₩ 포인트 랭킹 TOP 10 🏆\n"

        for i, (nick, money) in enumerate(top_users):
            ranking_str += f"{i+1}. {nick} ({money}₩)\n"

        ranking_str += "-------------------------"
        emit('command_result', ranking_str, room=sid)
        return True

    # 6. !지급 [닉네임] [금액] (관리자 전용)
    elif command == '!지급':
        if not user_data['is_admin']:
            emit('command_result', "❌ 관리자만 사용할 수 있는 명령어입니다.", room=sid)
            return True

        if len(parts) < 3 or not parts[2].isdigit():
            emit('command_result', "⚠️ 사용법: !지급 [닉네임] [금액]", room=sid)
            return True

        target_nick = parts[1]
        amount = int(parts[2])

        target_data = get_user_data(target_nick)

        if target_data:
            new_money = target_data['money'] + amount
            update_user_data(target_nick, money=new_money)

            # 모든 클라이언트에게 알림
            message = f"📢 [시스템] 관리자 '{client_nickname}'님께서 '{target_nick}'님에게 {amount}₩을(를) 지급했습니다. (잔액: {new_money}₩)"
            emit('status_message', message, broadcast=True)
        else:
            emit('command_result', f"❌ '{target_nick}' 닉네임을 가진 사용자가 없습니다.", room=sid)
        return True

    # --- 멀티버스 가상 체험 명령어 ---

    # 7. !뇌절 (대량 출력 시뮬레이션)
    elif command == '!뇌절':
        message = "[:[^].[-]:]~[:[파이썬].[6₩]:]" * 50
        emit('command_result', f"🤯 뇌절 모드 실행: (대량 출력 시뮬레이션)\n{message}...", room=sid)
        return True

    # 8. !분석 (Pandas 데이터 분석 시뮬레이션)
    elif command == '!분석':
        all_users = get_all_users_data()
        if not all_users:
            emit('command_result', "⚠️ 현재 사용자 데이터가 없습니다.", room=sid)
            return True

        total_money = sum(data['money'] for data in all_users.values())
        avg_money = total_money / len(all_users)

        result = f"📊 데이터 분석 (Pandas 시뮬레이션)\n"
        result += f"- 전체 사용자 수: {len(all_users)}명\n"
        result += f"- 총 발행 ₩: {total_money}₩\n"
        result += f"- 사용자당 평균 잔액: {int(avg_money)}₩"

        emit('command_result', result, room=sid)
        return True

    # 9. !게임 (주사위 게임 시뮬레이션)
    elif command == '!게임':
        user_roll = random.randint(1, 6)
        gemini_roll = random.randint(1, 6)

        result = f"🎲 주사위 게임 (PyGame 시뮬레이션)\n"
        result += f"- '{client_nickname}'님의 주사위: {user_roll}\n"
        result += f"- Gemini의 주사위: {gemini_roll}\n"

        # 주사위 결과에 따라 ₩ 지급/차감 (잔액 확인 후 진행)
        if user_roll > gemini_roll:
            update_user_data(client_nickname, money=user_data['money'] + 500)
            result += "✅ 승리! 500₩를 획득했습니다!"
        elif user_roll < gemini_roll:
            # 잔액이 300₩ 미만이면 모두 차감 (파산 방지)
            loss = min(300, user_data['money'])
            update_user_data(client_nickname, money=user_data['money'] - loss)
            result += f"❌ 패배... {loss}₩를 잃었습니다."
        else:
            result += "🤝 무승부! 잔액 변동 없음."

        emit('command_result', result, room=sid)
        return True

    # 명령어가 아니면 False 반환
    return False

# --- 5. Flask 및 SocketIO 설정 ---

app = Flask(__name__)
# Colab 환경에서는 'eventlet'을 사용하여 비동기 실행하는 것이 가장 안정적입니다.
socketio = SocketIO(app, async_mode='eventlet')

# 웹 페이지 라우팅
@app.route('/')
def index():
    # 'templates/index.html' 파일을 찾아서 클라이언트에게 제공합니다.
    return render_template('index.html')

# --- 6. SocketIO 이벤트 핸들러 ---

@socketio.on('set_nickname')
def handle_set_nickname(data):
    """클라이언트가 닉네임을 설정할 때 처리"""
    sid = request.sid
    nickname = data['nickname'].strip()

    with clients_lock:
        # 1. 중복 확인
        if nickname in nicknames:
            if sid in clients and clients[sid] == nickname:
                 # 이미 같은 닉네임으로 접속했으면 OK
                emit('nickname_ok', {'nickname': nickname})
                return
            emit('nickname_error', {'message': f"❌ '{nickname}'은(는) 이미 사용 중입니다."}, room=sid)
            return

        # 2. 로그인 처리 (이전 연결 제거 및 기존 닉네임 해제)
        if sid in clients and clients[sid] in nicknames:
            old_nickname = clients[sid]
            del nicknames[old_nickname]
            emit('status_message', f"[시스템] '{old_nickname}'님이 접속을 종료했습니다.", broadcast=True, include_self=False)


        # 3. 새 닉네임 등록
        clients[sid] = nickname
        nicknames[nickname] = sid

    # 4. 사용자 데이터 로드/생성
    user_data = get_user_data(nickname)
    if user_data is None:
        # DB에 새 사용자 생성 (초기 0₩)
        update_user_data(nickname, money=0, is_admin=False, has_ticket=False)

    # 5. 접속 완료 알림
    emit('nickname_ok', {'nickname': nickname})
    emit('status_message', f"🌟 [시스템] '{nickname}'님이 접속했습니다. (현재 {len(nicknames)}명)", broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    """클라이언트가 메시지를 보낼 때 처리"""
    sid = request.sid
    if sid not in clients:
        # 닉네임 설정이 안된 경우 무시
        return

    client_nickname = clients[sid]
    message = data['message'].strip()

    # 메시지 필터링 (뇌절 방지)
    if not message:
        return
    if len(message) > MAX_MSG_LENGTH or message.count('\n') > MAX_NEWLINES:
        emit('command_result', "❌ 메시지 길이 또는 줄바꿈 제한을 초과했습니다.", room=sid)
        return

    # 1. 명령어 처리
    if message.startswith('!'):
        if process_command(sid, client_nickname, message):
            return # 명령어가 성공적으로 처리되었으면 일반 메시지 전송은 건너뜀

    # 2. 일반 메시지 처리
    # 포인트 적립 (관리자 제외)
    user_data = get_user_data(client_nickname)
    if user_data and not user_data['is_admin']:
        update_user_data(client_nickname, money=user_data['money'] + POINT_PER_MESSAGE)

    # 모든 클라이언트에게 메시지 전송
    emit('receive_message', {'nickname': client_nickname, 'message': message}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트가 연결을 끊을 때 처리"""
    sid = request.sid
    with clients_lock:
        if sid in clients:
            nickname = clients[sid]
            del clients[sid]
            if nickname in nicknames:
                 del nicknames[nickname]

            emit('status_message', f"👋 [시스템] '{nickname}'님이 접속을 종료했습니다. (현재 {len(nicknames)}명)", broadcast=True)

# --- 7. 서버 실행 ---
if __name__ == '__main__':
    # 템플릿 폴더가 없으면 생성 (Colab/단일 파일 실행 환경 대비)
    os.makedirs('templates', exist_ok=True)

    # DB 초기화 및 관리자 계정 설정
    init_db()

    print("🌐 서버 시작! 웹 브라우저로 접속하세요.")
    # Colab 환경에서는 127.0.0.1 대신 '0.0.0.0'을 사용해야 외부에서 접근 가능합니다.
    socketio.run(app, host='0.0.0.0', port=5000)
