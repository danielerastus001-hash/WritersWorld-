#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  MEGA FIX — Chat, Notifications, Aegis,
#  Awards, Leaderboard
# ─────────────────────────────────────────────

import os

APP  = os.path.expanduser("~/writersworld/app.py")
CHAT = os.path.expanduser("~/writersworld/templates/chat.html")
LEAD = os.path.expanduser("~/writersworld/templates/leaderboard.html")

with open(APP) as f:
    app = f.read()

patches = 0

# ── 1. Fix chat route — show messages from BOTH sides ──
old1 = '''    messages = AdminMessage.query.filter(
        ((AdminMessage.admin_id == current_user.id) &
         (AdminMessage.user_id  == user_id)) |
        ((AdminMessage.admin_id == user_id) &
         (AdminMessage.user_id  == current_user.id))
    ).order_by(AdminMessage.created_at.asc()).all()'''

new1 = '''    admin_user = User.query.filter_by(is_admin=True).first()
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
    ).order_by(AdminMessage.created_at.asc()).all()'''

if old1 in app:
    app = app.replace(old1, new1)
    patches += 1
    print("✓ Chat messages fixed — both sides visible")
else:
    print("✗ Chat query pattern not found")

# ── 2. Fix notification message — say "Admin" not "Dan" ──
old2 = '''        notify_id = user_id if current_user.is_admin else \
                        User.query.filter_by(is_admin=True).first().id
            add_notification(notify_id,
                f"New message from {current_user.username}",
                'message', url_for('chat', user_id=user_id))'''

new2 = '''        notify_id = user_id if current_user.is_admin else \
                        User.query.filter_by(is_admin=True).first().id
            sender_name = "Admin" if current_user.is_admin else current_user.username
            add_notification(notify_id,
                f"You have a new message from {sender_name}",
                'message', url_for('chat', user_id=user_id if current_user.is_admin else current_user.id))'''

if old2 in app:
    app = app.replace(old2, new2)
    patches += 1
    print("✓ Notification shows 'Admin' not username")
else:
    print("✗ Notification pattern not found")

# ── 3. Fix Aegis — unique ideas every time ──
old3 = '''@app.route('/aegis/idea', methods=['POST'])
@login_required
def aegis_idea():
    genre  = request.json.get('genre','General')
    result, error = ask_aegis(
        f"Generate a professional story idea for the {genre} genre. "
        f"Include: Title, Plot Summary, Main Character, Plot Twist, "
        f"Opening Line. Make it compelling and original.")
    if error:
        return jsonify({'error': error})
    return jsonify({'result': result})'''

new3 = '''@app.route('/aegis/idea', methods=['POST'])
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
    return jsonify({'result': result})'''

if old3 in app:
    app = app.replace(old3, new3)
    patches += 1
    print("✓ Aegis now generates unique ideas every time")
else:
    print("✗ Aegis idea pattern not found")

with open(APP, 'w') as f:
    f.write(app)

# ── 4. Fix leaderboard — top 10 with gem ranks ──
new_leaderboard = '''{% extends "base.html" %}
{% block title %}Leaderboard — WritersWorld{% endblock %}
{% block page_title %}Leaderboard{% endblock %}
{% block content %}

{% set rank_data = [
  (1,  "🥇", "Gold",     "#FFD700"),
  (2,  "🥈", "Silver",   "#C0C0C0"),
  (3,  "🥉", "Bronze",   "#CD7F32"),
  (4,  "💎", "Diamond",  "#00CFFF"),
  (5,  "💠", "Sapphire", "#0066FF"),
  (6,  "♦️",  "Ruby",     "#FF1744"),
  (7,  "🔮", "Amethyst", "#AA00FF"),
  (8,  "🌟", "Platinum", "#E0E0E0"),
  (9,  "⭐", "Emerald",  "#00C853"),
  (10, "✨", "Pearl",    "#F5F5F5")
] %}

<div style="margin-bottom:20px;">
  <p class="text-dim" style="font-size:0.88rem;">Top 10 authors ranked by total story views.</p>
</div>

{% if users %}
{% for user in users[:10] %}
{% set rd = rank_data[loop.index0] if loop.index0 < rank_data|length else (loop.index, "🏅", "Ranked", "#888") %}
<div style="background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px 16px; margin-bottom:10px; display:flex; align-items:center; gap:14px; position:relative; overflow:hidden;">

  <!-- Gem rank glow -->
  <div style="position:absolute; left:0; top:0; bottom:0; width:4px; background:{{ rd[3] }};"></div>

  <!-- Rank -->
  <div style="font-size:1.6rem; width:36px; text-align:center; flex-shrink:0;">{{ rd[1] }}</div>

  <!-- Avatar -->
  <div style="width:44px; height:44px; border-radius:50%; background:var(--green-dark); border:2px solid {{ rd[3] }}; display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:700; color:var(--green); flex-shrink:0; overflow:hidden;">
    {% if user.avatar and user.avatar != 'default.png' %}
    <img src="{{ url_for('static', filename='uploads/' + user.avatar) }}" style="width:44px; height:44px; object-fit:cover; border-radius:50%;">
    {% else %}
    {{ user.username[0].upper() }}
    {% endif %}
  </div>

  <!-- Info -->
  <div style="flex:1; min-width:0;">
    <a href="{{ url_for('profile', user_id=user.id) }}" style="color:var(--text); font-weight:700; font-size:0.95rem; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ user.username }}</a>
    <div style="font-size:0.75rem; color:{{ rd[3] }}; font-weight:600; margin-top:2px;">{{ rd[2] }} Rank</div>
    <div class="text-dim" style="font-size:0.76rem; margin-top:2px;">
      {{ user.stories|selectattr('is_published')|list|length }} stories · {{ user.follower_count() }} followers
    </div>
  </div>

  <!-- Views -->
  <div style="text-align:right; flex-shrink:0;">
    <div style="color:{{ rd[3] }}; font-weight:800; font-size:1.2rem;">
      {{ user.stories|selectattr('is_published')|sum(attribute='views') }}
    </div>
    <div class="text-dim" style="font-size:0.72rem;">views</div>
  </div>
</div>
{% endfor %}

{% else %}
<div class="empty-state">
  <div class="icon">📈</div>
  <p>No authors on the leaderboard yet.</p>
  <a href="{{ url_for('write') }}" class="btn btn-green">Start Writing</a>
</div>
{% endif %}

<div style="margin-top:24px; padding:14px; background:var(--dark); border-radius:8px; border:1px solid var(--border);">
  <p style="color:var(--green); font-weight:700; margin-bottom:10px; font-size:0.9rem;">🏆 Rank Tiers</p>
  <div style="display:flex; flex-wrap:wrap; gap:8px;">
    {% for pos, icon, name, color in rank_data %}
    <span style="background:var(--card); border:1px solid {{ color }}; color:{{ color }}; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">
      {{ icon }} #{{ pos }} {{ name }}
    </span>
    {% endfor %}
  </div>
</div>
{% endblock %}'''

