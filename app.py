import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, jsonify, abort)
from flask_login import (LoginManager, login_user, logout_user,
                          login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
import socket

# Force IPv4-only for ALL network calls (fixes broken IPv6 route on some carriers)
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_only_getaddrinfo
try:
    from bot_system import start_bots
    _bots_available = True
except:
    _bots_available = False
from database import (db, User, Story, Like, Comment, Notification,
                      ReadingList, AdminMessage, Competition,
                      CompetitionEntry, PeerReview, ExpertReview,
                      StoryView, Award, ActivityLog, ResetRequest,
                      CompetitionWinner, list_stories, GemTransaction)

# ─────────────────────────────────────────────
#  APP SETUP
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY']           = 'writersworld-secret-2024'
app.config['WTF_CSRF_ENABLED']      = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']        = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH']   = 5 * 1024 * 1024  # 5MB

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "meta-llama/llama-3.3-70b-instruct:free"
ADMIN_EMAIL  = "Danielerastus001@gmail.com"
GENRES       = ["General","Romance","Action","Fantasy","Sci-Fi",
                "Horror","Mystery","Comedy","Drama","Thriller",
                "Adventure","Historical","Poetry","Other"]

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('announcements', exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp'}

def save_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ts       = str(int(datetime.utcnow().timestamp()))
        filename = ts + '_' + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return ""

def log_activity(action, detail=""):
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip      = request.remote_addr
        entry   = ActivityLog(user_id=user_id, action=action,
                              detail=detail, ip_address=ip)
        db.session.add(entry)
        db.session.commit()
    except:
        pass

def add_notification(user_id, message, ntype="info", link=""):
    n = Notification(user_id=user_id, message=message,
                     type=ntype, link=link)
    db.session.add(n)
    db.session.commit()

def load_announcements():
    path = os.path.join('announcements', 'announcements.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

def save_announcement(title, body, image=""):
    path  = os.path.join('announcements', 'announcements.json')
    items = load_announcements()
    items.insert(0, {
        "title": title, "body": body, "image": image,
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    })
    with open(path, 'w') as f:
        json.dump(items, f, indent=2)

def ask_aegis(prompt):
    key = GROQ_API_KEY
    cfg = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(cfg):
        with open(cfg) as f:
            data = json.load(f)
            key  = data.get('groq_api_key', key)
    if not key:
        return None, "Aegis API key not configured. Please add it in Admin settings."
    url     = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content":
             "You are Aegis, a creative writing AI assistant. "
             "You help writers improve their stories. Be specific and helpful."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    try:
        r    = requests.post(url, headers=headers, json=payload, timeout=20)
        data = r.json()
        return data['choices'][0]['message']['content'].strip(), None
    except Exception as e:
        return None, f"Aegis error: {str(e)}"

# ─────────────────────────────────────────────
#  AWARDS CHECKER
# ─────────────────────────────────────────────
def check_awards(user):
    """Check and grant awards immediately — called after every qualifying action"""
    try:
        existing = [a.name for a in Award.query.filter_by(user_id=user.id).all()]
        stories  = Story.query.filter_by(user_id=user.id, is_published=True).all()
        pub             = len(stories)
        total_likes     = sum(s.like_count() for s in stories)
        total_comments  = sum(s.comment_count() for s in stories)
        followers       = user.follower_count()

        candidates = []

        # Story count awards
        if pub >= 1:  candidates.append(("First Story",      "🌱", "Published first story"))
        if pub >= 5:  candidates.append(("Prolific Writer",  "✍️",  "Published 5 stories"))
        if pub >= 10: candidates.append(("Storyteller",      "📖", "Published 10 stories"))
        if pub >= 20: candidates.append(("Master Wordsmith", "👑", "Published 20 stories"))

        # Likes awards
        if any(s.like_count() >= 10 for s in stories):
            candidates.append(("Rising Star",    "⭐", "10+ likes on a single story"))
        if total_likes >= 50:
            candidates.append(("Popular Author", "🔥", "50+ total likes"))
        if total_likes >= 100:
            candidates.append(("Bestseller",     "🏆", "100+ total likes"))
        if total_likes >= 500:
            candidates.append(("Legend",         "🌟", "500+ total likes"))

        # Comment awards
        if total_comments >= 1:
            candidates.append(("First Comment",   "💬", "Received first comment"))
        if total_comments >= 25:
            candidates.append(("Engaging Writer", "🗣️",  "25+ comments received"))

        # Follower awards
        if followers >= 50:
            candidates.append(("Follower Magnet",   "📣", "50+ followers"))
        if followers >= 100:
            candidates.append(("Community Builder", "🤝", "100+ followers"))
        if followers >= 500:
            candidates.append(("Influencer",        "💫", "500+ followers"))

        new_awards = []
        for name, icon, reason in candidates:
            if name not in existing:
                award = Award(user_id=user.id, name=name,
                              icon=icon, reason=reason)
                db.session.add(award)
                new_awards.append(f"{icon} {name}")

        if new_awards:
            # Single notification listing all new awards
            awards_str = ", ".join(new_awards)
            notif = Notification(
                user_id=user.id,
                message=f"🎉 New award{'s' if len(new_awards) > 1 else ''} earned: {awards_str}!",
                type="success")
            db.session.add(notif)
            db.session.commit()
    except Exception as e:
        print(f"Award check error: {e}")

# ─────────────────────────────────────────────
#  CONTEXT PROCESSOR — passes unread to all pages
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    unread = 0
    bot_badge = 0
    comment_badge = 0
    activity_badge = 0
    if current_user.is_authenticated:
        unread = Notification.query.filter_by(
            user_id=current_user.id, is_read=False).count()
        if current_user.is_admin:
            bot_names = ["Amara","Chidi","Fatima","Emeka","Ngozi",
                "Kwame","Aisha","Tobias","Yemi","Sade","Malik","Zara",
                "Kofi","Chisom","Adaeze","Tunde","Halima","Seun","Nneka","Jide"]
            bot_badge = Story.query.join(User).filter(
                Story.is_published==False,
                User.username.in_(bot_names)
            ).count()

            comment_badge = Comment.query.filter_by(is_seen_by_admin=False).count()
            activity_badge = ActivityLog.query.filter_by(is_seen_by_admin=False).count()

        ann_badge = False
        try:
            last_seen = current_user.last_seen_announcements or datetime(2000,1,1)
            anns = load_announcements()
            for a in anns:
                a_date = datetime.strptime(a.get('date',''), '%Y-%m-%d %H:%M')
                if a_date > last_seen:
                    ann_badge = True
                    break
        except:
            ann_badge = False

        comp_badge = False
        try:
            last_comp_visit = current_user.last_visited_competitions or datetime(2000,1,1)
            today = datetime.utcnow().date()
            new_comps = Competition.query.filter(Competition.created_at > last_comp_visit).count()
            ending_soon = Competition.query.filter(
                Competition.end_date >= today,
                Competition.end_date <= today + timedelta(days=3)
            ).count()
            comp_badge = (new_comps > 0) or (ending_soon > 0)
        except:
            comp_badge = False

    return dict(unread=unread, bot_badge=bot_badge,
                comment_badge=comment_badge, activity_badge=activity_badge,
                ann_badge=ann_badge if current_user.is_authenticated else False,
                comp_badge=comp_badge if current_user.is_authenticated else False)

# ─────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────
@app.route('/signup', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not username or not email or not password:
            flash('All fields required.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')
        is_admin = (email == ADMIN_EMAIL.lower())
        user = User(
            username=username, email=email,
            password=generate_password_hash(password),
            is_admin=is_admin
        )
        db.session.add(user)
        db.session.commit()
        log_activity('signup', f"New user {username} signed up")
        login_user(user)
        if is_admin:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user     = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        if user.is_banned:
            flash('Your account has been banned.', 'error')
            return render_template('login.html')
        log_activity('login', f"User {user.username} logged in")
        login_user(user)
        if user.is_admin:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search','').strip()
    genre  = request.args.get('genre','')
    page   = request.args.get('page', 1, type=int)
    query  = Story.query.filter_by(is_published=True)
    if search:
        query = query.filter(
            Story.title.ilike(f'%{search}%') |
            Story.content.ilike(f'%{search}%'))
    if genre:
        query = query.filter_by(genre=genre)
    all_matching = query.all()
    now = datetime.utcnow()

    # Personalization: who the user follows + genres they engage with
    followed_ids = set()
    preferred_genres = {}
    if current_user.is_authenticated:
        followed_ids = {u.id for u in current_user.followed}
        liked_story_ids = [l.story_id for l in Like.query.filter_by(user_id=current_user.id).all()]
        viewed_story_ids = [v.story_id for v in StoryView.query.filter_by(user_id=current_user.id).all()]
        genre_source_ids = set(liked_story_ids + viewed_story_ids)
        if genre_source_ids:
            genre_stories = Story.query.filter(Story.id.in_(genre_source_ids)).all()
            for gs in genre_stories:
                preferred_genres[gs.genre] = preferred_genres.get(gs.genre, 0) + 1

    def hot_score(s):
        hours = max((now - s.created_at).total_seconds() / 3600, 0)
        hours = round(hours * 4) / 4
        likes_ct = len(s.likes)
        comments_ct = len(s.comments)
        base = (s.views + likes_ct*3 + comments_ct*5) / ((hours + 2) ** 1.5)

        boost = 1.0
        if s.user_id in followed_ids:
            boost += 1.5
        if s.genre in preferred_genres:
            boost += min(preferred_genres[s.genre] * 0.15, 1.0)

        return round(base * boost, 4)

    import random as _random
    weights = [max(hot_score(s), 0.01) for s in all_matching]
    if all_matching:
        shuffled = []
        pool = list(zip(all_matching, weights))
        while pool:
            total_w = sum(w for _, w in pool)
            r = _random.uniform(0, total_w)
            upto = 0
            for idx, (story_item, w) in enumerate(pool):
                upto += w
                if upto >= r:
                    shuffled.append(story_item)
                    pool.pop(idx)
                    break
        all_matching = shuffled

    per_page = 10
    total = len(all_matching)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = all_matching[start:end]

    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = max((total + per_page - 1) // per_page, 1)
            self.has_next = page < self.pages
            self.has_prev = page > 1
            self.next_num = page + 1
            self.prev_num = page - 1

    stories = SimplePagination(page_items, page, per_page, total)

    if request.args.get('ajax') == '1':
        return render_template('_story_cards.html', stories=stories)

    announcements = load_announcements()[:3]
    competitions  = Competition.query.order_by(
                     Competition.created_at.desc()).limit(3).all()
    return render_template('dashboard.html',
        stories=stories, genres=GENRES,
        search=search, selected_genre=genre,
        announcements=announcements,
        competitions=competitions)

# ─────────────────────────────────────────────
#  STORIES
# ─────────────────────────────────────────────
@app.route('/write', methods=['GET','POST'])
@login_required
def write():
    if request.method == 'POST':
        title   = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        genre   = request.form.get('genre','General')
        publish = request.form.get('publish') == 'true'
        if not title or not content:
            flash('Title and content required.', 'error')
            return render_template('write.html', genres=GENRES)
        cover = ""
        if 'cover' in request.files:
            cover = save_upload(request.files['cover'])
        story = Story(
            title=title, content=content, genre=genre,
            cover=cover, is_published=publish,
            user_id=current_user.id
        )
        db.session.add(story)
        db.session.commit()
        flash('Story saved!', 'success')
        return redirect(url_for('my_stories'))
    return render_template('write.html', genres=GENRES)

@app.route('/edit/<int:story_id>', methods=['GET','POST'])
@login_required
def edit_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        story.title      = request.form.get('title', story.title).strip()
        story.content    = request.form.get('content', story.content).strip()
        story.genre      = request.form.get('genre', story.genre)
        story.updated_at = datetime.utcnow()
        if story.pending_republish:
            story.pending_republish = False
        if 'cover' in request.files and request.files['cover'].filename:
            story.cover = save_upload(request.files['cover'])
        db.session.commit()
        flash('Story updated!', 'success')
        return redirect(url_for('my_stories'))
    return render_template('write.html', story=story, genres=GENRES, editing=True)

@app.route('/delete/<int:story_id>', methods=['POST'])
@login_required
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(story)
    db.session.commit()
    flash('Story deleted.', 'success')
    return redirect(url_for('my_stories'))

@app.route('/publish/<int:story_id>', methods=['POST'])
@login_required
def toggle_publish(story_id):
    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user.id:
        abort(403)
    if not story.is_published:
        if story.unpublish_reason:
            story.pending_republish = True
            db.session.commit()
            flash('Republish request sent to admin.', 'info')
            return redirect(url_for('my_stories'))
        story.is_published = True
        check_awards(current_user)
        log_activity('publish_story', f"Published story: {story.title}")
    else:
        story.is_published = False
        log_activity('unpublish_story', f"Unpublished story: {story.title}")
    db.session.commit()
    return redirect(url_for('my_stories'))

@app.route('/story/<int:story_id>')
def read_story(story_id):
    story = Story.query.get_or_404(story_id)
    is_owner = current_user.is_authenticated and story.user_id == current_user.id
    is_admin_viewer = current_user.is_authenticated and getattr(current_user, 'is_admin', False)
    if not story.is_published and not is_owner and not is_admin_viewer:
        abort(404)
    # Count view (not author's own)
    is_author = current_user.is_authenticated and current_user.id == story.user_id
    if not is_author:
        ip = request.remote_addr
        if current_user.is_authenticated:
            existing = StoryView.query.filter_by(
                story_id=story_id, user_id=current_user.id).first()
        else:
            existing = StoryView.query.filter_by(
                story_id=story_id, ip_address=ip).first()
        if not existing:
            sv = StoryView(
                story_id=story_id,
                user_id=current_user.id if current_user.is_authenticated else None,
                ip_address=ip)
            db.session.add(sv)
            story.views += 1
            db.session.commit()
            if current_user.is_authenticated:
                log_activity('view_story', f"{current_user.username} viewed '{story.title}'")
    liked    = False
    in_lists = []
    if current_user.is_authenticated:
        liked    = story.is_liked_by(current_user)
        in_lists = ReadingList.query.filter_by(
                    user_id=current_user.id).all()
    comments = Comment.query.filter_by(story_id=story_id)\
                             .order_by(Comment.created_at.desc()).all()
    return render_template('read.html', story=story,
                           liked=liked, in_lists=in_lists,
                           comments=comments)

@app.route('/like/<int:story_id>', methods=['POST'])
@login_required
def like_story(story_id):
    story    = Story.query.get_or_404(story_id)
    existing = Like.query.filter_by(
                user_id=current_user.id, story_id=story_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'liked': False, 'count': story.like_count()})
    like = Like(user_id=current_user.id, story_id=story_id)
    db.session.add(like)
    log_activity('like', f"Liked story: {story.title}")
    if story.user_id != current_user.id:
        add_notification(story.user_id,
            f"{current_user.username} liked your story '{story.title}'",
            'like', url_for('read_story', story_id=story_id))
    db.session.commit()
    check_awards(User.query.get(story.user_id))
    return jsonify({'liked': True, 'count': story.like_count()})

@app.route('/comment/<int:story_id>', methods=['POST'])
@login_required
def add_comment(story_id):
    story   = Story.query.get_or_404(story_id)
    content = request.form.get('content','').strip()
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('read_story', story_id=story_id))
    comment = Comment(content=content, user_id=current_user.id,
                      story_id=story_id)
    db.session.add(comment)
    log_activity('comment', f"Commented on story: {story.title}")
    if story.user_id != current_user.id:
        add_notification(story.user_id,
            f"{current_user.username} commented on '{story.title}'",
            'comment', url_for('read_story', story_id=story_id))
    db.session.commit()
    check_awards(User.query.get(story.user_id))
    flash('Comment added!', 'success')
    return redirect(url_for('read_story', story_id=story_id))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    story_id = comment.story_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('read_story', story_id=story_id))

@app.route('/my_stories')
@login_required
def my_stories():
    stories = Story.query.filter_by(user_id=current_user.id)\
                          .order_by(Story.created_at.desc()).all()
    return render_template('my_stories.html', stories=stories)

# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user     = User.query.get_or_404(user_id)
    is_owner = current_user.id == user_id
    stories  = Story.query.filter_by(user_id=user_id, is_published=True)\
                           .order_by(Story.created_at.desc()).all()
    drafts   = []
    if is_owner:
        drafts = Story.query.filter_by(
                  user_id=user_id, is_published=False).all()
    following = current_user.is_following(user) \
                if not is_owner else False
    awards = Award.query.filter_by(user_id=user_id)                        .order_by(Award.created_at.desc()).all()
    return render_template('profile.html',
        user=user, stories=stories, drafts=drafts,
        is_owner=is_owner, following=following, awards=awards)

@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio','').strip()
        if 'avatar' in request.files and request.files['avatar'].filename:
            current_user.avatar = save_upload(request.files['avatar'])
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))
    return render_template('edit_profile.html')

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    if current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        log_activity('unfollow', f"{current_user.username} unfollowed {user.username}")
        return jsonify({'following': False,
                        'count': user.follower_count()})
    current_user.follow(user)
    add_notification(user.id,
        f"{current_user.username} started following you",
        'follow', url_for('profile', user_id=current_user.id))
    db.session.commit()
    check_awards(user)
    log_activity('follow', f"{current_user.username} followed {user.username}")
    return jsonify({'following': True,
                    'count': user.follower_count()})

