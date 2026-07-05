from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import random
from datetime import datetime
import google.generativeai as genai

# অ্যাপ সেটআপ
app = Flask(__name__, static_folder='static', static_url_path='')

# CORS আপডেট করা হয়েছে যাতে গিটহাব পেজেস থেকে কোনো কানেকশন এরর না আসে
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATABASE = 'sami_ai.db'

# জেমিনি এপিআই কনফিগারেশন
# ⚠️ এখানে আপনার আসল Gemini API Key বসাতে ভুলবেন না
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
model = genai.GenerativeModel('gemini-1.5-flash')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS conversations 
                    (id TEXT PRIMARY KEY, title TEXT, created_at TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT, role TEXT, 
                     content TEXT, language TEXT, created_at TEXT, 
                     FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE)''')
    conn.commit()
    conn.close()

def generate_id():
    return datetime.now().strftime('%Y%m%d%H%M%S%f') + str(random.randint(1000,9999))

BANNED_WORDS = ['sex', 'porn', 'nude', 'xxx', 'fuck', 'shit', 'bastard', 'haram', 'অশ্লীল', 'পর্ণ', 'নগ্ন', 'যৌন', 'ধর্ষণ', 'খারাপ']
def contains_adult_content(text):
    return any(word in text.lower() for word in BANNED_WORDS)

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

    if contains_adult_content(user_message):
        return jsonify({'response': '⚠️ দুঃখিত, এই ধরনের কনটেন্ট অনুমোদিত নয়।', 'conversation_id': conversation_id, 'language': 'bn'})

    try:
        # এআই-এর পরিচয়ে আপনার প্রজেক্টের কাঙ্ক্ষিত ক্রেডিট লাইনটি যুক্ত করা হয়েছে
        system_prompt = "আপনি একজন বুদ্ধিমান বাংলা এআই সহকারী। আপনার নাম 'Sami AI'। আপনাকে তৈরি করেছেন মোঃ ইমতিয়াজ হোসেন সামি (সফটওয়্যার ইঞ্জিনিয়ারিং বিভাগ, ড্যাফোডিল ইন্টারন্যাশনাল ইউনিভার্সিটি) - developed by Md. Emtiaz Hossain Sami 2026. আপনি সবসময় শুধুমাত্র বাংলায় উত্তর দেবেন।"
        response = model.generate_content(f"{system_prompt}\nUser: {user_message}")
        bot_response = response.text
    except Exception as e:
        bot_response = f"⚠️ সার্ভারে সমস্যা হচ্ছে। বিস্তারিত: {str(e)}"

    conn = get_db()
    if not conversation_id or not conn.execute('SELECT id FROM conversations WHERE id=?', (conversation_id,)).fetchone():
        conversation_id = generate_id()
        title = user_message[:40] + ('...' if len(user_message) > 40 else '')
        conn.execute('INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)', (conversation_id, title, datetime.now().isoformat()))

    now = datetime.now().isoformat()
    conn.execute('INSERT INTO messages (conversation_id, role, content, language, created_at) VALUES (?, ?, ?, ?, ?)', (conversation_id, 'user', user_message, 'bn', now))
    conn.execute('INSERT INTO messages (conversation_id, role, content, language, created_at) VALUES (?, ?, ?, ?, ?)', (conversation_id, 'assistant', bot_response, 'bn', now))
    conn.commit()
    conn.close()

    return jsonify({'response': bot_response, 'conversation_id': conversation_id, 'language': 'bn'})

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    conn = get_db()
    rows = conn.execute('SELECT id, title, created_at FROM conversations ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify({'conversations': [dict(r) for r in rows]})

@app.route('/api/conversations/<conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    conn = get_db()
    rows = conn.execute('SELECT role, content, language, created_at FROM messages WHERE conversation_id=? ORDER BY created_at ASC', (conv_id,)).fetchall()
    conn.close()
    return jsonify({'messages': [dict(r) for r in rows]})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
