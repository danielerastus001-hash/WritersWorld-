import os, re

APP  = os.path.expanduser("~/writersworld/app.py")
BASE = os.path.expanduser("~/writersworld/templates/base.html")
ADM  = os.path.expanduser("~/writersworld/templates/admin.html")

with open(APP) as f:
    app = f.read()

old = '# ─────────────────────────────────────────────\n#  ACTIVITY LOG ROUTE'

new = '''# ─────────────────────────────────────────────
#  ADMIN SEPARATE PAGES
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
    return render_template('admin_comments.html', comments=comments)

# ─────────────────────────────────────────────
#  ACTIVITY LOG ROUTE'''

if old in app:
    app = app.replace(old, new)
    print("Routes added")
else:
    print("Pattern not found")

with open(APP, 'w') as f:
    f.write(app)

# Add sidebar links
with open(BASE) as f:
    base = f.read()

old2 = "<a href=\"{{ url_for('admin_panel') }}\" class=\"admin-link\">⚡ Control Centre</a>"
new2 = """<a href="{{ url_for('admin_panel') }}" class="admin-link">⚡ Control Centre</a>
      <a href="{{ url_for('admin_users') }}" style="color:#ff8866;font-size:0.85rem;padding-left:28px;border-left:3px solid #ff8866;">👥 All Users</a>
      <a href="{{ url_for('admin_stories') }}" style="color:#ff8866;font-size:0.85rem;padding-left:28px;border-left:3px solid #ff8866;">📚 All Stories</a>
      <a href="{{ url_for('admin_comments') }}" style="color:#ff8866;font-size:0.85rem;padding-left:28px;border-left:3px solid #ff8866;">💬 All Comments</a>
      <a href="{{ url_for('activity_log') }}" style="color:#ff8866;font-size:0.85rem;padding-left:28px;border-left:3px solid #ff8866;">📋 Activity Log</a>"""

if old2 in base:
    base = base.replace(old2, new2)
    with open(BASE, 'w') as f:
        f.write(base)
    print("Sidebar links added")
else:
    print("Sidebar pattern not found")

print("Done")
