#!/usr/bin/env python3
"""Super Projects: single-file GitHub-style project host.
Run: python -m pip install Flask && python super_projects.py
Open: http://127.0.0.1:5000
Set SECRET_KEY and DATA_DIR environment variables in production.
"""
from __future__ import annotations
import fnmatch, hashlib, hmac, io, json, mimetypes, os, re, secrets, shutil, tempfile, zipfile
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
from flask import Flask, Response, abort, jsonify, redirect, render_template_string, request, send_file, session, url_for
from werkzeug.utils import secure_filename

APP = Flask(__name__)
APP.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
APP.config.update(MAX_CONTENT_LENGTH=64 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
ROOT = Path(os.environ.get("DATA_DIR", Path(__file__).with_name("super_projects_data"))).resolve()
PROJECTS = ROOT / "projects"
DB = ROOT / "users.xml"
ROOT.mkdir(parents=True, exist_ok=True); PROJECTS.mkdir(exist_ok=True)
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,24}$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9._-]{1,60}$")
LANG = {
"Python":"#3572A5","JavaScript":"#f1e05a","TypeScript":"#3178c6","HTML":"#e34c26","CSS":"#563d7c",
"Java":"#b07219","C":"#555555","C++":"#f34b7d","C#":"#178600","Go":"#00ADD8","Rust":"#dea584",
"Ruby":"#701516","PHP":"#4F5D95","Swift":"#F05138","Kotlin":"#A97BFF","Shell":"#89e051","R":"#198CE7",
"Dart":"#00B4AB","Lua":"#000080","Vue":"#41b883","Svelte":"#ff3e00","Markdown":"#083fa1","Other":"#8b98a7"}
EXT_LANG={".py":"Python",".js":"JavaScript",".mjs":"JavaScript",".ts":"TypeScript",".html":"HTML",".htm":"HTML",".css":"CSS",".java":"Java",".c":"C",".h":"C",".cpp":"C++",".hpp":"C++",".cs":"C#",".go":"Go",".rs":"Rust",".rb":"Ruby",".php":"PHP",".swift":"Swift",".kt":"Kotlin",".sh":"Shell",".r":"R",".dart":"Dart",".lua":"Lua",".vue":"Vue",".svelte":"Svelte",".md":"Markdown"}

def now(): return datetime.now(timezone.utc).isoformat()
def init_db():
    if not DB.exists():
        root=ET.Element("superProjects", version="1"); ET.SubElement(root,"users"); write_xml(root)
def read_xml(): init_db(); return ET.parse(DB).getroot()
def write_xml(root):
    tmp=DB.with_suffix(".tmp"); ET.ElementTree(root).write(tmp, encoding="utf-8", xml_declaration=True); os.replace(tmp,DB)
