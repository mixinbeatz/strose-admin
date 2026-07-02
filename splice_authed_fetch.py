with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

old = '''  async function fs_get(col) { const r=await fetch(`${BASE}/${col}?key=${API_KEY}&pageSize=100`); return await r.json(); }
  async function fs_get_doc(path) { const r=await fetch(`${BASE}/${path}?key=${API_KEY}`); return await r.json(); }
  async function fs_post(col,fields) { const r=await fetch(`${BASE}/${col}?key=${API_KEY}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fields})}); return await r.json(); }
  async function fs_patch(path,fields) { const mask=Object.keys(fields).map(f=>`updateMask.fieldPaths=${f}`).join('&'); const r=await fetch(`${BASE}/${path}?key=${API_KEY}&${mask}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({fields})}); return await r.json(); }
  async function fs_delete(path) { await fetch(`${BASE}/${path}?key=${API_KEY}`,{method:'DELETE'}); }'''

new = '''  function authHeaders(extra) {
    const token = localStorage.getItem('authIdToken');
    return token ? Object.assign({ Authorization: 'Bearer ' + token }, extra || {}) : (extra || {});
  }
  async function fs_get(col) { const r=await fetch(`${BASE}/${col}?key=${API_KEY}&pageSize=100`,{headers:authHeaders()}); return await r.json(); }
  async function fs_get_doc(path) { const r=await fetch(`${BASE}/${path}?key=${API_KEY}`,{headers:authHeaders()}); return await r.json(); }
  async function fs_post(col,fields) { const r=await fetch(`${BASE}/${col}?key=${API_KEY}`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),body:JSON.stringify({fields})}); return await r.json(); }
  async function fs_patch(path,fields) { const mask=Object.keys(fields).map(f=>`updateMask.fieldPaths=${f}`).join('&'); const r=await fetch(`${BASE}/${path}?key=${API_KEY}&${mask}`,{method:'PATCH',headers:authHeaders({'Content-Type':'application/json'}),body:JSON.stringify({fields})}); return await r.json(); }
  async function fs_delete(path) { await fetch(`${BASE}/${path}?key=${API_KEY}`,{method:'DELETE',headers:authHeaders()}); }'''

count = content.count(old)
assert count == 1, f"ABORT: expected 1 match, found {count}"
content = content.replace(old, new)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Auth headers wired into Firestore helpers successfully.")