with open(LEAD, 'w') as f:
    f.write(new_leaderboard)
patches += 1
print("✓ Leaderboard updated with gem ranks")

# ── 5. Fix chat template ──
new_chat = '''{% extends "base.html" %}
{% block title %}Messages — WritersWorld{% endblock %}
{% block page_title %}Messages{% endblock %}
{% block content %}
<div style="max-width:600px; margin:0 auto;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:8px;">
    <h3 style="color:var(--green);">💬 Chat with {{ user.username }}</h3>
    <a href="{{ url_for('notifications') if not current_user.is_admin else url_for('admin_panel') }}" class="btn btn-gray btn-sm">← Back</a>
  </div>

  <div id="chatBox" style="min-height:200px; max-height:55vh; overflow-y:auto; display:flex; flex-direction:column; gap:12px; margin-bottom:16px; padding:8px; background:var(--dark); border-radius:10px; border:1px solid var(--border);">
    {% if messages %}
    {% for msg in messages %}
    {% if current_user.is_admin %}
      {% set is_mine = (msg.admin_id == current_user.id and not msg.is_reply) %}
    {% else %}
      {% set is_mine = msg.is_reply %}
    {% endif %}
    <div style="display:flex; flex-direction:column; align-items:{% if is_mine %}flex-end{% else %}flex-start{% endif %};">
      <div style="font-size:0.7rem; color:var(--text-dim); margin-bottom:3px; {% if is_mine %}text-align:right;{% endif %}">
        {% if is_mine %}You{% else %}{% if current_user.is_admin %}{{ user.username }}{% else %}Admin{% endif %}{% endif %}
        · {{ msg.created_at.strftime('%d %b %H:%M') }}
      </div>
      <div style="max-width:80%; padding:10px 14px; border-radius:{% if is_mine %}12px 12px 4px 12px{% else %}12px 12px 12px 4px{% endif %}; word-wrap:break-word; font-size:0.9rem; line-height:1.5; {% if is_mine %}background:var(--green-dark); color:var(--green);{% else %}background:var(--card); border:1px solid var(--border); color:var(--text);{% endif %}">
        {{ msg.message }}
      </div>
    </div>
    {% endfor %}
    {% else %}
    <div style="text-align:center; padding:30px; color:var(--text-dim); font-size:0.88rem;">
      No messages yet. Start the conversation.
    </div>
    {% endif %}
  </div>

  <form method="POST" style="display:flex; gap:10px; align-items:flex-end;">
    <textarea name="message" placeholder="Type your message..." style="flex:1; background:var(--card); border:1px solid var(--border); color:var(--text); padding:10px 14px; border-radius:8px; resize:none; height:70px; outline:none; font-family:inherit; font-size:0.9rem;" required></textarea>
    <button type="submit" class="btn btn-green" style="height:44px; padding:0 20px;">Send ➤</button>
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
print("✓ Chat template rewritten — both sides show correctly")

print(f"\n✅ {patches} fixes applied.")
print("Now run: cd ~/writersworld && python3 app.py")
