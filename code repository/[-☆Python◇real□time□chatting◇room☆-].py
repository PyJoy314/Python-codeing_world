# ==============================================================================
# 🛠️ 1. 환경 설정 및 파일 생성
# ==============================================================================
import os
import sys
import subprocess

# 1. 필수 라이브러리 설치 (Flask, SocketIO)
try:
    print("🚀 필수 라이브러리 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "Flask-SocketIO", "eventlet", "-q"])
    print("✅ 라이브러리 설치 완료.")
except Exception as e:
    print(f"❌ 라이브러리 설치 오류: {e}")

# 2. 'templates' 폴더 생성
os.makedirs('templates', exist_ok=True)

print("✅ 'templates' 폴더 생성 완료.")

# 3. 'templates/index.html' 파일에 웹 클라이언트 코드를 작성합니다.
# r"""을 사용하여 들여쓰기 오류 및 경고를 방지합니다.
html_content = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Gemini 멀티버스 채팅방 (Web)</title>
    <style>
        /* CSS 스타일 */
        body { font-family: sans-serif; margin: 0; padding: 20px; background: #2c2f33; color: #fff; }
        #chat-container { max-width: 800px; margin: 0 auto; background: #36393f; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); }
        #chat-window { height: 500px; overflow-y: scroll; padding: 15px; border-bottom: 1px solid #4f545c; }
        .message { margin-bottom: 10px; line-height: 1.4; }
        .nickname { font-weight: bold; color: #7289da; margin-right: 8px; }
        .system { color: #ffb84d; font-style: italic; border-left: 3px solid #ffb84d; padding-left: 10px; }
        .command { color: #f04747; border-left: 3px solid #f04747; padding-left: 10px; white-space: pre-wrap; }

        #nickname-screen { text-align: center; padding: 100px 20px; }
        #nickname-form input, #input-form input { padding: 12px; border: none; border-radius: 4px; background: #40444b; color: #dcddde; }
        #nickname-form button, #input-form button { padding: 12px 20px; background: #43b581; color: white; border: none; border-radius: 4px; cursor: pointer; transition: background 0.3s; }
        #nickname-form button:hover, #input-form button:hover { background: #3aa673; }

        #input-form { display: flex; padding: 15px; }
        #message-input { flex-grow: 1; margin-right: 10px; }
        #current-nickname { color: #43b581; }
        .info-text { color: #b9bbbe; font-size: 0.9em; padding: 0 15px 15px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <div id="chat-container">

        <div id="nickname-screen">
            <h1>✨ Gemini 멀티버스 채팅방 접속 ✨</h1>
            <form id="nickname-form">
                <input type="text" id="nickname-input" placeholder="닉네임을 입력하세요 (필수)">
                <button type="submit">접속</button>
                <div id="nickname-error" style="color: #f04747; margin-top: 15px;"></div>
            </form>
        </div>

        <div id="chat-screen" style="display: none;">
            <div style="padding: 15px 15px 5px 15px; border-bottom: 1px solid #4f545c;">
                <h3 style="margin: 0;">채팅방 - 현재 접속: <span id="current-nickname"></span></h3>
            </div>
            <div id="chat-window">
                </div>

            <form id="input-form">
                <input type="text" id="message-input" autocomplete="off" placeholder="메시지 또는 !명령어를 입력하세요...">
                <button type="submit">전송</button>
            </form>
            <div class="info-text">
                명령어: !잔액, !상점, !구매 [아이템], !닉네임 [새닉], !랭킹, !지급 [닉] [금액] (관리자 전용), !뇌절, !분석, !게임
            </div>
        </div>

    </div>

    <script>
        // 서버 주소 설정 (Colab에서는 127.0.0.1 대신 현재 호스트를 사용)
        const socket = io(); // io()만 사용하면 현재 페이지의 호스트와 포트를 자동으로 사용합니다.
        let currentNickname = '';

        // 1. 닉네임 설정 처리
        document.getElementById('nickname-form').onsubmit = function(e) {
            e.preventDefault();
            const nickname = document.getElementById('nickname-input').value.trim();
            document.getElementById('nickname-error').innerText = '';
            if (nickname) {
                socket.emit('set_nickname', { nickname: nickname });
            }
        };

        socket.on('nickname_ok', function(data) {
            currentNickname = data.nickname;
            document.getElementById('current-nickname').innerText = currentNickname;
            document.getElementById('nickname-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'block';
            document.getElementById('message-input').focus();
        });

        socket.on('nickname_error', function(data) {
            document.getElementById('nickname-error').innerText = data.message;
        });

        // 2. 메시지 전송 처리
        document.getElementById('input-form').onsubmit = function(e) {
            e.preventDefault();
            const input = document.getElementById('message-input');
            const message = input.value;
            if (message) {
                socket.emit('send_message', { message: message });
                input.value = '';
            }
        };

        // 3. 메시지 수신 처리 (일반 메시지)
        socket.on('receive_message', function(data) {
            appendMessage(`<span class="nickname">[${data.nickname}]</span>: ${data.message}`, 'general');
        });

        // 4. 시스템/상태 메시지 수신 처리
        socket.on('status_message', function(message) {
            appendMessage(message, 'system');
        });

        // 5. 명령어 결과 수신 처리 (!잔액, !랭킹 등 본인에게만 오는 결과)
        socket.on('command_result', function(message) {
            appendMessage(message, 'command');
        });

        // 6. 닉네임 변경 반영
        socket.on('update_nickname', function(data) {
            currentNickname = data.new_nickname;
            document.getElementById('current-nickname').innerText = currentNickname;
        });

        // 7. 메시지를 채팅 창에 추가하는 함수
        function appendMessage(message, type='general') {
            const window = document.getElementById('chat-window');
            const div = document.createElement('div');
            div.className = 'message ' + type;

            if (type === 'general' || type === 'system') {
                div.innerHTML = message.replace(/\n/g, '<br>'); // 줄 바꿈 처리
            } else {
                div.innerText = message;
                // command 메시지는 CSS (white-space: pre-wrap;)를 사용하여 줄바꿈 처리
            }

            window.appendChild(div);
            window.scrollTop = window.scrollHeight;
        }
    </script>
</body>
</html>
"""

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ 'templates/index.html' 파일 생성 및 코드 작성 완료!")

# ==============================================================================
# 💻 2. 최종 웹 서버 코드 (SQLite DB 통합)
# ==============================================================================

import sqlite3
import random
import os
import threading
import sys
import json
import time

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

        # JSON 파일 -> DB 마이그레이션 (레거시 지원)
        if os.path.exists(JSON_FILE):
            print(f"⚠️ 레거시 JSON 파일({JSON_FILE}) 발견! DB로 마이그레이션 중...")
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    legacy_users = json.load(f)

                for nick, data in legacy_users.items():
                    # DB에 이미 존재하는 닉네임은 건너뜁니다.
                    cursor.execute("SELECT nickname FROM users WHERE nickname = ?", (nick,))
                    if cursor.fetchone() is None:
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                                       (nick, data.get('money', 0), data.get('is_admin', False), data.get('has_nickname_change_ticket', False)))
                conn.commit()
                # 마이그레이션 후 레거시 파일 삭제
                # os.remove(JSON_FILE)
                print("✅ 마이그레이션 완료.")
            except Exception as e:
                print(f"❌ JSON 마이그레이션 중 오류 발생: {e}")

        conn.close()

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
                cursor.execute("DELETE FROM users WHERE nickname = ?", (old_nickname,))

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

        new_nickname = parts[1]
        if new_nickname in nicknames or get_user_data(new_nickname):
            emit('command_result', f"❌ '{new_nickname}'은(는) 이미 사용 중인 닉네임입니다.", room=sid)
            return True

        old_nickname = client_nickname

        # DB 업데이트 및 닉네임 변경권 사용 처리
        update_user_data(new_nickname, has_ticket=False, old_nickname=old_nickname)

        # 서버 전역 변수 업데이트
        with clients_lock:
            clients[sid] = new_nickname
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

        if user_roll > gemini_roll:
            update_user_data(client_nickname, money=user_data['money'] + 500)
            result += "✅ 승리! 500₩를 획득했습니다!"
        elif user_roll < gemini_roll:
            update_user_data(client_nickname, money=user_data['money'] - 300)
            result += "❌ 패배... 300₩를 잃었습니다."
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

        # 2. 로그인 처리 (이전 연결 제거)
        if sid in clients:
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
    emit('status_message', f"✨ [시스템] '{nickname}'님이 접속했습니다.", broadcast=True)

    # 관리자 접속 시 비밀번호 안내
    if nickname == ADMIN_NICKNAME:
        emit('command_result', f"✅ [관리자 모드] 활성화. 비밀번호: {ADMIN_PASSWORD} (이 메시지는 본인에게만 보입니다.)", room=sid)

@socketio.on('send_message')
def handle_send_message(data):
    """클라이언트가 메시지를 보낼 때 처리"""
    sid = request.sid
    message = data['message']

    with clients_lock:
        client_nickname = clients.get(sid)

    if not client_nickname:
        # 닉네임 설정 안된 유저는 무시
        return

    # 1. 메시지 필터링 (뇌절 방지)
    if len(message) > MAX_MSG_LENGTH:
        emit('command_result', f"❌ 메시지 길이가 너무 깁니다. ({MAX_MSG_LENGTH}자 제한)", room=sid)
        return
    if message.count('\n') > MAX_NEWLINES:
        emit('command_result', f"❌ 줄 바꿈 횟수가 너무 많습니다. ({MAX_NEWLINES}개 제한)", room=sid)
        return

    # 2. 명령어 처리
    if message.startswith('!'):
        if process_command(sid, client_nickname, message):
            return

    # 3. 일반 메시지 전송
    emit('receive_message', {'nickname': client_nickname, 'message': message}, broadcast=True)

    # 4. ₩ 포인트 적립 (명령어가 아닌 일반 메시지에 한해서)
    user_data = get_user_data(client_nickname)
    if user_data:
        new_money = user_data['money'] + POINT_PER_MESSAGE
        update_user_data(client_nickname, money=new_money)
        # emit('command_result', f"💰 {POINT_PER_MESSAGE}₩ 적립! (잔액: {new_money}₩)", room=sid) # 너무 자주 뜨면 시끄러우니 주석 처리

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결이 끊어질 때 처리"""
    sid = request.sid
    with clients_lock:
        if sid in clients:
            nickname = clients[sid]
            del clients[sid]
            del nicknames[nickname]
            emit('status_message', f"[시스템] '{nickname}'님이 접속을 종료했습니다.", broadcast=True)


# --- 7. 서버 실행 ---
if __name__ == '__main__':
    print(f"\n==============================================")
    print(f"🌟 《Gemini 멀티버스 채팅방》 최종 통합 버전 🌟")
    print(f"==============================================")

    # DB 초기화 및 마이그레이션 실행
    init_db()

    print(f"💾 데이터베이스 파일: {DB_FILE} (영속성 확보)")
    print(f"✨ 관리자 닉네임: '{ADMIN_NICKNAME}' / 비밀번호: '{ADMIN_PASSWORD}'")

    # Colab 환경에서는 host='0.0.0.0'을 사용하고 debug=False, allow_unsafe_werkzeug=True를 설정합니다.
    # eventlet을 사용하면 Flask + SocketIO를 안정적으로 비동기 실행할 수 있습니다.
    try:
        print("\n🚀 웹 서버 (Flask + SocketIO) 시작 중...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n[시스템] 서버 종료 요청을 받았습니다.")
    except Exception as e:
        print(f"\n[시스템] 서버 실행 중 치명적인 오류 발생: {e}")