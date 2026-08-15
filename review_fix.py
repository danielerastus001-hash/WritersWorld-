#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  PEER REVIEW FIX
#  Shows full story + Q&A in admin panel
#  Run: python3 review_fix.py
# ─────────────────────────────────────────────

import os, re

ADM  = os.path.expanduser("~/writersworld/templates/admin.html")
PROF = os.path.expanduser("~/writersworld/templates/profile.html")

# ── Fix admin.html peer review section ──
with open(ADM) as f:
    adm = f.read()

new_review_section = '''
<div class="admin-section" id="reviews">
  <h2>📝 Pending Peer Reviews
    {% if pending_reviews %}
    <span style="background:var(--red);color:#fff;border-radius:12px;padding:2px 10px;font-size:0.78rem;margin-left:8px;animation:pulse 1.5s infinite;">{{ pending_reviews|length }}</span>
    {% endif %}
  </h2>
  {% if pending_reviews %}
  {% for review in pending_reviews %}
  <div class="card" style="border-left:4px solid var(--green); margin-bottom:20px;">

    <!-- STORY ENTRY -->
    <div style="margin-bottom:16px;">
      <h4 style="color:var(--green); margin-bottom:4px;">📖 Entry: {{ review.entry.title }}</h4>
      <p class="text-dim" style="font-size:0.8rem; margin-bottom:8px;">
        Author: <strong>{{ review.entry.user.username }}</strong> |
        Reviewer: <strong>{{ review.reviewer.username }}</strong> |
        Submitted: {{ review.submitted_at.strftime('%d %b %Y %H:%M') }}
      </p>
      <div style="background:var(--dark); border:1px solid var(--border); border-radius:6px; padding:14px; max-height:200px; overflow-y:auto; font-size:0.88rem; line-height:1.7; white-space:pre-wrap; color:var(--text);">{{ review.entry.content }}</div>
    </div>

    <!-- REVIEW Q&A -->
    <div style="background:var(--dark); border-radius:8px; padding:14px; margin-bottom:14px;">
      <p style="color:var(--green); font-weight:700; margin-bottom:12px; font-size:0.9rem;">💬 Reviewer's Answers:</p>

      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border);">
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Q1. What element of this piece did you most admire, and why?</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.q1 if review.q1 else '—' }}</p>
      </div>

      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border);">
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Q2. Which scenes would you have liked expanded?</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.q2 if review.q2 else '—' }}</p>
      </div>

      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border);">
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Q3. Where did you want to better understand why a moment mattered?</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.q3 if review.q3 else '—' }}</p>
      </div>

      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border);">
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Q4. Did the ending satisfy you? Why or why not?</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.q4 if review.q4 else '—' }}</p>
      </div>

      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border);">
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Q5. What words of encouragement do you have for this writer?</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.q5 if review.q5 else '—' }}</p>
      </div>

      {% if review.extra %}
      <div>
        <p style="color:var(--text-dim); font-size:0.8rem; font-weight:600;">Additional Comments:</p>
        <p style="font-size:0.88rem; margin-top:4px; color:var(--text);">{{ review.extra }}</p>
      </div>
      {% endif %}
    </div>

    <!-- ACTIONS -->
    <div style="display:flex; gap:10px; flex-wrap:wrap;">
      <form method="POST" action="{{ url_for('admin_review_action', review_id=review.id, action='approve') }}">
        <button type="submit" class="btn btn-green">✓ Approve & Share with Writer</button>
      </form>
      <form method="POST" action="{{ url_for('admin_review_action', review_id=review.id, action='reject') }}">
        <button type="submit" class="btn btn-red">✗ Reject Review</button>
      </form>
    </div>
  </div>
  {% endfor %}
  {% else %}
  <div class="card" style="text-align:center; color:var(--text-dim); padding:20px; font-size:0.88rem;">
    No pending peer reviews.
  </div>
  {% endif %}
</div>
'''

# Replace existing review section
if 'id="reviews"' in adm:
    # Remove old section and replace
    adm = re.sub(
        r'<div class="admin-section" id="reviews">.*?</div>\s*\n',
        '',
        adm,
        flags=re.DOTALL
    )
    print("Old review section removed")

# Add new section before All Users
adm = adm.replace(
    '<div class="admin-section">\n  <h2>👥 All Users',
    new_review_section + '\n<div class="admin-section">\n  <h2>👥 All Users'
)

with open(ADM, 'w') as f:
    f.write(adm)
print("✓ Full peer review section added to admin")

# ── Fix duplicate awards on profile ──
with open(PROF) as f:
    prof = f.read()

# Remove old short awards block
old_awards = '''{% if awards %}
<div class="card" style="margin-bottom:20px;">
  <h3 style="color:var(--green); margin-bottom:12px;">🏅 Awards</h3>
  <div style="display:flex; flex-wrap:wrap; gap:10px;">
    {% for award in awards %}
    <div style="background:var(--dark); border:1px solid var(--green-dark); border-radius:8px; padding:8px 14px; text-align:center;">
      <div style="font-size:1.4rem;">{{ award.icon }}</div>
      <div style="color:var(--green); font-size:0.78rem; font-weight:600; margin-top:4px;">{{ award.name }}</div>
      <div style="color:var(--text-dim); font-size:0.72rem;">{{ award.reason }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}'''

if old_awards in prof:
    prof = prof.replace(old_awards, '')
    with open(PROF, 'w') as f:
        f.write(prof)
    print("✓ Duplicate awards removed from profile")
else:
    print("✓ No duplicate awards found")

print("\n✅ All done. Restart with: python3 app.py")