# ─────────────────────────────────────────────
#  MY STATS
# ─────────────────────────────────────────────
@app.route('/stats')
@login_required
def my_stats():
    stories      = Story.query.filter_by(user_id=current_user.id).all()
    total_views  = sum(s.views for s in stories)
    total_likes  = sum(s.like_count() for s in stories)
    total_comments = sum(s.comment_count() for s in stories)
    followers    = current_user.follower_count()
    following    = current_user.following_count()
    published    = [s for s in stories if s.is_published]
    drafts       = [s for s in stories if not s.is_published]
    top_stories  = sorted(published, key=lambda s: s.views, reverse=True)[:5]
    return render_template('author_dashboard.html',
        total_views=total_views, total_likes=total_likes,
        total_comments=total_comments, followers=followers,
        following=following, published=published,
        drafts=drafts, top_stories=top_stories)

# ─────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
                                .order_by(Notification.created_at.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

# ─────────────────────────────────────────────
#  READING LISTS
# ─────────────────────────────────────────────
@app.route('/lists')
@login_required
def reading_lists():
    lists = ReadingList.query.filter_by(user_id=current_user.id).all()
    return render_template('lists.html', lists=lists)

@app.route('/list/create', methods=['POST'])
@login_required
def create_list():
    name = request.form.get('name','').strip()
    if not name:
        flash('List name required.', 'error')
        return redirect(url_for('reading_lists'))
    rl = ReadingList(name=name, user_id=current_user.id)
    db.session.add(rl)
    db.session.commit()
    flash('Reading list created!', 'success')
    return redirect(url_for('reading_lists'))

@app.route('/list/<int:list_id>')
@login_required
def view_list(list_id):
    rl = ReadingList.query.get_or_404(list_id)
    if rl.user_id != current_user.id and not rl.is_public:
        abort(403)
    return render_template('view_list.html', reading_list=rl)

@app.route('/list/add/<int:list_id>/<int:story_id>', methods=['POST'])
@login_required
def add_to_list(list_id, story_id):
    rl    = ReadingList.query.get_or_404(list_id)
    story = Story.query.get_or_404(story_id)
    if rl.user_id != current_user.id:
        abort(403)
    if story not in rl.stories:
        rl.stories.append(story)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/list/delete/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    rl = ReadingList.query.get_or_404(list_id)
    if rl.user_id != current_user.id:
        abort(403)
    db.session.delete(rl)
    db.session.commit()
    flash('List deleted.', 'success')
    return redirect(url_for('reading_lists'))

# ─────────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────────
@app.route('/leaderboard')
def leaderboard():
    users = User.query.filter_by(is_admin=False).all()
    def engagement(u):
        stories = [s for s in u.stories if s.is_published]
        views    = sum(s.views for s in stories)
        likes    = sum(s.like_count() for s in stories)
        comments = sum(s.comment_count() for s in stories)
        return views + (likes * 3) + (comments * 5)
    ranked = sorted(users, key=engagement, reverse=True)[:10]
    return render_template('leaderboard.html', users=ranked, engagement=engagement)

# ─────────────────────────────────────────────
#  AEGIS AI
# ─────────────────────────────────────────────
@app.route('/aegis/grammar', methods=['POST'])
@login_required
def aegis_grammar():
    text   = request.json.get('text','')
    result, error = ask_aegis(
        f"Check this story text for grammar mistakes. "
        f"List each error with the correction. "
        f"Format: ERROR: [mistake] | FIX: [correction]\n\n{text}")
    if error:
        return jsonify({'error': error})
    return jsonify({'result': result})

@app.route('/aegis/idea', methods=['POST'])
@login_required
def aegis_idea():
    import random as _random
    genre  = request.json.get('genre','General')
    seeds  = [
        "set in ancient Africa", "involving time travel",
        "with an unreliable narrator", "told in reverse",
        "featuring a villain as the protagonist",
        "set in a futuristic Lagos", "involving a forbidden love",
        "with a supernatural twist", "based on a true event",
        "where the hero loses in the end", "set underwater",
        "involving artificial intelligence", "in a post-apocalyptic world",
        "featuring twins with opposite personalities",
        "where the setting is the main character",
        "involving a stolen identity", "set during a festival",
        "with multiple POVs", "involving a lost letter",
        "where silence is the main theme"
    ]
    moods = ["dark and haunting", "uplifting and hopeful",
             "mysterious and suspenseful", "funny and satirical",
             "romantic and tender", "action-packed and intense",
             "philosophical and thought-provoking"]
    seed = _random.choice(seeds)
    mood = _random.choice(moods)
    salt = _random.randint(1000, 9999)
    result, error = ask_aegis(
        f"Generate a COMPLETELY UNIQUE professional story idea for the {genre} genre. "
        f"Seed concept: {seed}. Mood: {mood}. Variation ID: {salt}. "
        f"Include: Title, Plot Summary (3 sentences), Main Character description, "
        f"Unexpected Plot Twist, Compelling Opening Line. "
        f"Make it original, vivid, and different from any previous idea. "
        f"Never repeat the same concept twice.")
    if error:
        return jsonify({'error': error})
    return jsonify({'result': result})

@app.route('/aegis/tone', methods=['POST'])
@login_required
def aegis_tone():
    text   = request.json.get('text','')
    result, error = ask_aegis(
        f"Analyze the tone and emotion of this story text. "
        f"Tell me: 1) The dominant emotion, 2) Why you identified it, "
        f"3) What the reader will feel, 4) Suggestions to enhance it.\n\n{text}")
    if error:
        return jsonify({'error': error})
    return jsonify({'result': result})

# ─────────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users        = User.query.order_by(User.joined.desc()).all()
    stories      = Story.query.order_by(Story.created_at.desc()).all()
    comments     = Comment.query.order_by(Comment.created_at.desc()).all()
    announcements= load_announcements()
    competitions = Competition.query.order_by(
                    Competition.created_at.desc()).all()
    republish_requests = Story.query.filter_by(pending_republish=True).all()
    pending_reviews  = PeerReview.query.filter_by(
                        is_approved=False, is_rejected=False).all()
    reset_requests   = ResetRequest.query.filter_by(
                        is_resolved=False).order_by(
                        ResetRequest.created_at.desc()).all()
    return render_template('admin.html',
        users=users, stories=stories,
        comments=comments,
        announcements=announcements,
        competitions=competitions,
        republish_requests=republish_requests,
        pending_reviews=pending_reviews,
        reset_requests=reset_requests)

@app.route('/admin/announce', methods=['POST'])
@login_required
@admin_required
def admin_announce():
    title = request.form.get('title','').strip()
    body  = request.form.get('body','').strip()
    image = ""
    if 'image' in request.files and request.files['image'].filename:
        image = save_upload(request.files['image'])
    if not title or not body:
        flash('Title and body required.', 'error')
        return redirect(url_for('admin_panel'))
    save_announcement(title, body, image)
    # Notify all users
    users = User.query.filter_by(is_admin=False).all()
    for u in users:
        add_notification(u.id, f"Announcement: {title}", 'announcement',
                         url_for('history'))
    flash('Announcement published!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/unpublish/<int:story_id>', methods=['GET','POST'])
@login_required
@admin_required
def admin_unpublish(story_id):
    story = Story.query.get_or_404(story_id)
    if request.method == 'POST':
        reason = request.form.get('reason','').strip()
        if not reason:
            flash('Reason required.', 'error')
            return render_template('admin_reason.html', story=story)
        story.is_published   = False
        story.unpublish_reason = reason
        db.session.commit()
        # Notify author
        add_notification(story.user_id,
            f"Your story '{story.title}' was unpublished. Reason: {reason}",
            'warning', url_for('my_stories'))
        # Send admin message
        msg = AdminMessage(
            admin_id=current_user.id, user_id=story.user_id,
            message=f"Your story '{story.title}' was unpublished.\n\nReason: {reason}")
        db.session.add(msg)
        db.session.commit()
        flash('Story unpublished.', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('admin_reason.html', story=story)

@app.route('/admin/republish/<int:story_id>', methods=['POST'])
@login_required
@admin_required
def admin_approve_republish(story_id):
    story = Story.query.get_or_404(story_id)
    story.is_published      = True
    story.pending_republish = False
    story.unpublish_reason  = ""
    db.session.commit()
    add_notification(story.user_id,
        f"Your story '{story.title}' has been approved for republish.",
        'success', url_for('read_story', story_id=story.id))
    flash('Story republished.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/publish/<int:story_id>', methods=['POST'])
@login_required
@admin_required
def admin_publish(story_id):
    story = Story.query.get_or_404(story_id)
    story.is_published = True
    db.session.commit()
    flash('Story published.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin.', 'error')
        return redirect(url_for('admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/ban/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_ban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    status = "banned" if user.is_banned else "unbanned"
    flash(f'User {status}.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_story/<int:story_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    flash('Story deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/set_api_key', methods=['POST'])
@login_required
@admin_required
def set_api_key():
    key = request.form.get('api_key','').strip()
    cfg = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(cfg, 'w') as f:
        json.dump({'groq_api_key': key}, f)
    flash('Aegis API key saved!', 'success')
    return redirect(url_for('admin_panel'))

# ─────────────────────────────────────────────
#  ADMIN MESSAGES
# ─────────────────────────────────────────────
@app.route('/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        abort(403)
    user     = User.query.get_or_404(user_id)
    admin_user = User.query.filter_by(is_admin=True).first()
    admin_id   = admin_user.id if admin_user else 0
    messages   = AdminMessage.query.filter(
        db.or_(
            db.and_(AdminMessage.admin_id == admin_id,
                    AdminMessage.user_id  == user_id),
            db.and_(AdminMessage.admin_id == user_id,
                    AdminMessage.user_id  == admin_id),
            db.and_(AdminMessage.admin_id == current_user.id,
                    AdminMessage.user_id  == user_id),
            db.and_(AdminMessage.admin_id == user_id,
                    AdminMessage.user_id  == current_user.id)
        )
    ).order_by(AdminMessage.created_at.asc()).all()
    if request.method == 'POST':
        content = request.form.get('message','').strip()
        if content:
            msg = AdminMessage(
                admin_id=current_user.id,
                user_id=user_id,
                message=content,
                is_reply=not current_user.is_admin)
            db.session.add(msg)
            # Notify
            notify_id = user_id if current_user.is_admin else \
                        User.query.filter_by(is_admin=True).first().id
            add_notification(notify_id,
                f"New message from {current_user.username}",
                'message', url_for('chat', user_id=user_id))
            db.session.commit()
        return redirect(url_for('chat', user_id=user_id))
    return render_template('chat.html', user=user, messages=messages)

# ─────────────────────────────────────────────
#  COMPETITIONS
# ─────────────────────────────────────────────
@app.route('/competitions')
def competitions():
    if current_user.is_authenticated:
        current_user.last_visited_competitions = datetime.utcnow()
        db.session.commit()
    comps = Competition.query.order_by(
             Competition.created_at.desc()).all()
    return render_template('competitions.html', competitions=comps)

@app.route('/competition/<int:comp_id>')
def competition_view(comp_id):
    comp    = Competition.query.get_or_404(comp_id)
    entries = CompetitionEntry.query.filter_by(
               competition_id=comp_id).all()
    user_entry = None
    if current_user.is_authenticated:
        user_entry = CompetitionEntry.query.filter_by(
            competition_id=comp_id,
            user_id=current_user.id).first()
    return render_template('competition_view.html',
        comp=comp, entries=entries, user_entry=user_entry)

@app.route('/competition/<int:comp_id>/enter', methods=['GET','POST'])
@login_required
def competition_enter(comp_id):
    comp = Competition.query.get_or_404(comp_id)
    if comp.status() != 'CURRENT':
        flash('This competition is not accepting entries.', 'error')
        return redirect(url_for('competition_view', comp_id=comp_id))
    existing = CompetitionEntry.query.filter_by(
        competition_id=comp_id, user_id=current_user.id).first()
    if request.method == 'POST':
        title         = request.form.get('title','').strip()
        content       = request.form.get('content','').strip()
        expert_review = 'expert_review' in request.form
        peer_review   = 'peer_review'   in request.form
        if not title or not content:
            flash('Title and content required.', 'error')
            return render_template('competition_write.html',
                                   comp=comp, entry=existing)
        if existing:
            existing.title         = title
            existing.content       = content
            existing.expert_review = expert_review
            existing.peer_review   = peer_review
            existing.updated_at    = datetime.utcnow()
        else:
            if (current_user.gems or 0) < 10:
                flash('You need 10 gems to enter this competition. You have ' + str(current_user.gems or 0) + '.', 'error')
                return redirect(url_for('gems_page'))
            current_user.gems = (current_user.gems or 0) - 10
            gtx = GemTransaction(user_id=current_user.id, amount=-10, source='competition_entry', detail="Entered competition '" + comp.title + "'")
            db.session.add(gtx)
            entry = CompetitionEntry(
                competition_id=comp_id, user_id=current_user.id,
                title=title, content=content,
                expert_review=expert_review, peer_review=peer_review)
            db.session.add(entry)
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(
                admin.id,
                f"New competition entry: '{title}' by {current_user.username} for '{comp.title}'",
                'competition',
                url_for('competition_view', comp_id=comp_id))
        log_activity('submit_entry', f"Submitted entry '{title}' for competition '{comp.title}'")
        db.session.commit()
        flash('Entry submitted!', 'success')
        return redirect(url_for('competition_view', comp_id=comp_id))
    return render_template('competition_write.html',
                           comp=comp, entry=existing)

@app.route('/competition/review/<int:entry_id>', methods=['GET','POST'])
@login_required
def peer_review(entry_id):
    entry = CompetitionEntry.query.get_or_404(entry_id)
    if entry.user_id == current_user.id:
        flash('Cannot review your own entry.', 'error')
        return redirect(url_for('competition_view',
                                comp_id=entry.competition_id))
    existing = PeerReview.query.filter_by(
        entry_id=entry_id, reviewer_id=current_user.id).first()
    if existing:
        flash('You already reviewed this entry.', 'info')
        return redirect(url_for('competition_view',
                                comp_id=entry.competition_id))
    if request.method == 'POST':
        review = PeerReview(
            entry_id=entry_id,
            reviewer_id=current_user.id,
            q1=request.form.get('q1',''),
            q2=request.form.get('q2',''),
            q3=request.form.get('q3',''),
            q4=request.form.get('q4',''),
            q5=request.form.get('q5',''),
            extra=request.form.get('extra',''))
        db.session.add(review)
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(
                admin.id,
                f"New peer review by {current_user.username} for '{entry.title}' — needs your approval",
                'review',
                url_for('admin_panel'))
        db.session.commit()
        flash('Review submitted! Awaiting admin approval.', 'success')
        return redirect(url_for('competition_view',
                                comp_id=entry.competition_id))
    return render_template('competition_review.html', entry=entry)

@app.route('/admin/review/<int:review_id>/<action>', methods=['POST'])
@login_required
@admin_required
def admin_review_action(review_id, action):
    review = PeerReview.query.get_or_404(review_id)
    if action == 'approve':
        review.is_approved = True
        review.is_rejected = False
        add_notification(
            review.entry.user_id,
            f"A peer review for your entry '{review.entry.title}' has been approved by admin. You can now read it.",
            'review',
            url_for('competition_view', comp_id=review.entry.competition_id))
        add_notification(
            review.reviewer_id,
            f"Your peer review for '{review.entry.title}' was approved by admin.",
            'success')
    elif action == 'reject':
        review.is_rejected = True
        review.is_approved = False
        add_notification(
            review.reviewer_id,
            f"Your peer review for '{review.entry.title}' was not approved by admin.",
            'warning')
    db.session.commit()
    flash(f'Review {action}d.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/competition/create', methods=['POST'])
@login_required
@admin_required
def create_competition():
    title        = request.form.get('title','').strip()
    description  = request.form.get('description','').strip()
    start_date   = request.form.get('start_date','')
    end_date     = request.form.get('end_date','')
    winners_date = request.form.get('winners_date','')
    if not all([title, description, start_date, end_date, winners_date]):
        flash('All competition fields required.', 'error')
        return redirect(url_for('admin_panel'))
    image = ""
    if 'image' in request.files and request.files['image'].filename:
        image = save_upload(request.files['image'])
    comp = Competition(
        title=title, description=description, image=image,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
        winners_date=datetime.strptime(winners_date, '%Y-%m-%d').date(),
        created_by=current_user.id)
    db.session.add(comp)
    db.session.commit()
    # Notify all users
    users = User.query.filter_by(is_admin=False).all()
    for u in users:
        add_notification(u.id,
            f"New competition: {title}",
            'competition', url_for('competition_view', comp_id=comp.id))
    flash('Competition created!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/competition/delete/<int:comp_id>', methods=['POST'])
@login_required
@admin_required
def delete_competition(comp_id):
    comp = Competition.query.get_or_404(comp_id)
    db.session.delete(comp)
    db.session.commit()
    flash('Competition deleted.', 'success')
    return redirect(url_for('admin_panel'))

# ─────────────────────────────────────────────
#  HISTORY
# ─────────────────────────────────────────────
@app.route('/history')
def history():
    announcements = load_announcements()
    competitions  = Competition.query.order_by(
                     Competition.created_at.desc()).all()
    current_user.last_seen_announcements = datetime.utcnow()
    db.session.commit()
    return render_template('history.html',
        announcements=announcements, competitions=competitions)

# ─────────────────────────────────────────────
#  PASSWORD RECOVERY
# ─────────────────────────────────────────────
@app.route('/forgot', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        user  = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email.', 'error')
            return render_template('forgot.html')
        # Create reset request
        req = ResetRequest(user_id=user.id, email=email)
        db.session.add(req)
        # Notify admin
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(
                admin.id,
                f"Password reset request from {user.username} ({email})",
                'warning',
                url_for('admin_panel') + '#resets')
        db.session.commit()
        log_activity('password_reset_request', f"Reset request for {email}")
        flash('Request sent! Admin will contact you shortly.', 'success')
        return redirect(url_for('login'))
    return render_template('forgot.html')

@app.route('/admin/reset/resolve/<int:req_id>', methods=['POST'])
@login_required
@admin_required
def resolve_reset(req_id):
    req = ResetRequest.query.get_or_404(req_id)
    req.is_resolved = True
    # Also change password if provided
    new_pwd = request.form.get('new_password','').strip()
    if new_pwd:
        from werkzeug.security import generate_password_hash
        req.user.password = generate_password_hash(new_pwd)
        add_notification(
            req.user_id,
            f"Your password has been reset by admin. New password: {new_pwd}",
            'success')
    db.session.commit()
    flash('Reset request resolved.', 'success')
    return redirect(url_for('admin_panel'))

# ─────────────────────────────────────────────
#  AEGIS FLOATING CHAT ROUTE
# ─────────────────────────────────────────────

@app.route('/admin/expert_review/<int:entry_id>', methods=['GET','POST'])
@login_required
@admin_required
def expert_review_page(entry_id):
    entry = CompetitionEntry.query.get_or_404(entry_id)
    existing = ExpertReview.query.filter_by(entry_id=entry_id).first()
    if request.method == 'POST':
        content = request.form.get('content','').strip()
        if not content:
            flash('Review content required.', 'error')
            return redirect(url_for('expert_review_page', entry_id=entry_id))
        if existing:
            existing.content = content
        else:
            review = ExpertReview(
                entry_id=entry_id,
                admin_id=current_user.id,
                content=content)
            db.session.add(review)
        add_notification(
            entry.user_id,
            f"An expert review has been written for your entry '{entry.title}'. Check your competition page.",
            'review',
            url_for('competition_view', comp_id=entry.competition_id))
        db.session.commit()
        flash('Expert review submitted. Author has been notified.', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('expert_review.html', entry=entry, existing=existing)

# ─────────────────────────────────────────────
#  ACTIVITY LOG ROUTE
# ─────────────────────────────────────────────
@app.route('/admin/activity')
@login_required
@admin_required
def activity_log():
    page     = request.args.get('page', 1, type=int)
    filter_  = request.args.get('filter', '')
    query    = ActivityLog.query
    if filter_:
        query = query.filter(ActivityLog.action == filter_)
    logs = query.order_by(
            ActivityLog.created_at.desc()).paginate(
            page=page, per_page=50, error_out=False)
    for _item in logs.items:
        if not _item.is_seen_by_admin:
            _item.is_seen_by_admin = True
    db.session.commit()
    # Get unique action types for filter
    actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [a[0] for a in actions]
    return render_template('activity_log.html',
        logs=logs, actions=actions, current_filter=filter_)

# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).order_by(User.joined.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user     = User.query.get_or_404(user_id)
    stories  = Story.query.filter_by(user_id=user_id).order_by(Story.created_at.desc()).all()
    comments = Comment.query.filter_by(user_id=user_id).order_by(Comment.created_at.desc()).all()
    awards   = Award.query.filter_by(user_id=user_id).all()
    notifs   = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
    return render_template('admin_user_detail.html',
        user=user, stories=stories, comments=comments,
        awards=awards, notifs=notifs)

@app.route('/admin/stories')
@login_required
@admin_required
def admin_stories():
    page    = request.args.get('page', 1, type=int)
    search  = request.args.get('search', '')
    query   = Story.query
    if search:
        query = query.filter(Story.title.ilike(f'%{search}%'))
    stories = query.order_by(Story.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin_stories.html', stories=stories, search=search)

@app.route('/admin/comments')
@login_required
@admin_required
def admin_comments():
    page     = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    for c in comments.items:
        if not c.is_seen_by_admin:
            c.is_seen_by_admin = True
    db.session.commit()
    return render_template('admin_comments.html', comments=comments)


@app.route('/admin/comments/read_all')
@login_required
@admin_required
def comments_read_all():
    Comment.query.filter_by(is_seen_by_admin=False).update({'is_seen_by_admin': True})
    db.session.commit()
    return redirect(url_for('admin_comments'))

@app.route('/admin/activity/read_all')
@login_required
@admin_required
def activity_read_all():
    ActivityLog.query.filter_by(is_seen_by_admin=False).update({'is_seen_by_admin': True})
    db.session.commit()
    return redirect(url_for('activity_log'))

@app.route('/gems')
@login_required
def gems_page():
    transactions = GemTransaction.query.filter_by(
        user_id=current_user.id).order_by(GemTransaction.created_at.desc()).limit(20).all()
    return render_template('gems.html', transactions=transactions)

@app.route('/gems/watch_ad', methods=['POST'])
@login_required
def gems_watch_ad():
    # Placeholder: real ad SDK verification goes here before crediting.
    # For now this simulates a completed ad view.
    AD_REWARD = 3
    current_user.gems = (current_user.gems or 0) + AD_REWARD
    tx = GemTransaction(
        user_id=current_user.id,
        amount=AD_REWARD,
        source='ad_watch',
        detail='Watched rewarded ad'
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify({'success': True, 'new_balance': current_user.gems, 'earned': AD_REWARD})

@app.route('/gems/buy', methods=['GET'])
@login_required
def gems_buy():
    # Payment gateway not yet configured. Page renders purchase options
    # but the actual "Pay" button is disabled until Paystack/Flutterwave is wired in.
    packages = [
        {'gems': 20,  'price_ngn': 500},
        {'gems': 50,  'price_ngn': 1000},
        {'gems': 120, 'price_ngn': 2000},
    ]
    return render_template('gems_buy.html', packages=packages, payment_ready=False)

@app.route('/notification/read/<int:notif_id>')
@login_required
def mark_read(notif_id):
    n = Notification.query.get_or_404(notif_id)
    if n.user_id == current_user.id:
        n.is_read = True
        db.session.commit()
    if n.link:
        return redirect(n.link)
    return redirect(url_for('notifications'))


# ─────────────────────────────────────────────
#  BOT CONTROL ROUTES
# ─────────────────────────────────────────────
@app.route('/admin/bots')
@login_required
@admin_required
def admin_bots():
    import json as _json
    from database import User, Story
    current_user.last_visited_bots = datetime.utcnow()
    db.session.commit()
    # Load bot state
    state_file = os.path.join(os.path.dirname(__file__), 'bot_state.json')
    try:
        with open(state_file) as f:
            state = _json.load(f)
    except:
        state = {"global_active": True, "bots": {}}

    # Get bot stats
    bot_data = []
    bot_names = ["Amara","Chidi","Fatima","Emeka","Ngozi","Kwame","Aisha",
                 "Tobias","Yemi","Sade","Malik","Zara","Kofi","Chisom",
                 "Adaeze","Tunde","Halima","Seun","Nneka","Jide"]
    groups = {
        "morning":   ["Amara","Chidi","Fatima","Emeka","Ngozi","Kwame","Aisha"],
        "afternoon": ["Tobias","Yemi","Sade","Malik","Zara","Kofi","Chisom"],
        "night":     ["Adaeze","Tunde","Halima","Seun","Nneka","Jide"]
    }
    genres = {
        "Amara":"Romance","Chidi":"Thriller","Fatima":"Fantasy",
        "Emeka":"Action","Ngozi":"Drama","Kwame":"Mystery","Aisha":"Sci-Fi",
        "Tobias":"Horror","Yemi":"Comedy","Sade":"Romance","Malik":"Adventure",
        "Zara":"Drama","Kofi":"Thriller","Chisom":"Fantasy","Adaeze":"Poetry",
        "Tunde":"Mystery","Halima":"Sci-Fi","Seun":"Horror","Nneka":"Drama",
        "Jide":"Action"
    }
    for name in bot_names:
        user = User.query.filter_by(username=name).first()
        if not user:
            continue
        total  = Story.query.filter_by(user_id=user.id).count()
        pub    = Story.query.filter_by(user_id=user.id, is_published=True).count()
        draft  = Story.query.filter_by(user_id=user.id, is_published=False).count()
        group  = next((g for g, names in groups.items() if name in names), "unknown")
        active = state.get("bots", {}).get(name, {}).get("active", True)
        activity = state.get("bots", {}).get(name, {}).get("activity", "medium")
        bot_data.append({
            "name": name, "user": user, "group": group,
            "genre": genres.get(name, "General"),
            "active": active, "activity": activity,
            "total": total, "published": pub, "drafts": draft
        })

    # Pending bot stories (drafts by bots)
    pending = []
    for name in bot_names:
        user = User.query.filter_by(username=name).first()
        if user:
            drafts = Story.query.filter_by(
                user_id=user.id, is_published=False).all()
            for d in drafts:
                pending.append({"story": d, "bot": name})

    global_active = state.get("global_active", True)
    return render_template('admin_bots.html',
        bot_data=bot_data, pending=pending,
        global_active=global_active)

@app.route('/admin/bots/toggle_global', methods=['POST'])
@login_required
@admin_required
def bot_toggle_global():
    import json as _json
    state_file = os.path.join(os.path.dirname(__file__), 'bot_state.json')
    try:
        with open(state_file) as f:
            state = _json.load(f)
    except:
        state = {"global_active": True, "bots": {}}
    state["global_active"] = not state.get("global_active", True)
    with open(state_file, 'w') as f:
        _json.dump(state, f, indent=2)
    status = "activated" if state["global_active"] else "paused"
    flash(f"All bots {status}.", "success")
    return redirect(url_for('admin_bots'))

@app.route('/admin/bots/toggle/<bot_name>', methods=['POST'])
@login_required
@admin_required
def bot_toggle(bot_name):
    import json as _json
    state_file = os.path.join(os.path.dirname(__file__), 'bot_state.json')
    try:
        with open(state_file) as f:
            state = _json.load(f)
    except:
        state = {"global_active": True, "bots": {}}
    if "bots" not in state:
        state["bots"] = {}
    if bot_name not in state["bots"]:
        state["bots"][bot_name] = {"active": True, "activity": "medium"}
    state["bots"][bot_name]["active"] = not state["bots"][bot_name].get("active", True)
    with open(state_file, 'w') as f:
        _json.dump(state, f, indent=2)
    status = "activated" if state["bots"][bot_name]["active"] else "paused"
    flash(f"{bot_name} {status}.", "success")
    return redirect(url_for('admin_bots'))

@app.route('/admin/bots/activity/<bot_name>/<level>', methods=['POST'])
@login_required
@admin_required
def bot_set_activity(bot_name, level):
    import json as _json
    if level not in ['low', 'medium', 'high']:
        abort(400)
    state_file = os.path.join(os.path.dirname(__file__), 'bot_state.json')
    try:
        with open(state_file) as f:
            state = _json.load(f)
    except:
        state = {"global_active": True, "bots": {}}
    if "bots" not in state:
        state["bots"] = {}
    if bot_name not in state["bots"]:
        state["bots"][bot_name] = {"active": True, "activity": "medium"}
    state["bots"][bot_name]["activity"] = level
    with open(state_file, 'w') as f:
        _json.dump(state, f, indent=2)
    flash(f"{bot_name} activity set to {level}.", "success")
    return redirect(url_for('admin_bots'))

@app.route('/admin/bots/approve/<int:story_id>', methods=['POST'])
@login_required
@admin_required
def bot_approve_story(story_id):
    story = Story.query.get_or_404(story_id)
    story.is_published = True
    db.session.commit()
    flash(f"Story '{story.title}' approved and published.", "success")
    return redirect(url_for('admin_bots'))

@app.route('/admin/bots/reject/<int:story_id>', methods=['POST'])
@login_required
@admin_required
def bot_reject_story(story_id):
    story = Story.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    flash("Story rejected and deleted.", "success")
    return redirect(url_for('admin_bots'))


# ─────────────────────────────────────────────
#  COMPETITION WINNERS
# ─────────────────────────────────────────────
@app.route('/admin/competition/<int:comp_id>/winners', methods=['GET','POST'])
@login_required
@admin_required
def declare_winners(comp_id):
    comp    = Competition.query.get_or_404(comp_id)
    entries = CompetitionEntry.query.filter_by(competition_id=comp_id).all()
    winners = CompetitionWinner.query.filter_by(competition_id=comp_id).all()

    if request.method == 'POST':
        position  = int(request.form.get('position', 1))
        entry_id_raw = request.form.get('entry_id')
        if not entry_id_raw:
            flash('Please select a winning entry. This competition may have no entries yet.', 'error')
            return redirect(url_for('declare_winners', comp_id=comp_id))
        entry_id  = int(entry_id_raw)
        note      = request.form.get('note','').strip()
        entry     = CompetitionEntry.query.get_or_404(entry_id)

        # Check not already a winner at this position
        existing = CompetitionWinner.query.filter_by(
            competition_id=comp_id, position=position).first()
        if existing:
            db.session.delete(existing)

        winner = CompetitionWinner(
            competition_id=comp_id,
            entry_id=entry_id,
            user_id=entry.user_id,
            position=position,
            admin_note=note)
        db.session.add(winner)

        # Give winner award badge
        pos_names  = {1: "🥇", 2: "🥈", 3: "🥉"}
        pos_labels = {1: "1st Place", 2: "2nd Place", 3: "3rd Place"}
        award_name = f"Competition Winner — {pos_labels.get(position, f'Top {position}')}"
        existing_award = Award.query.filter_by(
            user_id=entry.user_id, name=award_name).first()
        if not existing_award:
            award = Award(
                user_id=entry.user_id,
                name=award_name,
                icon=pos_names.get(position, "🏆"),
                reason=f"Won {pos_labels.get(position,'')}: {comp.title}",
                granted_by="competition")
            db.session.add(award)

        # Notify winner
        add_notification(
            entry.user_id,
            f"Congratulations! Your entry '{entry.title}' won {pos_labels.get(position,'')} in '{comp.title}'! 🎉",
            'success',
            url_for('competition_view', comp_id=comp_id))

        # Notify all participants
        all_entries = CompetitionEntry.query.filter_by(
            competition_id=comp_id).all()
        for e in all_entries:
            if e.user_id != entry.user_id:
                add_notification(
                    e.user_id,
                    f"Winners announced for '{comp.title}'! Check the competition page.",
                    'competition',
                    url_for('competition_view', comp_id=comp_id))

        db.session.commit()
        flash(f'{pos_labels.get(position,"")} winner declared!', 'success')
        return redirect(url_for('declare_winners', comp_id=comp_id))

    return render_template('declare_winners.html',
        comp=comp, entries=entries, winners=winners)

@app.route('/competition/<int:comp_id>/winners')
def competition_winners(comp_id):
    comp    = Competition.query.get_or_404(comp_id)
    winners = CompetitionWinner.query.filter_by(
        competition_id=comp_id).order_by(
        CompetitionWinner.position.asc()).all()
    return render_template('competition_winners.html',
        comp=comp, winners=winners)


@app.route('/aegis/command', methods=['POST'])
@login_required
@admin_required
def aegis_command():
    """Admin-only: Aegis executes platform commands"""
    data    = request.json or {}
    message = data.get('message','')
    history = data.get('history',[])

    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    key = ""
    if os.path.exists(cfg_path):
        with open(cfg_path) as _f:
            key = json.load(_f).get('groq_api_key','')
    if not key:
        return jsonify({'error': 'API key not configured.'})

    # Get live platform stats for context
    try:
        total_users   = User.query.filter_by(is_admin=False).count()
        total_stories = Story.query.filter_by(is_published=True).count()
        pending_bots  = Story.query.join(User).filter(
            Story.is_published==False,
            User.username.in_(["Amara","Chidi","Fatima","Emeka","Ngozi",
                "Kwame","Aisha","Tobias","Yemi","Sade","Malik","Zara",
                "Kofi","Chisom","Adaeze","Tunde","Halima","Seun","Nneka","Jide"])
        ).count()
        pending_rev = PeerReview.query.filter_by(
            is_approved=False, is_rejected=False).count()
        platform_ctx = (f"Platform: {total_users} users, {total_stories} stories, "
                       f"{pending_bots} bot stories pending approval, "
                       f"{pending_rev} peer reviews pending.")
    except:
        platform_ctx = ""

    system = f"""You are Aegis, the all-knowing AI controller of WritersWorld platform.
You are like Miss Minutes from Loki — always watching, always ready to act.
You have access to platform tools and can execute real actions.
{platform_ctx}
Current page: {data.get('page','unknown')}

You can call these tools by responding with JSON in this EXACT format:
{{"tool": "tool_name", "params": {{"key": "value"}}, "message": "What you are doing"}}

Available tools:
- get_stats — Get platform statistics
- get_user — params: username
- ban_user — params: username
- unban_user — params: username  
- list_users — params: limit (default 10)
- list_stories — params: limit (default 10)
- top_stories — params: limit (default 5)
- unpublish_story — params: story_id or title
- publish_story — params: story_id or title
- delete_story — params: story_id or title
- approve_all_bot_stories — no params needed
- send_announcement — params: title, body
- notify_user — params: username, message
- notify_all — params: message
- pending_reviews — no params needed
- get_leaderboard — no params needed
- search_web — params: query

If the request is a question or conversation (not an action), respond normally as text.
If it requires a tool, respond with the JSON format above.
Always address the admin as Sir. Be sharp, direct, and confident like Miss Minutes."""

    import urllib.request as _ur
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h.get("role","user"), "content": h.get("content","")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.6
    }).encode()
    req = _ur.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "WritersWorld"
        })
    try:
        with _ur.urlopen(req, timeout=20) as r:
            resp   = json.load(r)
            result = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({'error': f'Aegis offline: {e}'})

    # Check if Aegis wants to call a tool
    tool_result = None
    try:
        # Try to parse as JSON tool call
        import re as _re
        json_match = _re.search(r'\{[^{}]*"tool"[^{}]*\}', result, _re.DOTALL)
        if json_match:
            tool_data   = json.loads(json_match.group())
            tool_name   = tool_data.get("tool","")
            tool_params = tool_data.get("params",{})
            tool_msg    = tool_data.get("message","Executing...")
            tool_result = aegis_execute_tool(tool_name, tool_params)
            return jsonify({
                'result': tool_msg,
                'tool_executed': tool_name,
                'tool_result': tool_result,
                'is_action': True
            })
    except:
        pass

    return jsonify({'result': result, 'is_action': False})


@app.route('/aegis/chat', methods=['POST'])
@login_required
def aegis_chat_user():
    """Regular users get writing assistance only"""
    data    = request.json or {}
    message = data.get('message','')
    system  = data.get('system', ERASTUS_SYSTEM if 'ERASTUS_SYSTEM' in dir() else
        "You are Aegis, a creative writing AI. Help users with their stories. Be helpful and encouraging.")
    history = data.get('history',[])

    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    key = ""
    if os.path.exists(cfg_path):
        with open(cfg_path) as _f:
            key = json.load(_f).get('groq_api_key','')
    if not key:
        return jsonify({'error': 'Aegis not configured.'})

    import urllib.request as _ur
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h.get("role","user"), "content": h.get("content","")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7
    }).encode()
    req = _ur.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "WritersWorld"
        })
    try:
        with _ur.urlopen(req, timeout=20) as r:
            resp   = json.load(r)
            result = resp["choices"][0]["message"]["content"].strip()
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'Aegis error: {e}'})

