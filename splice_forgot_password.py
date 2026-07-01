with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

def splice(old, new, label):
    global content
    count = content.count(old)
    assert count == 1, f"ABORT [{label}]: expected 1 match, found {count}"
    content = content.replace(old, new)

splice(
    '''    <button class="login-btn" onclick="doLogin()">Sign In</button>
    <div class="login-error" id="login-error">Invalid email or password.</div>''',
    '''    <button class="login-btn" onclick="doLogin()">Sign In</button>
    <div class="login-forgot" id="login-forgot" onclick="doForgotPassword()" style="text-align:center;margin-top:10px;font-size:13px;color:#999;cursor:pointer;text-decoration:underline;">Forgot password?</div>
    <div class="login-error" id="login-error">Invalid email or password.</div>
    <div class="login-error" id="login-forgot-msg" style="color:#4a9;display:none;"></div>''',
    "forgot password link"
)

splice(
    '''  async function doLogin() {''',
    '''  async function doForgotPassword() {
    const email = document.getElementById('login-user').value.trim();
    const errEl = document.getElementById('login-error');
    const msgEl = document.getElementById('login-forgot-msg');
    errEl.style.display = 'none';
    msgEl.style.display = 'none';
    if (!email) {
      errEl.textContent = 'Enter your email above first, then click "Forgot password?"';
      errEl.style.display = 'block';
      return;
    }
    try {
      const res = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=${API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requestType: 'PASSWORD_RESET', email })
      });
      const data = await res.json();
      if (!res.ok) throw new Error((data.error && data.error.message) || 'Could not send reset email');
      msgEl.textContent = 'Check your email for a password reset link.';
      msgEl.style.display = 'block';
    } catch (err) {
      errEl.textContent = 'Could not send reset email. Check the address and try again.';
      errEl.style.display = 'block';
    }
  }

  async function doLogin() {''',
    "doForgotPassword function"
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Forgot password feature added successfully.")