def user_node(root, name): return next((u for u in root.find("users") if u.get("name")==name),None)
def hash_password(password, salt=None):
    salt=salt or secrets.token_bytes(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return salt.hex()+":"+digest.hex()
def verify_password(password, stored):
    try: s,d=stored.split(":",1); return hmac.compare_digest(hash_password(password,bytes.fromhex(s)).split(":")[1],d)
    except Exception: return False
def slug_id(): return secrets.token_urlsafe(9).replace("-","").replace("_","")
def current_user(): return session.get("username")
def login_required(fn):
    @wraps(fn)
    def inner(*a,**k):
        if not current_user(): return jsonify(error="Sign in required."),401
        return fn(*a,**k)
    return inner
def safe_rel(raw):
    raw=str(raw or "").replace("\\","/").strip("/"); p=PurePosixPath(raw)
    if not raw or p.is_absolute() or ".." in p.parts or any(x in ("", ".") for x in p.parts): abort(400,"Invalid path")
    return p
def project_dir(owner,pid): return PROJECTS/secure_filename(owner)/pid
def get_project(pid):
    root=read_xml()
    for u in root.find("users"):
        ps=u.find("projects")
        if ps is not None:
            for p in ps:
                if p.get("id")==pid: return root,u,p
    return root,None,None
def project_json(u,p):
    return {"id":p.get("id"),"name":p.get("name"),"description":p.get("description", ""),"visibility":p.get("visibility","public"),"language":p.get("language","Other"),"owner":u.get("name"),"created":p.get("created"),"updated":p.get("updated")}
def can_view(u,p): return p is not None and (p.get("visibility")=="public" or current_user()==u.get("name"))
def owner_only(u):
    if u is None or current_user()!=u.get("name"): abort(403)
def touch(root,p): p.set("updated",now()); write_xml(root)
def detect_language(folder):
    scores={}
    if folder.exists():
        for f in folder.rglob("*"):
            if f.is_file():
                lang=EXT_LANG.get(f.suffix.lower())
                if lang: scores[lang]=scores.get(lang,0)+max(1,min(f.stat().st_size,100000))
    return max(scores,key=scores.get) if scores else "Other"
def ignore_patterns(folder):
    defaults=[".DS_Store","Thumbs.db","__pycache__","*.pyc",".git",".git/*"]
    f=folder/".fileignore"
    if f.exists():
        try: defaults += [x.strip() for x in f.read_text("utf-8",errors="ignore").splitlines() if x.strip() and not x.lstrip().startswith("#")]
        except OSError: pass
    return defaults
def ignored(rel,patterns):
    s=rel.as_posix(); return any(fnmatch.fnmatch(s,p) or fnmatch.fnmatch(rel.name,p.rstrip("/")) or (p.endswith("/") and s.startswith(p)) for p in patterns)

HTML=r'''<!doctype html><html lang="en" data-theme="dark"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#0d1117">
<title>Super Projects</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
<style>
:root{color-scheme:dark;--page:#0d1117;--panel:#111820;--raised:#151d26;--hover:#19232d;--border:#28333f;--text:#e6edf3;--muted:#8b98a7;--green:#70e1ad;--blue:#88baff;--red:#ff8585;font-family:Inter,system-ui,sans-serif} [data-theme=light]{color-scheme:light;--page:#f6f8fa;--panel:#fff;--raised:#fff;--hover:#f3f6f8;--border:#d8dee4;--text:#1f2328;--muted:#59636e;--green:#16895d;--blue:#2868bd;--red:#c84646}*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--text)}button,input,textarea,select{font:inherit}.top{position:sticky;top:0;z-index:3;display:flex;gap:18px;align-items:center;padding:13px 4vw;background:var(--panel);border-bottom:1px solid var(--border)}.brand{font-weight:800;font-size:18px}.brand span{color:var(--green)}.search{flex:1;max-width:600px}.input{width:100%;color:var(--text);background:var(--page);border:1px solid var(--border);border-radius:7px;padding:9px 11px}.button{border:1px solid var(--border);border-radius:7px;padding:8px 12px;color:var(--text);background:var(--raised);cursor:pointer}.primary{background:var(--green);color:#082016;border-color:var(--green);font-weight:700}.danger{color:var(--red)}.layout{display:grid;grid-template-columns:230px 1fr;min-height:calc(100vh - 62px)}aside{padding:26px 18px;background:var(--panel);border-right:1px solid var(--border)}aside button{width:100%;margin-bottom:8px;text-align:left}.main{padding:42px 5vw;min-width:0}.hero{display:flex;justify-content:space-between;gap:20px;align-items:end}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:25px}.cardx{padding:18px;background:var(--panel);border:1px solid var(--border);border-radius:10px;cursor:pointer}.cardx:hover{background:var(--hover)}.title{color:var(--blue);font-weight:750}.dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}.badge{border:1px solid var(--border);border-radius:20px;padding:2px 7px;color:var(--muted)}dialog{width:min(720px,94vw);max-height:90vh;overflow:auto;color:var(--text);background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:23px}dialog::backdrop{background:#000a}.rowx{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.stack{display:grid;gap:11px}.file{display:flex;justify-content:space-between;gap:12px;padding:10px;border-bottom:1px solid var(--border)}.file a{color:var(--blue)}.auth{min-height:100vh;display:grid;place-items:center}.authbox{width:min(420px,92vw);padding:28px;background:var(--panel);border:1px solid var(--border);border-radius:12px}.toastx{position:fixed;right:20px;bottom:20px;padding:12px 16px;background:var(--raised);border:1px solid var(--border);border-left:3px solid var(--green);border-radius:7px;z-index:10}.owner{font-size:12px;color:var(--muted)}pre{white-space:pre-wrap;word-break:break-word;background:var(--page);padding:14px;border:1px solid var(--border);border-radius:8px;max-height:45vh;overflow:auto}@media(max-width:720px){.layout{grid-template-columns:1fr}aside{display:flex;gap:8px;overflow:auto;border-right:0;border-bottom:1px solid var(--border);padding:10px}aside button{min-width:max-content;margin:0}.main{padding:25px 16px}.hero{align-items:start;flex-direction:column}.top{flex-wrap:wrap}.search{order:3;flex-basis:100%}}
</style>
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js" integrity="sha384-IQsoLXl5PILFhosVNubq5LC7Qb9DXgDA9i+tQ8Zj3iwWAwPtgFTxbJ8NT4GN1R8p" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.min.js" integrity="sha384-cVKIPhGWiC2Al4u+LWgxfKTRIcfu0JTxR+EQDz/bgldoEyl4H0zUF0QKbrJ0EcQF" crossorigin="anonymous"></script></head><body>
<div id="auth" class="auth"><form id="authForm" class="authbox stack"><div class="brand">super<span>projects</span></div><h1 id="authTitle">Sign in</h1><input class="input" id="username" placeholder="Username" required pattern="[A-Za-z0-9_-]{3,24}"><input class="input" id="password" type="password" placeholder="Password" minlength="12" required><button class="button primary">Continue</button><button class="button" type="button" id="authMode">Need an account? Register</button><div id="authMsg" class="muted"></div></form></div>
<div id="app" hidden><header class="top"><div class="brand">super<span>projects</span></div><input id="search" class="input search" placeholder="Search public projects, owners, languages..."><span id="who"></span><button class="button" id="theme">Theme</button><button class="button" id="logout">Sign out</button></header><div class="layout"><aside><button class="button primary" id="newProject">+ New project</button><button class="button" data-view="mine">My projects</button><button class="button" data-view="explore">Explore public</button><a class="button" href="/api/export.xml" style="display:block;text-decoration:none">Download my XML</a></aside><main class="main"><div class="hero"><div><div class="muted">YOUR CREATIVE HOME</div><h1 id="heading">Your projects</h1><p class="muted" id="subheading">Create repositories, upload folders, and share your work.</p></div><button class="button primary" id="newProject2">+ New project</button></div><div id="projects" class="grid"></div></main></div></div>
<dialog id="create"><form id="createForm" class="stack"><h2>Create a project</h2><input class="input" name="name" placeholder="Project name" pattern="[A-Za-z0-9._-]{1,60}" required><textarea class="input" name="description" maxlength="240" placeholder="Description"></textarea><select class="input" name="visibility"><option value="public">Public</option><option value="private">Private</option></select><select class="input" name="language">{% for n,c in languages.items() %}<option>{{n}}</option>{% endfor %}</select><label><input type="checkbox" name="readme" checked> Add README.md</label><label><input type="checkbox" name="ignore" checked> Add .fileignore</label><div class="rowx"><button class="button primary">Create</button><button class="button" type="button" data-close>Cancel</button></div></form></dialog>
<dialog id="detail"><div class="rowx" style="justify-content:space-between"><div><div class="owner" id="detailOwner"></div><h2 id="detailName"></h2></div><button class="button" data-close>Close</button></div><p id="detailDesc" class="muted"></p><div class="rowx"><span id="detailLang"></span><span id="detailVis" class="badge"></span><a class="button" id="zip">Download ZIP</a><button class="button" id="uploadBtn">Upload folder/files</button><button class="button danger" id="deleteBtn">Delete</button></div><input id="folderInput" type="file" webkitdirectory directory multiple hidden><input id="filesInput" type="file" multiple hidden><p class="muted">Folder upload works in Chromium browsers. You can also choose individual files.</p><button class="button" id="filesBtn">Choose individual files</button><div id="fileList" style="margin-top:15px"></div><h3 id="previewTitle" hidden>Preview</h3><pre id="preview" hidden></pre></dialog>
<script>
"use strict";
let me=null, view="mine", current=null, mode="login";
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>\"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
async function api(url,opt={}){const r=await fetch(url,{credentials:"same-origin",...opt});const ct=r.headers.get("content-type")||"";const x=ct.includes("json")?await r.json():await r.text();if(!r.ok)throw Error(x.error||x||"Request failed");return x}
function toast(s){const d=document.createElement("div");d.className="toastx";d.textContent=s;document.body.append(d);setTimeout(()=>d.remove(),3000)}
async function boot(){try{const x=await api("/api/me");if(x.user){me=x.user;showApp()}}catch(e){}}
function showApp(){$("#auth").hidden=true;$("#app").hidden=false;$("#who").textContent=me;loadProjects()}
$("#authMode").onclick=()=>{mode=mode==="login"?"register":"login";$("#authTitle").textContent=mode==="login"?"Sign in":"Create account";$("#authMode").textContent=mode==="login"?"Need an account? Register":"Already registered? Sign in"};
$("#authForm").onsubmit=async e=>{e.preventDefault();try{const x=await api("/api/auth/"+mode,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:$("#username").value,password:$("#password").value})});me=x.user;showApp()}catch(err){$("#authMsg").textContent=err.message}};
$("#logout").onclick=async()=>{await api("/api/auth/logout",{method:"POST"});location.reload()};
async function loadProjects(){const q=encodeURIComponent($("#search").value);const arr=await api(`/api/projects?view=${view}&q=${q}`);$("#heading").textContent=view==="mine"?"Your projects":"Explore projects";const box=$("#projects");box.innerHTML="";for(const p of arr){const d=document.createElement("article");d.className="cardx";d.innerHTML=`<div class="owner">${esc(p.owner)}</div><div class="title">${esc(p.name)}</div><p class="muted">${esc(p.description||"No description")}</p><div><span class="dot" style="background:${esc(p.color)}"></span>${esc(p.language)} <span class="badge">${esc(p.visibility)}</span></div>`;d.onclick=()=>openProject(p.id);box.append(d)}if(!arr.length)box.innerHTML='<p class="muted">No projects found.</p>'}
let timer;$("#search").oninput=()=>{clearTimeout(timer);timer=setTimeout(loadProjects,180)};document.querySelectorAll("[data-view]").forEach(b=>b.onclick=()=>{view=b.dataset.view;loadProjects()});
function openCreate(){$("#create").showModal()}$("#newProject").onclick=openCreate;$("#newProject2").onclick=openCreate;document.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>b.closest("dialog").close());
$("#createForm").onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target),body=Object.fromEntries(f);body.readme=f.has("readme");body.ignore=f.has("ignore");try{const p=await api("/api/projects",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});$("#create").close();e.target.reset();await loadProjects();openProject(p.id)}catch(err){toast(err.message)}};
async function openProject(id){const p=await api("/api/projects/"+id);current=p;$("#detailOwner").textContent=p.owner+" / repository";$("#detailName").textContent=p.name;$("#detailDesc").textContent=p.description||"No description";$("#detailLang").innerHTML=`<span class="dot" style="background:${p.color}"></span>${esc(p.language)}`;$("#detailVis").textContent=p.visibility;$("#zip").href=`/api/projects/${id}/zip`;$("#uploadBtn").hidden=p.owner!==me;$("#filesBtn").hidden=p.owner!==me;$("#deleteBtn").hidden=p.owner!==me;renderFiles(p);$("#detail").showModal()}
function renderFiles(p){const b=$("#fileList");b.innerHTML="<h3>Files</h3>";for(const f of p.files){const d=document.createElement("div");d.className="file";const path=encodeURIComponent(f.path).replaceAll("%2F","/");d.innerHTML=`<a href="#">${esc(f.path)}</a><span>${f.size} bytes · <a href="/api/projects/${p.id}/file/${path}">Download</a></span>`;d.querySelector("a").onclick=async e=>{e.preventDefault();try{const x=await api(`/api/projects/${p.id}/preview/${path}`);$("#previewTitle").hidden=false;$("#previewTitle").textContent=f.path;$("#preview").hidden=false;$("#preview").textContent=x.content}catch(err){toast(err.message)}};b.append(d)}}
async function upload(input){if(!current||!input.files.length)return;const fd=new FormData();for(const f of input.files)fd.append("files",f,f.webkitRelativePath||f.name);try{await api(`/api/projects/${current.id}/upload`,{method:"POST",body:fd});toast("Upload complete");openProject(current.id);loadProjects()}catch(err){toast(err.message)}input.value=""}
$("#uploadBtn").onclick=()=>$("#folderInput").click();$("#filesBtn").onclick=()=>$("#filesInput").click();$("#folderInput").onchange=e=>upload(e.target);$("#filesInput").onchange=e=>upload(e.target);
$("#deleteBtn").onclick=async()=>{if(current&&confirm(`Delete ${current.name}?`)){await api(`/api/projects/${current.id}`,{method:"DELETE"});$("#detail").close();loadProjects()}};
$("#theme").onclick=()=>{const h=document.documentElement;h.dataset.theme=h.dataset.theme==="dark"?"light":"dark"};boot();
</script></body></html>'''

@APP.get("/")
def index(): return render_template_string(HTML,languages=LANG)
@APP.get("/api/me")
def me(): return jsonify(user=current_user())
@APP.post("/api/auth/register")
def register():
    d=request.get_json(silent=True) or {}; name=str(d.get("username","")).strip(); pw=str(d.get("password",""))
    if not USERNAME_RE.fullmatch(name): return jsonify(error="Username must be 3-24 letters, numbers, underscores, or hyphens."),400
    if len(pw.encode())<12: return jsonify(error="Password must be at least 12 characters."),400
    root=read_xml()
    if user_node(root,name): return jsonify(error="That username already exists."),409
    u=ET.SubElement(root.find("users"),"user",name=name,password=hash_password(pw),created=now()); ET.SubElement(u,"projects"); write_xml(root)
    (PROJECTS/secure_filename(name)).mkdir(exist_ok=True); session.clear(); session["username"]=name; return jsonify(user=name),201
@APP.post("/api/auth/login")
def login():
    d=request.get_json(silent=True) or {}; name=str(d.get("username","")).strip(); root=read_xml(); u=user_node(root,name)
    if u is None or not verify_password(str(d.get("password","")),u.get("password","")): return jsonify(error="Invalid username or password."),401
    session.clear(); session["username"]=name; return jsonify(user=name)
@APP.post("/api/auth/logout")
def logout(): session.clear(); return jsonify(ok=True)
@APP.get("/api/projects")
def list_projects():
    root=read_xml(); q=request.args.get("q","").lower().strip(); mine=request.args.get("view","mine")=="mine"; out=[]
    for u in root.find("users"):
        ps=u.find("projects")
        if ps is None: continue
        for p in ps:
            if mine and u.get("name")!=current_user(): continue
            if not mine and p.get("visibility")!="public": continue
            j=project_json(u,p)
            if q and q not in " ".join(map(str,j.values())).lower(): continue
            j["color"]=LANG.get(j["language"],LANG["Other"]); out.append(j)
    out.sort(key=lambda x:x.get("updated") or "",reverse=True); return jsonify(out)
@APP.post("/api/projects")
@login_required
def create_project():
    d=request.get_json(silent=True) or {}; name=str(d.get("name","")).strip()
    if not PROJECT_RE.fullmatch(name): return jsonify(error="Project name must use 1-60 letters, numbers, dots, hyphens, or underscores."),400
    root=read_xml(); u=user_node(root,current_user()); ps=u.find("projects")
    if any(p.get("name","").lower()==name.lower() for p in ps): return jsonify(error="You already have a project with that name."),409
    pid=slug_id(); t=now(); lang=str(d.get("language","Other")); lang=lang if lang in LANG else "Other"
    p=ET.SubElement(ps,"project",id=pid,name=name,description=str(d.get("description",""))[:240],visibility="private" if d.get("visibility")=="private" else "public",language=lang,created=t,updated=t)
    folder=project_dir(current_user(),pid); folder.mkdir(parents=True)
    if d.get("readme"): (folder/"README.md").write_text(f"# {name}\n\n{p.get('description') or 'A new project.'}\n",encoding="utf-8")
    if d.get("ignore"): (folder/".fileignore").write_text("# Excluded from ZIP downloads\n.DS_Store\nThumbs.db\n__pycache__/\n*.pyc\n.env\n",encoding="utf-8")
    write_xml(root); return jsonify(project_json(u,p)),201
@APP.get("/api/projects/<pid>")
def project_detail(pid):
    root,u,p=get_project(pid)
    if not can_view(u,p): abort(404)
    folder=project_dir(u.get("name"),pid); files=[]
    if folder.exists():
        for f in sorted(folder.rglob("*")):
            if f.is_file(): files.append({"path":f.relative_to(folder).as_posix(),"size":f.stat().st_size})
    j=project_json(u,p); j.update(files=files,color=LANG.get(j["language"],LANG["Other"])); return jsonify(j)
@APP.delete("/api/projects/<pid>")
@login_required
def delete_project(pid):
    root,u,p=get_project(pid); owner_only(u)
    if p is None: abort(404)
    u.find("projects").remove(p); write_xml(root); shutil.rmtree(project_dir(u.get("name"),pid),ignore_errors=True); return jsonify(ok=True)
@APP.post("/api/projects/<pid>/upload")
@login_required
def upload_files(pid):
    root,u,p=get_project(pid); owner_only(u); folder=project_dir(u.get("name"),pid); folder.mkdir(parents=True,exist_ok=True); count=0
    for item in request.files.getlist("files"):
        parts=[secure_filename(x) for x in (item.filename or "").replace("\\","/").split("/") if x not in ("",".","..")]
        if not parts or any(not x for x in parts): continue
        target=folder.joinpath(*parts).resolve()
        if folder not in target.parents: continue
        target.parent.mkdir(parents=True,exist_ok=True); item.save(target); count+=1
    if not count: return jsonify(error="Choose at least one valid file."),400
    p.set("language",detect_language(folder)); touch(root,p); return jsonify(uploaded=count)
@APP.get("/api/projects/<pid>/file/<path:filename>")
def download_file(pid,filename):
    root,u,p=get_project(pid)
    if not can_view(u,p): abort(404)
    folder=project_dir(u.get("name"),pid); rel=safe_rel(filename); target=(folder/Path(*rel.parts)).resolve()
    if folder not in target.parents or not target.is_file(): abort(404)
    return send_file(target,as_attachment=True,download_name=target.name)
@APP.get("/api/projects/<pid>/preview/<path:filename>")
def preview_file(pid,filename):
    root,u,p=get_project(pid)
    if not can_view(u,p): abort(404)
    folder=project_dir(u.get("name"),pid); rel=safe_rel(filename); target=(folder/Path(*rel.parts)).resolve()
    if folder not in target.parents or not target.is_file(): abort(404)
    if target.stat().st_size>512000: return jsonify(error="Preview is limited to 500 KB."),413
    try: text=target.read_text("utf-8")
    except UnicodeDecodeError: return jsonify(error="Binary files cannot be previewed."),415
    return jsonify(content=text)
@APP.get("/api/projects/<pid>/zip")
def download_zip(pid):
    root,u,p=get_project(pid)
    if not can_view(u,p): abort(404)
    folder=project_dir(u.get("name"),pid); patterns=ignore_patterns(folder); mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob("*"):
            if f.is_file():
                rel=f.relative_to(folder)
                if not ignored(rel,patterns): z.write(f,(Path(p.get("name"))/rel).as_posix())
    mem.seek(0); return send_file(mem,mimetype="application/zip",as_attachment=True,download_name=secure_filename(p.get("name"))+".zip")
@APP.get("/api/export.xml")
@login_required
def export_xml():
    root=read_xml(); u=user_node(root,current_user()); export=ET.Element("superProjectsExport",generated=now()); copy=ET.SubElement(export,"user",name=u.get("name"),created=u.get("created","")); cps=ET.SubElement(copy,"projects")
    for p in u.find("projects"): cps.append(ET.fromstring(ET.tostring(p)))
    data=ET.tostring(export,encoding="utf-8",xml_declaration=True); return Response(data,mimetype="application/xml",headers={"Content-Disposition":f'attachment; filename="{secure_filename(current_user())}-projects.xml"'})
if __name__=="__main__":
    init_db(); APP.run(host=os.environ.get("HOST","127.0.0.1"),port=int(os.environ.get("PORT","5000")),debug=os.environ.get("FLASK_DEBUG")=="1")
