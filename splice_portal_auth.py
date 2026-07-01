import sys

PATH = "index.html"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

def splice(old, new, label):
    global content
    count = content.count(old)
    assert count == 1, f"ABORT [{label}]: expected 1 match, found {count}"
    content = content.replace(old, new)

splice(
    '''    <input type="text" id="login-user" placeholder="Username" autocomplete="off" />''',
    '''    <input type="email" id="login-user" placeholder="Email" autocomplete="off" />''',
    "login field -> email"
)

splice(
    '''    <div class="login-error" id="login-error">Invalid username or password.</div>''',
    '''    <div class="login-error" id="login-error">Invalid email or password.</div>''',
    "login error text"
)

splice(
    '''  const CREDS = { mficarra:'music2026', admin:'admin', sacredapps:'admin1', nponiato:'cda2026', cheyanne:'office2026' };
  const MINISTRY_ID_MAP = { nponiato: 'cda' };
  const MINISTRY_NAME_MAP = { nponiato: 'Catholic Daughters' };
  let currentUser = '';''',
    '''  const MINISTRY_NAME_MAP = { cda: 'Catholic Daughters' }; // ministry id (custom claim) -> display name
  const STAFF_NAME_MAP = {
    'markramski@gmail.com': 'Mark Ramotowski',
    'mficarra@stroseanthem.com': 'Matthew Ficarra',
    'cbosn@stroseanthem.com': 'Cheyanne Bosn',
    'pnovak@stroseanthem.com': 'Paul Novak',
    'thenrich@stroseanthem.com': 'Tom Henrich',
    'frbcolasito@stroseanthem.com': 'Fr. Bing Colasito'
    // add nponiato's real email here once her account is bootstrapped
  };
  let currentUser = '';
  let currentClaims = null;''',
    "CREDS block -> claims-based name maps"
)

splice(
    '''  function doLogin() {
    const u = document.getElementById('login-user').value.trim();
    const p = document.getElementById('login-pass').value;
    if (CREDS[u] === p) {
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      currentUser = u;
      document.getElementById('logged-in-user').textContent = u==='sacredapps'?'Sacred Apps Admin':u==='nponiato'?'Nancy Poniatowski':u==='mficarra'?'Matthew Ficarra':u==='cheyanne'?'Cheyanne':'Parish Staff';
      applyRoleNav(u);
      loadDashboard();
    } else { document.getElementById('login-error').style.display = 'block'; }
  }''',
    '''  function decodeJwt(token) {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(atob(payload).split('').map(c => '%' + c.charCodeAt(0).toString(16).padStart(2, '0')).join(''));
    return JSON.parse(json);
  }

  function setSession(idToken, refreshToken) {
    localStorage.setItem('authIdToken', idToken);
    localStorage.setItem('authRefreshToken', refreshToken);
    currentClaims = decodeJwt(idToken);
    currentUser = currentClaims.email || '';
  }

  function clearSession() {
    localStorage.removeItem('authIdToken');
    localStorage.removeItem('authRefreshToken');
    currentClaims = null;
    currentUser = '';
  }

  // Attaches the current ID token to a Firestore/API call. Use this once portal reads/writes require auth (re-lock step).
  function authedFetch(url, options) {
    options = options || {};
    const token = localStorage.getItem('authIdToken');
    if (!token) return fetch(url, options);
    options.headers = Object.assign({}, options.headers, { Authorization: 'Bearer ' + token });
    return fetch(url, options);
  }

  function enterApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
    document.getElementById('logged-in-user').textContent = STAFF_NAME_MAP[currentUser] || (currentClaims.role ? currentClaims.role.charAt(0).toUpperCase() + currentClaims.role.slice(1) : 'Parish Staff');
    applyRoleNav();
    loadDashboard();
  }

  async function tryRestoreSession() {
    const token = localStorage.getItem('authIdToken');
    if (!token) return false;
    try {
      const claims = decodeJwt(token);
      if (claims.exp && claims.exp * 1000 < Date.now()) { clearSession(); return false; }
      currentClaims = claims;
      currentUser = claims.email || '';
      enterApp();
      return true;
    } catch (e) { clearSession(); return false; }
  }

  async function doLogin() {
    const email = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value;
    document.getElementById('login-error').style.display = 'none';
    try {
      const res = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass, returnSecureToken: true })
      });
      const data = await res.json();
      if (!res.ok) throw new Error((data.error && data.error.message) || 'Login failed');
      setSession(data.idToken, data.refreshToken);
      enterApp();
    } catch (err) {
      document.getElementById('login-error').style.display = 'block';
    }
  }''',
    "doLogin -> Firebase Auth sign-in + session helpers"
)

splice(
    '''  function applyRoleNav(u) {
    const isMinistry = u === 'nponiato';
    const isCheyanne = u === 'cheyanne';
    const isMatt     = !isMinistry && !isCheyanne;''',
    '''  function applyRoleNav() {
    const isMinistry = !!(currentClaims && currentClaims.role === 'ministry');
    const isCheyanne = !!(currentClaims && currentClaims.email === 'cbosn@stroseanthem.com');
    const isMatt     = !isMinistry && !isCheyanne;''',
    "applyRoleNav -> claims-based"
)

splice(
    '''  function signOut() {
    var tb = document.querySelector('.topbar'); if (tb) tb.style.display = 'flex';
    var ct = document.querySelector('.content'); if (ct) ct.style.padding = '32px';
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
    document.getElementById('login-user').value = '';
    document.getElementById('login-pass').value = '';
  }''',
    '''  function signOut() {
    clearSession();
    var tb = document.querySelector('.topbar'); if (tb) tb.style.display = 'flex';
    var ct = document.querySelector('.content'); if (ct) ct.style.padding = '32px';
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
    document.getElementById('login-user').value = '';
    document.getElementById('login-pass').value = '';
  }''',
    "signOut clears session"
)

splice(
    '''  document.getElementById('login-pass').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });''',
    '''  document.getElementById('login-pass').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });
  tryRestoreSession();''',
    "restore session on load"
)

splice(
    '''  async function loadMyMinistry() {
    const ministryId = MINISTRY_ID_MAP[currentUser];''',
    '''  async function loadMyMinistry() {
    const ministryId = currentClaims && currentClaims.ministry;''',
    "loadMyMinistry ministryId"
)

splice(
    '''  async function saveMyMinistry() {
    const ministryId = MINISTRY_ID_MAP[currentUser];''',
    '''  async function saveMyMinistry() {
    const ministryId = currentClaims && currentClaims.ministry;''',
    "saveMyMinistry ministryId"
)

splice(
    '''      const ministryName = MINISTRY_NAME_MAP[currentUser] || 'Catholic Daughters';''',
    '''      const ministryName = MINISTRY_NAME_MAP[currentClaims && currentClaims.ministry] || 'Catholic Daughters';''',
    "loadMinistryPosts ministryName"
)

splice(
    '''    var ministry = currentUser === 'nponiato' ? 'Catholic Daughters' : 'Ministry';
    var submittedBy = currentUser === 'nponiato' ? 'Nancy Poniatowski' : currentUser;''',
    '''    var ministry = MINISTRY_NAME_MAP[currentClaims && currentClaims.ministry] || 'Ministry';
    var submittedBy = STAFF_NAME_MAP[currentUser] || currentUser;''',
    "submit-event ministry/submittedBy"
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("All 11 splices applied successfully.")