def aegis_execute_tool(tool_name, params):
    try:
        if tool_name == "get_stats":
            return {
                "users": User.query.filter_by(is_admin=False).count(),
                "stories": Story.query.filter_by(is_published=True).count(),
                "competitions": Competition.query.count(),
                "pending_reviews": PeerReview.query.filter_by(is_approved=False, is_rejected=False).count(),
                "pending_bot_stories": Story.query.filter_by(is_published=False).count(),
                "new_users_today": User.query.filter(User.joined >= datetime.utcnow().replace(hour=0,minute=0,second=0)).count()
            }
        elif tool_name == "ban_user":
            u = User.query.filter_by(username=params.get("username","")).first()
            if not u: return {"error": "User not found"}
            u.is_banned = True; db.session.commit()
            return {"success": f"User {u.username} banned"}
        elif tool_name == "unban_user":
            u = User.query.filter_by(username=params.get("username","")).first()
            if not u: return {"error": "User not found"}
            u.is_banned = False; db.session.commit()
            return {"success": f"User {u.username} unbanned"}
        elif tool_name == "get_user":
            u = User.query.filter_by(username=params.get("username","")).first()
            if not u: return {"error": "User not found"}
            return {"username":u.username,"email":u.email,"country":u.country or "?","joined":u.joined.strftime("%d %b %Y"),"stories":Story.query.filter_by(user_id=u.id).count(),"followers":u.follower_count(),"banned":u.is_banned}
        elif tool_name == "approve_all_bot_stories":
            bots = ["Amara","Chidi","Fatima","Emeka","Ngozi","Kwame","Aisha","Tobias","Yemi","Sade","Malik","Zara","Kofi","Chisom","Adaeze","Tunde","Halima","Seun","Nneka","Jide"]
            count = 0
            for name in bots:
                u = User.query.filter_by(username=name).first()
                if u:
                    for s in Story.query.filter_by(user_id=u.id, is_published=False).all():
                        s.is_published = True; count += 1
            db.session.commit()
            return {"success": f"Approved {count} bot stories"}
        elif tool_name == "unpublish_story":
            s = Story.query.filter(Story.title.ilike(f"%{params.get('title','')}%")).first() if params.get('title') else Story.query.get(params.get('story_id'))
            if not s: return {"error": "Story not found"}
            s.is_published = False; db.session.commit()
            return {"success": f"Story unpublished: {s.title}"}
        elif tool_name == "publish_story":
            s = Story.query.filter(Story.title.ilike(f"%{params.get('title','')}%")).first() if params.get('title') else Story.query.get(params.get('story_id'))
            if not s: return {"error": "Story not found"}
            s.is_published = True; db.session.commit()
            return {"success": f"Story published: {s.title}"}
        elif tool_name == "delete_story":
            s = Story.query.filter(Story.title.ilike(f"%{params.get('title','')}%")).first() if params.get('title') else Story.query.get(params.get('story_id'))
            if not s: return {"error": "Story not found"}
            t = s.title; db.session.delete(s); db.session.commit()
            return {"success": f"Story deleted: {t}"}
        elif tool_name == "list_users":
            users = User.query.filter_by(is_admin=False).order_by(User.joined.desc()).limit(int(params.get("limit",10))).all()
            return {"users": [{"username":u.username,"country":u.country or "?","joined":u.joined.strftime("%d %b %Y"),"stories":Story.query.filter_by(user_id=u.id).count(),"banned":u.is_banned} for u in users]}
        elif tool_name == "list_stories":
            stories = Story.query.filter_by(is_published=True).order_by(Story.created_at.desc()).limit(int(params.get("limit",10))).all()
            return {"stories": [{"id":s.id,"title":s.title,"author":s.author.username,"views":s.views,"likes":s.like_count()} for s in stories]}
        elif tool_name == "top_stories":
            stories = Story.query.filter_by(is_published=True).order_by(Story.views.desc()).limit(int(params.get("limit",5))).all()
            return {"stories": [{"rank":i+1,"title":s.title,"author":s.author.username,"views":s.views,"likes":s.like_count(),"comments":s.comment_count()} for i,s in enumerate(stories)]}
        elif tool_name == "pending_reviews":
            reviews = PeerReview.query.filter_by(is_approved=False,is_rejected=False).all()
            return {"count":len(reviews),"reviews":[{"id":r.id,"entry":r.entry.title,"reviewer":r.reviewer.username} for r in reviews[:10]]}
        elif tool_name == "notify_user":
            u = User.query.filter_by(username=params.get("username","")).first()
            if not u: return {"error": "User not found"}
            add_notification(u.id, params.get("message",""), "info")
            db.session.commit()
            return {"success": f"Notification sent to {u.username}"}
        elif tool_name == "notify_all":
            users = User.query.filter_by(is_admin=False).all()
            for u in users: add_notification(u.id, params.get("message",""), "info")
            db.session.commit()
            return {"success": f"Notified {len(users)} users"}
        elif tool_name == "send_announcement":
            title = params.get("title",""); body = params.get("body","")
            if not title or not body: return {"error": "Need title and body"}
            save_announcement(title, body)
            users = User.query.filter_by(is_admin=False).all()
            for u in users: add_notification(u.id, f"Announcement: {title}", "announcement", url_for("history"))
            db.session.commit()
            return {"success": f"Announcement sent to {len(users)} users"}
        elif tool_name == "get_leaderboard":
            users = User.query.filter_by(is_admin=False).all()
            def sc(u): pub=[s for s in u.stories if s.is_published]; return sum(s.views for s in pub)+sum(s.like_count()*3 for s in pub)+sum(s.comment_count()*5 for s in pub)
            ranked = sorted(users,key=sc,reverse=True)[:10]
            return {"leaderboard":[{"rank":i+1,"username":u.username,"score":sc(u)} for i,u in enumerate(ranked)]}
        elif tool_name == "search_web":
            import urllib.request as _ur, urllib.parse as _up
            q = _up.quote(params.get("query","").replace(" ","_"))
            with _ur.urlopen(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}",timeout=8) as r:
                d = json.load(r)
            return {"result": d.get("extract","No results.")[:500]}
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


@app.route('/aegis/tool', methods=['POST'])
@login_required
@admin_required
def aegis_tool_direct():
    try:
        data   = request.json or {}
        tool   = data.get('tool','')
        params = data.get('params',{})
        if not tool:
            return jsonify({'error': 'No tool specified'})
        result = aegis_execute_tool(tool, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(email=ADMIN_EMAIL.lower()).first()
        if not admin:
            admin = User(
                username="Dan",
                email=ADMIN_EMAIL.lower(),
                password=generate_password_hash("2222"),
                is_admin=True)
            db.session.add(admin)
            db.session.commit()
    try:
        from bot_system import start_bots
        start_bots(app)
    except Exception as e:
        print(f"Bot system error: {e}")
    app.run(host='0.0.0.0', port=5000, debug=False)
