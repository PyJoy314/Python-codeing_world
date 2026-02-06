import sqlite3, os, time, threading, random
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

# --- [설정 및 DB] ---
PORT = 5001
UPLOAD_FOLDER = 'uploads'
DB_FILE = "multiverse_ultimate_empire.sqlite"
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

crypto_prices = {"비트코인": 50000000}
noejul_loops = {}

# Gemini AI 로드
client = None
try:
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key: client = genai.Client(api_key=api_key)
except: pass

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (nickname TEXT PRIMARY KEY, money INTEGER DEFAULT 1000, bank_money INTEGER DEFAULT 0, btc_amount REAL DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, nickname TEXT, msg TEXT, type TEXT, rank TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
init_db()

def get_user(nick):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        u = conn.execute("SELECT * FROM users WHERE nickname = ?", (nick,)).fetchone()
        if not u:
            conn.execute("INSERT INTO users (nickname) VALUES (?)", (nick,))
            u = conn.execute("SELECT * FROM users WHERE nickname = ?", (nick,)).fetchone()
        return dict(u)

def update_db(nick, field, amount):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(f"UPDATE users SET {field} = {field} + ? WHERE nickname = ?", (amount, nick))

def broadcast_news(msg):
    """실시간 제국 속보를 전송합니다."""
    socketio.emit('message', {'msg': f"🚨 [제국 속보] {msg}", 'type': 'system'}, room='main')

# 수정된 배경 엔진 로직
def empire_background_engine():
    global crypto_prices
    while True:
        time.sleep(60)
        try:
            with sqlite3.connect(DB_FILE, timeout=10) as conn: # timeout 추가
                # 1. 비트코인 시세 변동
                change = random.uniform(0.95, 1.05)
                crypto_prices["비트코인"] = int(crypto_prices["비트코인"] * change)
                
                # 2. 은행 이자 '돈 복사' (일괄 업데이트로 속도 향상)
                conn.execute("UPDATE users SET money = money + CAST(bank_money * 0.001 AS INTEGER) WHERE bank_money > 0")
                conn.commit()
                
                # 3. 실시간 전송
                socketio.emit('price_update', {'btc': crypto_prices["비트코인"]}, room='main')
                
                if change > 1.04:
                    broadcast_news(f"📈 비트코인 폭등! 현재가: {crypto_prices['비트코인']:,}₩")
                elif change < 0.96:
                    broadcast_news(f"📉 비트코인 대폭락! 현재가: {crypto_prices['비트코인']:,}₩")
        except Exception as e:
            print(f"Engine Error: {e}")

threading.Thread(target=empire_background_engine, daemon=True).start()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/uploads/<path:filename>')
def download(filename): return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file'); nick = request.form.get('nickname', '익명')
    if file:
        fname = f"{int(time.time())}_{secure_filename(file.filename)}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        file.save(path)
        reward = 10000 + (os.path.getsize(path) // 5)
        update_db(nick, "money", reward)
        if reward >= 50000:
            broadcast_news(f"{nick}님이 귀중한 파일을 공유하여 {reward:,}₩의 거액을 하사받았습니다!")
        f_url = f"{request.host_url.rstrip('/')}/uploads/{fname}"
        msg = f"📁 [파일 공유] {file.filename}\n🔗 다운로드: {f_url}"
        socketio.emit('message', {'nickname': nick, 'msg': msg, 'type': 'chat', 'rank': '시스템', 'reward': f"+{reward:,}₩"}, room='main')
    return '', 204

@socketio.on('join')
def on_join(d):
    join_room('main')
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        for h in reversed(conn.execute("SELECT * FROM chats ORDER BY id DESC LIMIT 100").fetchall()):
            emit('message', {'nickname': h['nickname'], 'msg': h['msg'], 'type': h['type'], 'rank': h['rank']})

@socketio.on('send_msg')
def handle_msg(data):
    # 1. 기본 데이터 추출 및 유저 정보 로드
    nick, raw = data['nickname'], data['msg'].strip()
    if not raw: return
    
    u = get_user(nick)
    
    # 2. 메시지 보상 계산 및 DB 업데이트
    if len(raw) > 500:
        fname = f"msg_{int(time.time())}.txt"
        path = os.path.join(UPLOAD_FOLDER, fname)
        with open(path, "w", encoding="utf-8") as f: f.write(raw)
        reward = len(raw) * 100 
        update_db(nick, "money", reward)
        raw = f"📄 대용량 메시지 감지 (파일 변환)\n🔗 다운로드: {request.host_url.rstrip('/')}/uploads/{fname}"
    else:
        reward = len(raw) * 50
        update_db(nick, "money", reward)

    if reward >= 100000:
        broadcast_news(f"현재 {nick}님이 대용량 메시지 전송으로 {reward:,}₩의 막대한 부를 쌓고 있습니다!")

    # [중요] 보상 수령 후 최신 유저 정보와 자산 다시 계산
    u = get_user(nick)
    btc_v = int(u['btc_amount'] * crypto_prices['비트코인'])
    total = u['money'] + u['bank_money'] + btc_v

    parts = raw.split()
    cmd = parts[0]
    
    # --- 명령어 처리부 ---
    
    if cmd == "!잔액":
        res = f"💰 {nick}님 자산\n💵 현금: {u['money']:,}₩\n🏦 은행: {u['bank_money']:,}₩\n🪙 코인: {btc_v:,}₩\n💳 총액: {total:,}₩"
        emit('message', {'msg': res, 'type': 'system', 'total_asset': total})
    
    elif cmd == "!랭킹":
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            users = conn.execute("SELECT * FROM users").fetchall()
            rank_list = []
            for row in users:
                t = row['money'] + row['bank_money'] + int(row['btc_amount'] * crypto_prices['비트코인'])
                rank_list.append({'nick': row['nickname'], 'total': t})
            rank_list.sort(key=lambda x: x['total'], reverse=True)
            top_msg = "🏆 [제국 자산 랭킹 TOP 5]\n"
            for i, r in enumerate(rank_list[:5], 1):
                medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "🎖️"
                top_msg += f"{medal} {i}위: {r['nick']} ({r['total']:,}₩)\n"
            socketio.emit('message', {'msg': top_msg, 'type': 'system', 'total_asset': total}, room='main')

    elif cmd == "!저금":
        amt = int(parts[1]) if len(parts)>1 else u['money']
        if u['money'] >= amt: 
            update_db(nick, "money", -amt); update_db(nick, "bank_money", amt)
            u = get_user(nick) # 업데이트 후 다시 로드
            total = u['money'] + u['bank_money'] + btc_v
            emit('message', {'msg': f"🏦 {amt:,}₩ 저금됨", 'type': 'system', 'total_asset': total})

    elif cmd == "!출금":
        amt = int(parts[1]) if len(parts)>1 else u['bank_money']
        if u['bank_money'] >= amt: 
            update_db(nick, "bank_money", -amt); update_db(nick, "money", amt)
            u = get_user(nick)
            total = u['money'] + u['bank_money'] + btc_v
            emit('message', {'msg': f"💸 {amt:,}₩ 출금됨", 'type': 'system', 'total_asset': total})

    elif cmd == "!매수" and len(parts)>2:
        amt = int(parts[2])
        if u['money'] >= amt:
            btc_add = amt / crypto_prices['비트코인']
            update_db(nick, "money", -amt); update_db(nick, "btc_amount", btc_add)
            u = get_user(nick)
            total = u['money'] + u['bank_money'] + int(u['btc_amount'] * crypto_prices['비트코인'])
            emit('message', {'msg': f"🪙 비트코인 {btc_add:.8f}개 매수완료", 'type': 'system', 'total_asset': total})
            if amt >= 10000000:
                broadcast_news(f"시장 요동! {nick}님이 비트코인을 {btc_add:.4f}개 쓸어담으며 '큰 손'으로 등극했습니다!")

    elif cmd == "!가위바위보" and len(parts)>2:
        pick, amt = parts[1], int(parts[2])
        if u['money'] >= amt:
            bot = random.choice(["가위", "바위", "보"])
            if pick == bot: res = "무승부"
            elif (pick=="가위" and bot=="보") or (pick=="바위" and bot=="가위") or (pick=="보" and bot=="바위"):
                update_db(nick, "money", amt); res = f"승리! (+{amt:,}₩)"
            else: update_db(nick, "money", -amt); res = f"패배... (-{amt:,}₩)"
            u = get_user(nick)
            total = u['money'] + u['bank_money'] + int(u['btc_amount'] * crypto_prices['비트코인'])
            emit('message', {'msg': f"🎮 {pick} vs {bot} -> {res}", 'type': 'system', 'total_asset': total})

    elif cmd == "!무한뇌절":
        if noejul_loops.get(nick): return
        noejul_loops[nick] = True
        def task():
            while noejul_loops.get(nick):
                update_db(nick, "money", 5000)
                socketio.emit('message', {'nickname': nick, 'msg': "🌀 뇌절 적립중...", 'type': 'noejul'}, room='main')
                if random.random() < 0.1:
                    broadcast_news(f"{nick}님이 멈추지 않는 '무한 뇌절'로 시장 경제를 뒤흔들고 있습니다!")
                time.sleep(2)
        threading.Thread(target=task, daemon=True).start()

    elif cmd in ["!뇌절정지", "!뇌절중단"]: noejul_loops[nick] = False

    elif cmd == "!gemini":
        prompt = " ".join(parts[1:])
        if not prompt:
            emit('message', {'msg': "🤖 질문을 입력해주세요!", 'type': 'system', 'total_asset': total})
        elif client is None:
            emit('message', {'msg': "⚠️ Gemini API가 연결되지 않았습니다.", 'type': 'system', 'total_asset': total})
        else:
            try:
                res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                socketio.emit('message', {
                    'nickname': '🤖 Gemini AI', 
                    'msg': res.text, 
                    'type': 'bot', 
                    'rank': '황실 책사'
                }, room='main')
            except Exception as e:
                socketio.emit('message', {'msg': f"⚠️ Gemini 오류: {str(e)}", 'type': 'system'}, room='main')

    elif cmd == "!명령어":
        emit('message', {'msg': "!잔액, !랭킹, !저금 [금액], !출금 [금액], !가위바위보 [패] [금액], !매수 비트코인 [금액], !무한뇌절, !뇌절중단, !gemini [질문]", 'type': 'system', 'total_asset': total})

    # 4. 일반 채팅 메시지 처리 (중복 전송 버그 수정됨)
    else:
        if total >= 200000000: rank = "멀티버스 지배자"
        elif total >= 10000000: rank = "초월자"
        else: rank = "평민"
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO chats (nickname, msg, type, rank) VALUES (?, ?, ?, ?)", (nick, raw, 'chat', rank))
        
        # [수정] 단 한 번만 전송하며 total_asset을 포함합니다.
        socketio.emit('message', {
            'nickname': nick, 
            'msg': raw, 
            'type': 'chat', 
            'rank': rank, 
            'reward': f"+{reward:,}₩",
            'total_asset': total 
        }, room='main')
        
if __name__ == '__main__':
    socketio.run(app, debug=True, port=PORT, host='0.0.0.0')
