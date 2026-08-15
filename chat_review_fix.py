#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  FIX: Chat messages + Review rejection reason
# ─────────────────────────────────────────────

import os

APP  = os.path.expanduser("~/writersworld/app.py")
CHAT = os.path.expanduser("~/writersworld/templates/chat.html")

# ── FIX 1: Chat — user can see admin message ──
with open(CHAT) as f:
    chat = f.read()

new_chat = '''{% extends "base.html" %}
{% block title %}Messages — WritersWorld{% endblock %}
{% block page_title %}Messages{% endblock %}
{% block content %}
<div style="max-width:600px; margin:0 auto;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:8px;">
    <h3 style="color:var(--green);">💬 Messages</h3>
    <a href="{{ url_for('notifications') }}" class="btn btn-gray btn-sm">← Back</a>
  </div>

  <div class="chat-messages" style="min-height:200px; max-height:60vh; overflow-y:auto; display:flex; flex-direction:column; gap:10px; margin-bottom:16px; padding:4px;">
    {% if messages %}
    {% for msg in messages %}
    {% set is_mine = msg.admin_id == current_user.id %}
    <div style="display:flex; flex-direction:column; align-items:{% if is_mine %}flex-end{% else %}flex-start{% endif %};">
      <div style="font-size:0.72rem; color:var(--text-dim); margin-bottom:3px; {% if is_mine %}text-align:right;{% endif %}">
        {% if is_mine %}You{% else %}{{ user.username if current_user.is_admin else 'Admin' }}{% endif %}
        · {{ msg.created_at.strftime('%d %b %Y %H:%M') }}
      </div>
      <div class="chat-bubble {% if is_mine %}admin{% else %}user{% endif %}" style="max-width:85%; word-wrap:break-word;">
        {{ msg.message }}
      </div>
    </div>
    {% endfor %}
    {% else %}
    <div class="empty-state" style="padding:30px 0;">
      <div class="icon">💬</div>
      <p>No messages yet. Send one below.</p>
    </div>
    {% endif %}
  </div>

  <form method="POST" style="display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end;">
    <div style="flex:1; min-width:200px;">
      <label style="color:var(--text-dim); font-size:0.82rem; display:block; margin-bottom:4px;">
        {% if current_user.is_admin %}Message to {{ user.username }}{% else %}Reply to Admin{% endif %}
      </label>
      <textarea name="message" placeholder="Type your message..." style="width:100%; background:var(--card); border:1px solid var(--border); color:var(--text); padding:10px; border-radius:6px; resize:none; height:70px; outline:none; font-family:inherit; font-size:0.9rem;" required></textarea>
    </div>
    <button type="submit" class="btn btn-green" style="height:40px; align-self:flex-end;">Send ➤</button>
  </form>
</div>

<script>
  // Auto scroll to bottom
  var chatBox = document.querySelector('.chat-messages');
  if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
</script>
{% endblock %}'''

with open(CHAT, 'w') as f:
    f.write(new_chat)
print("✓ Chat template fixed — messages now visible to both sides")

# ── FIX 2: Rejection reason for peer reviews ──
with open(APP) as f:
    app = f.read()

# Add reason to rejection route
old = '''@app.route('/admin/review/<int:review_id>/<action>', methods=['POST'])
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
    return redirect(url_for('admin_panel'))'''

new = '''@app.route('/admin/review/<int:review_id>/<action>', methods=['POST'])
@login_required
@admin_required
def admin_review_action(review_id, action):
    review = PeerReview.query.get_or_404(review_id)
    reason = request.form.get('reason', '').strip()
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
        flash('Review approved and shared with writer.', 'success')
    elif action == 'reject':
        review.is_rejected = True
        review.is_approved = False
        reject_msg = f"Your peer review for '{review.entry.title}' was rejected by admin."
        if reason:
            reject_msg += f" Reason: {reason}"
        add_notification(
            review.reviewer_id,
            reject_msg,
            'warning')
        # Also notify the entry author
        add_notification(
            review.entry.user_id,
            f"A peer review for your entry '{review.entry.title}' was rejected by admin." + (f" Reason: {reason}" if reason else ""),
            'info')
        flash('Review rejected. Reviewer has been notified.', 'success')
    db.session.commit()
    return redirect(url_for('admin_panel'))'''

if old in app:
    app = app.replace(old, new)
    print("✓ Rejection reason added to review action")
else:
    print("✗ Review action pattern not found")

with open(APP, 'w') as f:
    f.write(app)

print("\n✅ Done. Restart with: cd ~/writersworld && python3 app.py")
