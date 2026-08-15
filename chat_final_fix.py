#!/usr/bin/env python3
import os

APP  = os.path.expanduser("~/writersworld/app.py")
CHAT = os.path.expanduser("~/writersworld/templates/chat.html")

with open(APP) as f:
    app = f.read()

patches = 0

old1 = '''@app.route('/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        abort(403)
    user     = User.query.get_or_404(user_id)
    messages = AdminMessage.query.filter(
        ((AdminMessage.admin_id == current_user.id) &
         (AdminMessage.user_id  == user_id)) |
        ((AdminMessage.admin_id == user_id) &
         (AdminMessage.user_id  == current_user.id))
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
    return render_template('chat.html', user=user, messages=messages)'''

new1 = '''@app.route('/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):
    admin_user = User.query.filter_by(is_admin=True).first()
    admin_id   = admin_user.id if admin_user else 0

    if current_user.is_admin:
        other_user = User.query.get_or_404(user_id)
        uid_b = user_id
    else:
        other_user = admin_user
        uid_b = current_user.id

    messages = AdminMessage.query.filter_by(
        admin_id=admin_id, user_id=uid_b
    ).order_by(AdminMessage.created_at.asc()).all()

    if request.method == 'POST':
        content = request.form.get('message','').strip()
        if content:
            if current_user.is_admin:
                msg = AdminMessage(
                    admin_id=admin_id, user_id=uid_b,
                    message=content, is_reply=False)
                notify_target = uid_b
                sender_name   = "Admin"
                chat_link     = url_for('chat', user_id=admin_id)
            else:
                msg = AdminMessage(
                    admin_id=admin_id, user_id=current_user.id,
                    message=content, is_reply=True)
                notify_target = admin_id
                sender_name   = current_user.username
                chat_link     = url_for('chat', user_id=current_user.id)
            db.session.add(msg)
            add_notification(notify_target,
                f"You have a new message from {sender_name}",
                'message', chat_link)
            db.session.commit()
        return redirect(url_for('chat', user_id=user_id))
    return render_template('chat.html',
        user=other_user, messages=messages, admin_id=admin_id)'''

if old1 in app:
    app = app.replace(old1, new1)
    patches += 1
    print("Chat route fixed")
else:
    print("Pattern not found — check app.py chat route manually")

with open(APP, 'w') as f:
    f.write(app)

new_chat = '''{% extends "base.html" %}
{% block title %}Messages — WritersWorld{% endblock %}
{% block page_title %}Messages{% endblock %}
{% block content %}
<div style="max-width:600px; margin:0 auto;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:8px;">
    <h3 style="color:var(--green);">💬 Chat with {{ user.username }}</h3>
    <a href="{{ url_for('admin_panel') if current_user.is_admin else url_for('notifications') }}" class="btn btn-gray btn-sm">← Back</a>
  </div>
  <div id="chatBox" style="min-height:200px; max-height:55vh; overflow-y:auto; display:flex; flex-direction:column; gap:12px; padding:12px; background:var(--dark); border-radius:10px; border:1px solid var(--border); margin-bottom:16px;">
    {% if messages %}
      {% for msg in messages %}
        {% if current_user.is_admin %}
          {% set is_mine = not msg.is_reply %}
        {% else %}
          {% set is_mine = msg.is_reply %}
        {% endif %}
        <div style="display:flex; flex-direction:column; align-items:{% if is_mine %}flex-end{% else %}flex-start{% endif %};">
          <div style="font-size:0.7rem; color:var(--text-dim); margin-bottom:3px; {% if is_mine %}text-align:right;{% endif %}">
            {% if is_mine %}You{% else %}{% if current_user.is_admin %}{{ user.username }}{% else %}Admin{% endif %}{% endif %}
            · {{ msg.created_at.strftime('%d %b %H:%M') }}
          </div>
          <div style="max-width:82%; padding:10px 14px; word-wrap:break-word; font-size:0.9rem; line-height:1.5; border-radius:{% if is_mine %}14px 14px 4px 14px{% else %}14px 14px 14px 4px{% endif %}; {% if is_mine %}background:var(--green-dark); color:var(--green); border:1px solid var(--green);{% else %}background:var(--card); color:var(--text); border:1px solid var(--border);{% endif %}">
            {{ msg.message }}
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div style="text-align:center; padding:30px; color:var(--text-dim); font-size:0.88rem;">No messages yet.</div>
    {% endif %}
  </div>
  <form method="POST" style="display:flex; gap:10px; align-items:flex-end;">
    <textarea name="message" placeholder="Type your message..." style="flex:1; background:var(--card); border:1px solid var(--border); color:var(--text); padding:10px 14px; border-radius:8px; resize:none; height:72px; outline:none; font-family:inherit; font-size:0.9rem;" required></textarea>
    <button type="submit" class="btn btn-green" style="height:44px; padding:0 22px;">Send ➤</button>
  </form>
</div>
<script>
  var box = document.getElementById('chatBox');
  if (box) box.scrollTop = box.scrollHeight;
</script>
{% endblock %}'''

with open(CHAT, 'w') as f:
    f.write(new_chat)
patches += 1
print("Chat template rewritten")
print(f"Done. {patches} fixes applied.")
