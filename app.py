import os
from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 👇 初期データに「comments」の項目を追加しました
posts = [
    {
        "id": 1,
        "title": "最初のブログ記事",
        "content": "これはPythonとFlaskを使って作ったブログの最初の投稿です！",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image": None,
        "comments": [
            {
                "author": "読者A",
                "text": "素敵なブログですね！これからの更新も楽しみにしています。",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        ]
    }
]

@app.route('/')
def home():
    return render_template('index.html', posts=reversed(posts))

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        file = request.files.get('image')
        image_filename = None
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        if title and content:
            new_id = len(posts) + 1
            posts.append({
                "id": new_id,
                "title": title,
                "content": content,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": image_filename,
                "comments": []  # 新しい記事は最初コメント空っぽ
            })
            return redirect(url_for('home'))
            
    return render_template('new_post.html')

@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        abort(404)
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post['image'] = filename

        if title and content:
            post['title'] = title
            post['content'] = content
            post['date'] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (編集済)"
            return redirect(url_for('home'))
            
    return render_template('edit_post.html', post=post)

# 👇 【新機能】コメントを追加するためのルート
@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
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
        
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)