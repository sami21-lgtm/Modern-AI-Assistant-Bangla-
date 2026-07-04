from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import random
from datetime import datetime
from openai import OpenAI # DeepSeek OpenAI compatible library

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "https://sami21-lgtm.github.io"}})

DATABASE = 'sami_ai.db'

# ⚠️ DeepSeek এপিআই সেটআপ
# এখানে আপনার DeepSeek API কী বসান 
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY_HERE"

# DeepSeek ক্লায়েন্ট ইনিশিয়ালাইজ (এটি OpenAI এর ফরম্যাটে কিন্তু URL ভিন্ন)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com" 
)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            language TEXT,
            created_at TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def generate_id():
    return datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(1000,9999))

BANNED_WORDS = ['sex', 'porn', 'nude', 'xxx', 'fuck', 'shit', 'bastard', 'haram', 'অশ্লীল', 'পর্ণ', 'নগ্ন', 'যৌন', 'ধর্ষণ', 'খারাপ']
def contains_adult_content(text):
    text_lower = text.lower()
    return any(word in text_lower for word in BANNED_WORDS)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'মেসেজ প্রয়োজন'}), 400

    user_message = data['message']
    conversation_id = data.get('conversation_id')

    # এডাল্ট কনটেন্ট চেক
    if contains_adult_content(user_message):
        return jsonify({
            'response': '⚠️ দুঃখিত, এই ধরনের কনটেন্ট অনুমোদিত নয়। দয়া করে ভদ্র ভাষায় কথা বলুন।',
            'conversation_id': conversation_id,
            'language': 'bn'
        })

    # ⭐ DeepSeek AI দিয়ে সীমাহীন জেনারেটর
    try:
        # সিস্টেম প্রম্পট: AI কে ১০০% বাংলায় উত্তর দেওয়ার জন্য নির্দেশনা
        system_prompt = "আপনি একজন বুদ্ধিমান বাংলা এআই সহকারী। আপনার নাম 'Sami AI'। আপনাকে তৈরি করেছেন মোঃ ইমতিয়াজ হোসেন সামি ( সফটওয়্যার ইঞ্জিনিয়ারিং বিভাগ,ড্যাফোডিল ইন্টারন্যাশনাল ইউনিভার্সিটি)। আপনি যেকোনো ভাষায় প্রশ্ন পেলে সবসময় শুধুমাত্র বাংলায় উত্তর দেবেন।"
        
        response = client.chat.completions.create(
            model="deepseek-chat", # এখানে "deepseek-reasoner" দিলে R1 লজিক্যাল মডেল কাজ করবে
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=False
        )
        
        bot_response = response.choices[0].message.content
        
    except Exception as e:
        bot_response = f"⚠️ সার্ভারে একটু সমস্যা হচ্ছে। বিস্তারিত: {str(e)}। দয়া করে আবার চেষ্টা করুন।"

    # ডাটাবেসে সংরক্ষণ
    conn = get_db()
    if not conversation_id:
        conversation_id = generate_id()
        title = user_message[:40] + ('...' if len(user_message) > 40 else '')
        conn.execute('INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)',
                     (conversation_id, title, datetime.now().isoformat()))
    else:
        exists = conn.execute('SELECT id FROM conversations WHERE id=?', (conversation_id,)).fetchone()
        if not exists:
            conversation_id = generate_id()
            title = user_message[:40] + '...'
            conn.execute('INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)',
                         (conversation_id, title, datetime.now().isoformat()))

    now = datetime.now().isoformat()
    conn.execute('INSERT INTO messages (conversation_id, role, content, language, created_at) VALUES (?, ?, ?, ?, ?)',
                 (conversation_id, 'user', user_message, 'bn', now))
    conn.execute('INSERT INTO messages (conversation_id, role, content, language, created_at) VALUES (?, ?, ?, ?, ?)',
                 (conversation_id, 'assistant', bot_response, 'bn', now))
    conn.commit()
    conn.close()

    return jsonify({
        'response': bot_response,
        'conversation_id': conversation_id,
        'language': 'bn'
    })

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    conn = get_db()
    rows = conn.execute('SELECT id, title, created_at FROM conversations ORDER BY created_at DESC').fetchall()
    conn.close()
    convs = [{'id': r['id'], 'title': r['title'], 'created_at': r['created_at']} for r in rows]
    return jsonify({'conversations': convs})

@app.route('/api/conversations/<conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    conn = get_db()
    rows = conn.execute('SELECT role, content, language, created_at FROM messages WHERE conversation_id=? ORDER BY created_at ASC', (conv_id,)).fetchall()
    conn.close()
    msgs = [{'role': r['role'], 'content': r['content'], 'language': r['language'], 'created_at': r['created_at']} for r in rows]
    return jsonify({'messages': msgs})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
