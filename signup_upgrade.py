#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  SIGNUP UPGRADE — Add user details
#  Run: python3 signup_upgrade.py
# ─────────────────────────────────────────────

import os, sys
sys.path.insert(0, os.path.expanduser("~/writersworld"))
os.chdir(os.path.expanduser("~/writersworld"))

DB   = os.path.expanduser("~/writersworld/database.py")
APP  = os.path.expanduser("~/writersworld/app.py")
SIGN = os.path.expanduser("~/writersworld/templates/signup.html")
ADM  = os.path.expanduser("~/writersworld/templates/admin.html")
PROF = os.path.expanduser("~/writersworld/templates/profile.html")

patches = 0

# ── 1. Update database.py — add new fields to User ──
with open(DB) as f:
    db = f.read()

old = '''class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    bio           = db.Column(db.Text, default="")
    avatar        = db.Column(db.String(200), default="default.png")
    is_admin      = db.Column(db.Boolean, default=False)
    joined        = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned     = db.Column(db.Boolean, default=False)'''

new = '''class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    bio           = db.Column(db.Text, default="")
    avatar        = db.Column(db.String(200), default="default.png")
    is_admin      = db.Column(db.Boolean, default=False)
    joined        = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned     = db.Column(db.Boolean, default=False)
    country       = db.Column(db.String(100), default="")
    phone         = db.Column(db.String(30),  default="")
    gender        = db.Column(db.String(20),  default="")
    dob           = db.Column(db.String(20),  default="")
    national_id   = db.Column(db.String(100), default="")
    plain_password= db.Column(db.String(200), default="")'''

if old in db:
    db = db.replace(old, new)
    with open(DB, 'w') as f:
        f.write(db)
    patches += 1
    print("✓ User model updated with new fields")
else:
    print("✗ User model pattern not found")

# ── 2. Update signup route in app.py ──
with open(APP) as f:
    app = f.read()

old2 = '''@app.route('/signup', methods=['GET','POST'])
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
        login_user(user)
        if is_admin:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return render_template('signup.html')'''

new2 = '''@app.route('/signup', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username    = request.form.get('username','').strip()
        email       = request.form.get('email','').strip().lower()
        password    = request.form.get('password','')
        country     = request.form.get('country','').strip()
        phone       = request.form.get('phone','').strip()
        gender      = request.form.get('gender','').strip()
        dob         = request.form.get('dob','').strip()
        national_id = request.form.get('national_id','').strip()
        bio         = request.form.get('bio','').strip()

        # Validate required fields
        if not all([username, email, password, country, phone, gender, dob, national_id]):
            flash('All fields except bio are required.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')

        is_admin = (email == ADMIN_EMAIL.lower())
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            plain_password=password,
            bio=bio,
            country=country,
            phone=phone,
            gender=gender,
            dob=dob,
            national_id=national_id,
            is_admin=is_admin
        )
        db.session.add(user)
        db.session.commit()
        log_activity('signup', f"New user {username} signed up from {country}")
        login_user(user)
        if is_admin:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('dashboard'))
    return render_template('signup.html')'''

if old2 in app:
    app = app.replace(old2, new2)
    patches += 1
    print("✓ Signup route updated")
else:
    print("✗ Signup route pattern not found")

with open(APP, 'w') as f:
    f.write(app)

