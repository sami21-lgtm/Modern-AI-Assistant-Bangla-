from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import random
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app) # ফ্রন্টএন্ড থেকে এক্সেস দেওয়ার জন্য এটি যুক্ত করা হলো

DATABASE = 'sami_ai.db'

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

def generate_bangla_response(message):
    msg = message.strip().lower()
    if any(w in msg for w in ['তুমি কে', 'কে তুমি', 'who are you', 'who r u', 'আপনি কে']):
        return ("আমি সামি এআই, একটি বাংলা ভাষার চ্যাটবট।\nআমাকে তৈরি করেছেন মোঃ এমতিয়াজ হোসেন সামি,\nডিপার্টমেন্ট অফ সফটওয়্যার ইঞ্জিনিয়ারিং,\nড্যাফোডিল ইন্টারন্যাশনাল ইউনিভার্সিটি।")
    if any(w in msg for w in ['কে বানিয়েছে', 'তোমার নির্মাতা', 'developer', 'who made you']):
        return "আমাকে তৈরি করেছেন মোঃ এমতিয়াজ হোসেন সামি।"
    if 'ড্যাফোডিল' in msg or 'daffodil' in msg or 'diu' in msg:
        return "ড্যাফোডিল ইন্টারন্যাশনাল ইউনিভার্সিটি বাংলাদেশের অন্যতম সেরা বেসরকারি বিশ্ববিদ্যালয়। এখানে সফটওয়্যার ইঞ্জিনিয়ারিংসহ অনেক চমৎকার প্রোগ্রাম রয়েছে।"
    if 'সফটওয়্যার' in msg or 'software' in msg:
        return "সফটওয়্যার ইঞ্জিনিয়ারিং একটি অসাধারণ ক্ষেত্র, যেখানে আপনি প্রোগ্রামিং, সিস্টেম ডিজাইন, ডাটাবেজ ও ওয়েব ডেভেলপমেন্ট শিখতে পারবেন।"
    if 'আবহাওয়া' in msg or 'weather' in msg:
        return "দুঃখিত, আমি এখনো রিয়েল-টাইম আবহাওয়ার তথ্য দিতে পারি না। তবে আমি অন্যান্য প্রশ্নে সাহায্য করতে প্রস্তুত!"
    if 'জোক' in msg or 'joke' in msg or 'কৌতুক' in msg:
        jokes = [
            "প্রোগ্রামারদের প্রিয় জায়গা কোথায়? - 'ক্লাউড' এ! 😄",
            "কম্পিউটার কেন ঠান্ডা থাকে? কারণ তার অনেক ফ্যান আছে!",
            "একটি বাগ আরেকটি বাগকে বলল: 'তুমি এত সুন্দর, তোমাকে ডিবাগ করতে ইচ্ছে করছে না!' 😂"
        ]
        return random.choice(jokes)
    if 'কী করতে পারো' in msg or 'what can you do' in msg:
        return "আমি বাংলা ভাষায় যেকোনো প্রশ্নের উত্তর দিতে পারি।\n- সাধারণ জ্ঞান\n- প্রযুক্তি বিষয়ক তথ্য\n- কৌতুক\n- পরামর্শ\nশুধু জিজ্ঞাসা করুন!"
    if 'ধন্যবাদ' in msg or 'thanks' in msg or 'thank you' in msg:
        return "আপনাকে অসংখ্য ধন্যবাদ! আবার জিজ্ঞাসা করতে পারেন। 😊"
    if 'কেমন আছো' in msg or 'how are you' in msg:
        return "আমি ভালো আছি, আলহামদুলিল্লাহ! আপনি কেমন আছেন?"

    default_responses = [
        "আপনার প্রশ্নটি খুবই চমৎকার। আমি আমার জ্ঞান অনুযায়ী উত্তর দেওয়ার চেষ্টা করব।",
        "বুঝতে পেরেছি। চলুন দেখি কিভাবে সাহায্য করতে পারি।",
        "এটি একটি গুরুত্বপূর্ণ বিষয়। আমি চেষ্টা করছি বিস্তারিত জানাতে।",
        "দারুণ প্রশ্ন! আমি যতটুকু জানি তা শেয়ার করছি।"
    ]
    return random.choice(default_responses) + "\n\n(আমি এখনো শিখছি, শীঘ্রই আরও স্মার্ট হব!)"

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
        return jsonify({
            'response': '⚠️ দুঃখিত, এই ধরনের কনটেন্ট অনুমোদিত নয়। দয়া করে ভদ্র ভাষায় কথা বলুন।',
            'conversation_id': conversation_id,
            'language': 'bn'
        })

    bot_response = generate_bangla_response(user_message)
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
