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
                "category": "プログラミング",
                "comments": []
            }
        ]
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 👇 【新機能】今までに使われているカテゴリーの一覧を重複なく取得する関数
def get_existing_categories(posts):
    categories = set()
    for p in posts:
        cat = p.get('category', '未分類')
        if cat:
            categories.add(cat)
    return sorted(list(categories))


@app.route('/')
def home():
    posts = load_data()
    selected_category = request.args.get('category')
    
    if selected_category:
        posts = [p for p in posts if p.get('category') == selected_category]
        
    return render_template('index.html', posts=reversed(posts), selected_category=selected_category)

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    posts = load_data()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # ⚠️既存の選択（existing_category）か、新規入力（new_category）かを取得
        existing_cat = request.form.get('existing_category')
        new_cat = request.form.get('new_category', '').strip()
        
        # 新規入力があればそれを優先、なければ既存の選択、どちらもなければ「未分類」
        category = new_cat if new_cat else (existing_cat if existing_cat else '未分類')

        file = request.files.get('image')
        image_filename = None
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        if title and content:
            new_id = max([p['id'] for p in posts]) + 1 if posts else 1
            posts.append({
                "id": new_id,
                "title": title,
                "content": content,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": image_filename,
                "category": category,
                "comments": []
            })
            save_data(posts)
            return redirect(url_for('home'))
            
    # ⚠️既存のカテゴリー一覧をテンプレートに渡す
    existing_categories = get_existing_categories(posts)
    return render_template('new_post.html', categories=existing_categories)

@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    posts = load_data()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post is None:
        abort(404)
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # ⚠️編集時も同様に取得
        existing_cat = request.form.get('existing_category')
        new_cat = request.form.get('new_category', '').strip()
        category = new_cat if new_cat else (existing_cat if existing_cat else '未分類')
        
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post['image'] = filename

        if title and content:
            post['title'] = title
            post['content'] = content
            post['category'] = category
            post['date'] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (編集済)"
            
            for i, p in enumerate(posts):
                if p['id'] == post_id:
                    posts[i] = post
                    break
            save_data(posts)
            return redirect(url_for('home'))
            
    # ⚠️既存のカテゴリー一覧をテンプレートに渡す
    existing_categories = get_existing_categories(posts)
    return render_template('edit_post.html', post=post, categories=existing_categories)

@app.route('/post/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    posts = load_data()
    posts = [p for p in posts if p['id'] != post_id]
    save_data(posts)
    return redirect(url_for('home'))

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