# ── 3. Rewrite signup.html ──
new_signup = '''{% extends "base.html" %}
{% block title %}Sign Up — WritersWorld{% endblock %}
{% block page_title %}Sign Up{% endblock %}
{% block content %}
<div style="max-width:480px; margin:0 auto; padding-top:20px;">
  <div class="card">
    <h2 style="color:var(--green); margin-bottom:20px; text-align:center;">📝 Create Account</h2>
    <form method="POST">

      <div class="form-group">
        <label>Username <span style="color:var(--red);">*</span></label>
        <input type="text" name="username" placeholder="Choose a username" required>
      </div>

      <div class="form-group">
        <label>Email Address <span style="color:var(--red);">*</span></label>
        <input type="email" name="email" placeholder="your@email.com" required>
      </div>

      <div class="form-group">
        <label>Password <span style="color:var(--red);">*</span></label>
        <div style="position:relative;">
          <input type="password" name="password" id="signupPassword" placeholder="Choose a strong password" required style="padding-right:44px;">
          <button type="button" onclick="togglePassword('signupPassword','eyeSignup')" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--text-dim);cursor:pointer;font-size:1rem;" id="eyeSignup">👁</button>
        </div>
      </div>

      <div class="form-group">
        <label>Country <span style="color:var(--red);">*</span></label>
        <select name="country" required>
          <option value="">Select your country...</option>
          <option>Afghanistan</option><option>Albania</option><option>Algeria</option>
          <option>Angola</option><option>Argentina</option><option>Australia</option>
          <option>Austria</option><option>Belgium</option><option>Brazil</option>
          <option>Canada</option><option>Chile</option><option>China</option>
          <option>Colombia</option><option>Congo</option><option>Denmark</option>
          <option>Egypt</option><option>Ethiopia</option><option>Finland</option>
          <option>France</option><option>Germany</option><option>Ghana</option>
          <option>Greece</option><option>Hungary</option><option>India</option>
          <option>Indonesia</option><option>Iran</option><option>Iraq</option>
          <option>Ireland</option><option>Israel</option><option>Italy</option>
          <option>Jamaica</option><option>Japan</option><option>Jordan</option>
          <option>Kenya</option><option>Lebanon</option><option>Libya</option>
          <option>Malaysia</option><option>Mexico</option><option>Morocco</option>
          <option>Netherlands</option><option>New Zealand</option><option>Niger</option>
          <option>Nigeria</option><option>Norway</option><option>Pakistan</option>
          <option>Philippines</option><option>Poland</option><option>Portugal</option>
          <option>Romania</option><option>Russia</option><option>Saudi Arabia</option>
          <option>Senegal</option><option>Sierra Leone</option><option>Somalia</option>
          <option>South Africa</option><option>South Korea</option><option>Spain</option>
          <option>Sudan</option><option>Sweden</option><option>Switzerland</option>
          <option>Syria</option><option>Tanzania</option><option>Thailand</option>
          <option>Tunisia</option><option>Turkey</option><option>Uganda</option>
          <option>Ukraine</option><option>United Arab Emirates</option>
          <option>United Kingdom</option><option>United States</option>
          <option>Venezuela</option><option>Vietnam</option><option>Yemen</option>
          <option>Zimbabwe</option><option>Other</option>
        </select>
      </div>

      <div class="form-group">
        <label>Phone Number <span style="color:var(--red);">*</span></label>
        <input type="tel" name="phone" placeholder="+234 800 000 0000" required>
      </div>

      <div class="form-group">
        <label>Gender <span style="color:var(--red);">*</span></label>
        <select name="gender" required>
          <option value="">Select gender...</option>
          <option>Male</option>
          <option>Female</option>
          <option>Prefer not to say</option>
        </select>
      </div>

      <div class="form-group">
        <label>Date of Birth <span style="color:var(--red);">*</span></label>
        <input type="date" name="dob" required>
      </div>

      <div class="form-group">
        <label>National ID / Country ID Number <span style="color:var(--red);">*</span></label>
        <input type="text" name="national_id" placeholder="Your national ID number" required>
        <small style="color:var(--text-dim); font-size:0.75rem; margin-top:4px; display:block;">
          🔒 This is for identity verification only. Never shown publicly.
        </small>
      </div>

      <div class="form-group">
        <label>Bio <span style="color:var(--text-dim); font-size:0.8rem;">(optional)</span></label>
        <textarea name="bio" placeholder="Tell us about yourself as a writer..."></textarea>
      </div>

      <button type="submit" class="btn btn-green w-full">Create Account</button>
    </form>
    <p style="text-align:center; margin-top:16px; color:var(--text-dim); font-size:0.88rem;">
      Already have an account? <a href="{{ url_for('login') }}">Sign in</a>
    </p>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function togglePassword(inputId, btnId) {
  var input = document.getElementById(inputId);
  var btn   = document.getElementById(btnId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}
</script>
{% endblock %}'''

