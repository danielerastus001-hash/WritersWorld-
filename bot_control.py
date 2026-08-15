#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  BOT CONTROL SYSTEM PATCH
#  Adds bot control to admin + approval system
# ─────────────────────────────────────────────

import os

APP = os.path.expanduser("~/writersworld/app.py")
BOT = os.path.expanduser("~/writersworld/bot_system.py")

# ── 1. Update bot_system.py to save as draft (pending approval) ──
with open(BOT) as f:
    bot = f.read()

old = '''                            if title and content and len(content) > 200:
                                story = Story(
                                    title=title,
                                    content=content,
                                    genre=personality["genre"],
                                    is_published=True,
                                    user_id=bot_user.id,
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(story)
                                db.session.commit()
                                self.record_post(bot_name)
                                self.post_log[story.id] = datetime.utcnow()
                                self.log(f"{bot_name} posted: {title}")
                                # Stagger next bot
                                time.sleep(random.uniform(60, 300))'''

new = '''                            if title and content and len(content) > 200:
                                # Save as DRAFT — requires admin approval
                                story = Story(
                                    title=title,
                                    content=content,
                                    genre=personality["genre"],
                                    is_published=False,
                                    user_id=bot_user.id,
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(story)
                                db.session.commit()
                                self.record_post(bot_name)
                                self.post_log[story.id] = datetime.utcnow()
                                self.log(f"{bot_name} drafted: {title} (awaiting approval)")
                                # Notify admin
                                try:
                                    from database import User, Notification
                                    admin = User.query.filter_by(is_admin=True).first()
                                    if admin:
                                        n = Notification(
                                            user_id=admin.id,
                                            message=f"Bot story pending approval: '{title}' by {bot_name}",
                                            type='info',
                                            link='/admin/bots'
                                        )
                                        db.session.add(n)
                                        db.session.commit()
                                except:
                                    pass
                                time.sleep(random.uniform(60, 300))'''

if old in bot:
    bot = bot.replace(old, new)
    with open(BOT, 'w') as f:
        f.write(bot)
    print("✓ Bot stories now require admin approval")
else:
    print("✗ Bot posting pattern not found")

# ── 2. Add bot control state file ──
bot_state_init = '''
import json as _json
import os as _os

BOT_STATE_FILE = _os.path.join(_os.path.dirname(__file__), 'bot_state.json')

def load_bot_state():
    try:
        with open(BOT_STATE_FILE) as f:
            return _json.load(f)
    except:
        return {
            "global_active": True,
            "bots": {name: {"active": True, "activity": "medium"}
                     for name in BOT_PERSONALITIES}
        }

def save_bot_state(state):
    with open(BOT_STATE_FILE, 'w') as f:
        _json.dump(state, f, indent=2)

def is_bot_active(bot_name):
    state = load_bot_state()
    if not state.get("global_active", True):
        return False
    return state.get("bots", {}).get(bot_name, {}).get("active", True)

def get_bot_activity(bot_name):
    state = load_bot_state()
    return state.get("bots", {}).get(bot_name, {}).get("activity", "medium")

'''

if 'load_bot_state' not in bot:
    with open(BOT) as f:
        bot = f.read()
    bot = bot.replace(
        'class BotService:',
        bot_state_init + 'class BotService:'
    )
    # Use bot state in posting
    bot = bot.replace(
        '                        if should_post:',
        '                        if should_post and is_bot_active(bot_name):'
    )
    bot = bot.replace(
        '                            if self.can_like(story.id, bot_name):',
        '                            if self.can_like(story.id, bot_name) and is_bot_active(bot_name):'
    )
    bot = bot.replace(
        '                            if self.can_comment(story.id, bot_name):',
        '                            if self.can_comment(story.id, bot_name) and is_bot_active(bot_name):'
    )
    with open(BOT, 'w') as f:
        f.write(bot)
    print("✓ Bot state control added")

# ── 3. Add bot activity log ──
bot_log_path = os.path.expanduser("~/writersworld/bot_activity.json")
if not os.path.exists(bot_log_path):
    import json
    with open(bot_log_path, 'w') as f:
        json.dump([], f)
    print("✓ Bot activity log created")

# ── 4. Add bot control routes to app.py ──
with open(APP) as f:
    app = f.read()

bot_routes = '''
# ─────────────────────────────────────────────
#  BOT CONTROL ROUTES
# ─────────────────────────────────────────────
@app.route('/admin/bots')
@login_required
@admin_required
def admin_bots():
    import json as _json
    from database import User, Story
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

'''

if 'admin_bots' not in app:
    pos = app.find("if __name__ == '__main__':")
    if pos == -1:
        pos = app.find('if __name__ == "__main__":')
    if pos != -1:
        app = app[:pos] + bot_routes + app[pos:]
        with open(APP, 'w') as f:
            f.write(app)
        print("✓ Bot control routes added to app.py")
    else:
        print("✗ Could not find main block")
else:
    print("✓ Bot routes already exist")

print("\n✅ Bot control system ready.")
print("Now paste admin_bots.html template.")
