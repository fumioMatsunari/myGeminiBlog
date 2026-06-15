import os
import json
from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = 'blog_data.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        return [
            {
                "id": 1,
                "title": "最初のブログ記事",
                "content": "これはPythonとFlaskを使って作ったブログの最初の投稿です！",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": None,
                "category": "プログラミング",  # 👇 初期データにカテゴリーを追加
                "comments": []
            }
        ]
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/')
def home():
    posts = load_data()
    # 絞り込み用のカテゴリーが指定されているかチェック
    selected_category = request.args.get('category')
    
    if selected_category:
        # 選ばれたカテゴリーの記事だけを抽出
        posts = [p for p in posts if p.get('category') == selected_category]
        
    return render_template('index.html', posts=reversed(posts), selected_category=selected_category)

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', '未分類')  # 👇 カテゴリーを取得
        
        file = request.files.get('image')
        image_filename = None
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        if title and content:
            posts = load_data()
            new_id = max([p['id'] for p in posts]) + 1 if posts else 1
            posts.append({
                "id": new_id,
                "title": title,
                "content": content,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": image_filename,
                "category": category,  # 👇 保存データに追加
                "comments": []
            })
            save_data(posts)
            return redirect(url_for('home'))
            
    return render_template('new_post.html')

@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    posts = load_data()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        abort(404)
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', '未分類')  # 👇 編集時も取得
        
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post['image'] = filename

        if title and content:
            post['title'] = title
            post['content'] = content
            post['category'] = category  # 👇 編集内容を反映
            post['date'] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (編集済)"
            
            for i, p in enumerate(posts):
                if p['id'] == post_id:
                    posts[i] = post
                    break
            save_data(posts)
            return redirect(url_for('home'))
            
    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    posts = load_data()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        abort(404)
        
    author = request.form.get('author', '名無しさん')
    text = request.form.get('text')
    
    if text:
        post['comments'].append({
            "author": author if author.strip() != "" else "名無しさん",
            "text": text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        for i, p in enumerate(posts):
            if p['id'] == post_id:
                posts[i] = post
                break
        save_data(posts)
        
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)