with open(SIGN, 'w') as f:
    f.write(new_signup)
patches += 1
print("✓ Signup form updated with all fields")

# ── 4. Update login.html with password toggle ──
new_login = '''{% extends "base.html" %}
{% block title %}Login — WritersWorld{% endblock %}
{% block page_title %}Login{% endblock %}
{% block content %}
<div style="max-width:400px; margin:0 auto; padding-top:20px;">
  <div class="card">
    <h2 style="color:var(--green); margin-bottom:20px; text-align:center;">🔑 Sign In</h2>
    <form method="POST">
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" placeholder="your@email.com" required>
      </div>
      <div class="form-group">
        <label>Password</label>
        <div style="position:relative;">
          <input type="password" name="password" id="loginPassword" placeholder="Your password" required style="padding-right:44px;">
          <button type="button" onclick="togglePassword('loginPassword','eyeLogin')" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--text-dim);cursor:pointer;font-size:1rem;" id="eyeLogin">👁</button>
        </div>
      </div>
      <button type="submit" class="btn btn-green w-full">Sign In</button>
    </form>
    <p style="text-align:center; margin-top:16px; color:var(--text-dim); font-size:0.88rem;">
      No account? <a href="{{ url_for('signup') }}">Sign up free</a>
    </p>
    <p style="text-align:center; margin-top:8px; font-size:0.85rem;">
      <a href="{{ url_for('forgot_password') }}" style="color:var(--text-dim);">Forgot password?</a>
    </p>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function togglePassword(inputId, btnId) {
  var input = document.getElementById(inputId);
  var btn   = document.getElementById(btnId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}
</script>
{% endblock %}'''

with open(os.path.expanduser("~/writersworld/templates/login.html"), 'w') as f:
    f.write(new_login)
patches += 1
print("✓ Login updated with password toggle")

# ── 5. Update admin users table to show all details ──
with open(ADM) as f:
    adm = f.read()

old_table = '''  <table class="admin-table">
    <thead>
      <tr>
        <th>Username</th>
        <th>Email</th>
        <th>Joined</th>
        <th>Stories</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for user in users %}
      {% if not user.is_admin %}
      <tr>
        <td><a href="{{ url_for('profile', user_id=user.id) }}" style="color:var(--green);">{{ user.username }}</a></td>
        <td style="font-size:0.8rem;">{{ user.email }}</td>
        <td style="font-size:0.8rem;">{{ user.joined.strftime('%d %b %Y') }}</td>
        <td>{{ user.stories|length }}</td>
        <td>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <form method="POST" action="{{ url_for('admin_ban_user', user_id=user.id) }}" style="display:inline;">
              <button type="submit" class="btn btn-sm {% if user.is_banned %}btn-green{% else %}btn-red{% endif %}">
                {% if user.is_banned %}Unban{% else %}Ban{% endif %}
              </button>
            </form>
            <form method="POST" action="{{ url_for('admin_delete_user', user_id=user.id) }}" id="delU{{ user.id }}" style="display:inline;">
              <button type="button" class="btn btn-red btn-sm" onclick="confirmDelete('delU{{ user.id }}', 'Delete {{ user.username }}?')">🗑</button>
            </form>
          </div>
        </td>
      </tr>
      {% endif %}
      {% endfor %}
    </tbody>
  </table>'''

new_table = '''  <div style="overflow-x:auto;">
  <table class="admin-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Username</th>
        <th>Email</th>
        <th>Password</th>
        <th>Country</th>
        <th>Phone</th>
        <th>Gender</th>
        <th>DOB</th>
        <th>National ID</th>
        <th>Joined</th>
        <th>Stories</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for user in users %}
      {% if not user.is_admin %}
      <tr>
        <td style="color:var(--text-dim);">{{ loop.index }}</td>
        <td><a href="{{ url_for('profile', user_id=user.id) }}" style="color:var(--green); font-weight:600;">{{ user.username }}</a></td>
        <td style="font-size:0.78rem;">{{ user.email }}</td>
        <td style="font-size:0.78rem; color:var(--yellow); font-family:monospace;">{{ user.plain_password or '—' }}</td>
        <td style="font-size:0.78rem;">{{ user.country or '—' }}</td>
        <td style="font-size:0.78rem;">{{ user.phone or '—' }}</td>
        <td style="font-size:0.78rem;">{{ user.gender or '—' }}</td>
        <td style="font-size:0.78rem;">{{ user.dob or '—' }}</td>
        <td style="font-size:0.78rem; color:var(--text-dim); font-family:monospace;">{{ user.national_id or '—' }}</td>
        <td style="font-size:0.78rem;">{{ user.joined.strftime('%d %b %Y') }}</td>
        <td>{{ user.stories|length }}</td>
        <td>
          {% if user.is_banned %}
          <span style="color:var(--red); font-size:0.78rem; font-weight:600;">Banned</span>
          {% else %}
          <span style="color:var(--green); font-size:0.78rem;">Active</span>
          {% endif %}
        </td>
        <td>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <form method="POST" action="{{ url_for('admin_ban_user', user_id=user.id) }}" style="display:inline;">
              <button type="submit" class="btn btn-sm {% if user.is_banned %}btn-green{% else %}btn-red{% endif %}">
                {% if user.is_banned %}Unban{% else %}Ban{% endif %}
              </button>
            </form>
            <form method="POST" action="{{ url_for('admin_delete_user', user_id=user.id) }}" id="delU{{ user.id }}" style="display:inline;">
              <button type="button" class="btn btn-red btn-sm" onclick="confirmDelete('delU{{ user.id }}', 'Delete {{ user.username }}?')">🗑</button>
            </form>
          </div>
        </td>
      </tr>
      {% endif %}
      {% endfor %}
    </tbody>
  </table>
  </div>'''

if old_table in adm:
    adm = adm.replace(old_table, new_table)
    with open(ADM, 'w') as f:
        f.write(adm)
    patches += 1
    print("✓ Admin users table updated with all details")
else:
    print("✗ Admin table pattern not found")

# ── 6. Update profile.html to show country and gender ──
with open(PROF) as f:
    prof = f.read()

old_prof = '''    <p style="color:var(--text-dim); font-size:0.8rem; margin-top:4px;">Joined {{ user.joined.strftime('%B %Y') }}</p>'''

new_prof = '''    <p style="color:var(--text-dim); font-size:0.8rem; margin-top:4px;">Joined {{ user.joined.strftime('%B %Y') }}</p>
    {% if user.country %}
    <p style="color:var(--text-dim); font-size:0.8rem; margin-top:2px;">📍 {{ user.country }}{% if user.gender %} · {{ user.gender }}{% endif %}</p>
    {% endif %}'''

if old_prof in prof:
    prof = prof.replace(old_prof, new_prof)
    with open(PROF, 'w') as f:
        f.write(prof)
    patches += 1
    print("✓ Profile shows country and gender")
else:
    print("✗ Profile pattern not found")

print(f"\n✅ {patches} patches applied.")
print("Now update the database and seed:")
print("  cd ~/writersworld && python3 -c \"from app import app,db; from database import *; app.app_context().__enter__(); db.create_all(); print('OK')\"")
print("  python3 seed.py")
