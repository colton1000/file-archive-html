"""Python HTML Studio: create named HTML/CSS/JS bundles and preview them."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse, base64, errno, json, mimetypes, re, webbrowser, traceback
from datetime import datetime
from threading import Thread
import shutil
import io
import zipfile

ROOT = Path(__file__).resolve().parent
DB = ROOT / "projects.json"
INDEX = ROOT / "index.html"
BACKUP_DIR = ROOT / "backups"
PROJECTS_DIR = ROOT / "projects"

def read_db():
    if not DB.exists():
        return {"projects": []}
    try:
        data = json.loads(DB.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {DB.name} at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    except OSError as error:
        raise OSError(f"Could not read {DB}: {error}") from error

    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        raise ValueError(f"{DB.name} must contain a top-level 'projects' list")

    for project in data["projects"]:
        if not isinstance(project, dict):
            raise ValueError(f"Each project in {DB.name} must be an object")
        project.setdefault("html", "")
        project.setdefault("css", [])
        project.setdefault("javascript", [])
        project.setdefault("icons", [])
    return data

def write_db(data):
    temporary = DB.with_suffix(DB.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(DB)
    # Keep projects/<project-id>/ synchronized with projects.json.
    if "write_project_folder" in globals():
        sync_project_folders(data)

def backup_projects():
    if not DB.is_file():
        raise FileNotFoundError(f"Projects file not found: {DB}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = BACKUP_DIR / f"projects-{timestamp}.json"
    shutil.copy2(DB, destination)
    print(f"Backed up projects to: {destination}")
    return destination

def slug(name):
    value=re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()
    return value or "project"

def unique_id(data, name, keep=None):
    base=slug(name); candidate=base; used={p["id"] for p in data["projects"] if p.get("id") != keep}; n=2
    while candidate in used: candidate=f"{base}-{n}"; n+=1
    return candidate

def find(data, key):
    return next((p for p in data["projects"] if p.get("id")==key or p.get("name")==key), None)

def read_source(source):
    if "\n" in source or "\r" in source:
        return source
    try:
        path=Path(source)
        if path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError as error:
        if error.errno not in (errno.EINVAL, errno.ENAMETOOLONG) and getattr(error,"winerror",None) not in (123,206):
            raise
    return source

def project_folder(project):
    """Return the safe folder used by a project."""
    return PROJECTS_DIR / slug(project.get("id") or project.get("name") or "project")


def write_project_folder(project):
    """Write a project as normal HTML, CSS, JS, assets, and metadata files."""
    folder = project_folder(project)
    folder.mkdir(parents=True, exist_ok=True)

    css = "\n\n".join(
        f"/* {item.get('name', 'style.css')} */\n{resolve_icon_references(item.get('code', ''), project)}"
        for item in project.get("css", [])
    )
    javascript = "\n\n".join(
        f"// {item.get('name', 'script.js')}\n{resolve_icon_references(item.get('code', ''), project)}"
        for item in project.get("javascript", [])
    )
    body = resolve_icon_references(project.get("html", ""), project)
    title = project.get("name", "Project")
    page = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{title}</title>\n<link rel=\"stylesheet\" href=\"styles.css\">\n"
        "</head>\n<body>\n"
        f"{body}\n<script src=\"script.js\"></script>\n</body>\n</html>\n"
    )
    (folder / "index.html").write_text(page, encoding="utf-8")
    (folder / "styles.css").write_text(css + ("\n" if css else ""), encoding="utf-8")
    (folder / "script.js").write_text(javascript + ("\n" if javascript else ""), encoding="utf-8")
    (folder / "project.json").write_text(
        json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return folder


def sync_project_folders(data=None):
    """Create/update a disk folder for every database project."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    data = data or read_db()
    for project in data.get("projects", []):
        write_project_folder(project)


def load_folder_projects(data):
    """Load projects/project-id/project.json files into the API project list."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {item.get("id"): item for item in data.get("projects", [])}
    for metadata in PROJECTS_DIR.glob("*/project.json"):
        try:
            project = json.loads(metadata.read_text(encoding="utf-8"))
            if isinstance(project, dict) and project.get("id"):
                by_id[project["id"]] = project
        except (OSError, json.JSONDecodeError):
            continue
    return {"projects": list(by_id.values())}


def download_project(project):
    """Export/update a project inside the projects folder."""
    data = read_db()
    selected = find(data, project)
    if not selected:
        raise SystemExit(f"Project not found: {project}")
    folder = write_project_folder(selected)
    print(f"Downloaded project to: {folder}")
    return folder


def project_zip(project):
    """Return an in-memory ZIP of a project folder."""
    folder = write_project_folder(project)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in folder.rglob("*"):
            if path.is_file():
                archive.write(path, Path(folder.name) / path.relative_to(folder))
    return output.getvalue()

def add_project(name, html=""):
    data=read_db(); pid=unique_id(data,name)
    data["projects"].append({"id":pid,"name":name,"html":html,"css":[],"javascript":[],"icons":[]})
    write_db(data); print(f"Created project: {name} ({pid})")

def add_icon(project,name,source):
    data=read_db(); p=find(data,project)
    if not p: raise SystemExit(f"Project not found: {project}")
    icon_name=slug(name)
    if not name.strip(): raise ValueError("Icon name must not be empty")
    path=Path(source)
    if not path.is_file(): raise FileNotFoundError(f"Icon file not found: {path}")
    mime_type,_=mimetypes.guess_type(path.name)
    allowed_types={"image/gif","image/jpeg","image/png","image/svg+xml","image/vnd.microsoft.icon","image/webp","image/x-icon"}
    if mime_type not in allowed_types: raise ValueError("Icon files must be GIF, JPEG, PNG, SVG, ICO, or WebP")
    icons=p.setdefault("icons",[])
    if not isinstance(icons,list): raise ValueError(f"Invalid icons data in project: {p['name']}")
    icon={"name":icon_name,"mime_type":mime_type,"data":base64.b64encode(path.read_bytes()).decode("ascii")}
    existing=next((item for item in icons if item.get("name")==icon_name),None)
    if existing: icons[icons.index(existing)]=icon; action="Updated"
    else: icons.append(icon); action="Added"
    write_db(data); print(f"{action} icon '{icon_name}' in {p['name']}")

def set_html(project, source):
    data=read_db(); p=find(data,project)
    if not p: raise SystemExit(f"Project not found: {project}")
    p["html"]=read_source(source)
    write_db(data); print(f"Updated HTML in {p['name']}")

def add_asset(project, kind, name, source):
    data=read_db(); p=find(data,project)
    if not p: raise SystemExit(f"Project not found: {project}")
    if not name.strip():
        raise ValueError("Asset name must not be empty")
    code=read_source(source)
    key="javascript" if kind=="js" else "css"
    assets = p.setdefault(key, [])
    if not isinstance(assets, list):
        raise ValueError(f"Invalid {key} data in project: {p['name']}")
    old=next((x for x in assets if x.get("name")==name),None)
    if old: old["code"]=code; action="Updated"
    else: assets.append({"name":name,"code":code}); action="Added"
    write_db(data); print(f"{action} {kind.upper()} '{name}' in {p['name']}")

def remove_asset(project,kind,name):
    data=read_db(); p=find(data,project)
    if not p: raise SystemExit(f"Project not found: {project}")
    key={"css":"css","js":"javascript","icon":"icons"}.get(kind)
    if key is None: raise ValueError(f"Unsupported asset type: {kind}")
    before=len(p.get(key,[])); p[key]=[x for x in p.get(key,[]) if x.get("name")!=name]
    write_db(data); print("Removed" if len(p[key])<before else "Not found", name)

def list_all():
    for p in read_db()["projects"]:
        print(f"{p['id']}: {p['name']} | CSS: {', '.join(x['name'] for x in p['css']) or '-'} | JS: {', '.join(x['name'] for x in p['javascript']) or '-'} | Icons: {', '.join(x['name'] for x in p.get('icons',[])) or '-'}")

def resolve_icon_references(source,project):
    for icon in project.get("icons",[]):
        data_uri=f"data:{icon['mime_type']};base64,{icon['data']}"
        source=source.replace(f"icon:{icon['name']}",data_uri)
    return source

def export_project(project,out):
    data=read_db(); p=find(data,project)
    if not p: raise SystemExit(f"Project not found: {project}")
    css='\n'.join(f"/* {x['name']} */\n{resolve_icon_references(x['code'],p)}" for x in p['css']); js='\n'.join(f"// {x['name']}\n{resolve_icon_references(x['code'],p)}" for x in p['javascript'])
    html=resolve_icon_references(p["html"],p)
    page=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{p["name"]}</title><style>{css}</style></head><body>{html}<script>{js}</script></body></html>'
    Path(out).write_text(page,encoding="utf-8"); print(f"Exported {out}")

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        request_path = unquote(urlparse(self.path).path)
        if request_path in ("", "/", "/index.html"):
            if not INDEX.is_file():
                self.send_error(404, f"Studio page is missing: {INDEX.name}")
                return
            body = INDEX.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if request_path == "/api/projects":
            data = load_folder_projects(read_db())
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if request_path.startswith("/api/download/"):
            project_id = request_path.removeprefix("/api/download/")
            project = find(load_folder_projects(read_db()), project_id)
            if not project:
                self.send_error(404, "Project not found")
                return
            body = project_zip(project)
            filename = slug(project.get("name", project_id)) + ".zip"
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()
    def log_message(self,fmt,*args): pass

def start_server(port):
    if not INDEX.is_file():
        raise FileNotFoundError(
            f"Missing {INDEX.name}. Keep studio.py, index.html, and projects.json in the same folder."
        )
    handler = lambda *args, **kwargs: Handler(*args, directory=str(ROOT), **kwargs)
    server=ThreadingHTTPServer(("127.0.0.1",port),handler)
    port=server.server_address[1]; url=f"http://127.0.0.1:{port}/"
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return server,thread,url

def stop_server(server,thread):
    server.shutdown()
    server.server_close()
    thread.join()

def serve(port):
    server,thread,url=start_server(port)
    print(f"Studio running at {url}\nPress Ctrl+C to stop.")
    try:
        if not webbrowser.open(url): print(f"Open this URL in your browser: {url}")
        thread.join()
    except KeyboardInterrupt: print("\nStopped.")
    finally:
        stop_server(server,thread)

def multiline_input(label):
    """Read pasted code safely; two empty lines or .end saves it."""
    print(label)
    print("Enter or paste code. Press Enter twice on empty lines to save.")
    print("Type .end on its own line to save immediately.")
    lines = []
    pending_blank = False

    while True:
        try:
            line = input("... ")
        except EOFError:
            break

        if line.strip() == ".end":
            break

        if line == "":
            if pending_blank:
                # Remove the terminator's first empty line. Existing blank lines
                # inside pasted code remain intact.
                if lines and lines[-1] == "":
                    lines.pop()
                break
            pending_blank = True
            lines.append("")
            continue

        pending_blank = False
        lines.append(line)

    return "\n".join(lines)

def interactive(server_url=None):
    print("Python HTML Studio\nCommands: new, html, css, js, icon, remove, list, download, backup projects, serve, export, quit")
    while True:
        try: command=input("studio> ").strip().lower()
        except (EOFError,KeyboardInterrupt): break
        try:
            if command=="new": add_project(input("Project name: ").strip())
            elif command=="html":
                project=input("Project ID/name to update (create it with 'new' first): ").strip()
                source=multiline_input(f"Main HTML page for {project}")
                set_html(project, source)
            elif command in ("css","js"):
                project=input("Project ID/name: ").strip()
                name=input("Asset name: ").strip()
                source=multiline_input(f"{command.upper()} code")
                add_asset(project, command, name, source)
            elif command=="icon":
                project=input("Project ID/name: ").strip()
                name=input("Icon name: ").strip()
                source=input("Icon file path: ").strip()
                add_icon(project,name,source)
            elif command=="remove": remove_asset(input("Project ID/name: ").strip(),input("Type (css/js): ").strip(),input("Asset name: ").strip())
            elif command=="list": list_all()
            elif command=="download": download_project(input("Project ID/name: ").strip())
            elif command=="backup projects": backup_projects()
            elif command=="serve":
                if server_url: print(f"Studio is already running at {server_url}")
                else: serve(8000)
            elif command=="export": export_project(input("Project ID/name: ").strip(),input("Output HTML: ").strip())
            elif command in ("quit","exit"): break
            elif command: print("Unknown command")
        except Exception as e: print("Error:",e)

def main():
    sync_project_folders()
    ap=argparse.ArgumentParser(description="Build and preview named HTML/CSS/JS projects")
    sub=ap.add_subparsers(dest="cmd")
    n=sub.add_parser("new"); n.add_argument("name")
    h=sub.add_parser("html"); h.add_argument("project"); h.add_argument("source")
    for kind in ("css","js"):
        a=sub.add_parser(kind); a.add_argument("project"); a.add_argument("name"); a.add_argument("source")
    r=sub.add_parser("remove"); r.add_argument("project"); r.add_argument("kind",choices=["css","js","icon"]); r.add_argument("name")
    i=sub.add_parser("icon"); i.add_argument("project"); i.add_argument("name"); i.add_argument("source")
    sub.add_parser("list")
    backup=sub.add_parser("backup"); backup.add_argument("target",choices=["projects"])
    sv=sub.add_parser("serve"); sv.add_argument("--port",type=int,default=8000)
    ex=sub.add_parser("export"); ex.add_argument("project"); ex.add_argument("output")
    dl=sub.add_parser("download"); dl.add_argument("project")
    sub.add_parser("interactive", help="open the command-line project editor")
    a=ap.parse_args()
    if a.cmd=="new": add_project(a.name)
    elif a.cmd=="html": set_html(a.project,a.source)
    elif a.cmd in ("css","js"): add_asset(a.project,a.cmd,a.name,a.source)
    elif a.cmd=="icon": add_icon(a.project,a.name,a.source)
    elif a.cmd=="remove": remove_asset(a.project,a.kind,a.name)
    elif a.cmd=="list": list_all()
    elif a.cmd=="backup": backup_projects()
    elif a.cmd=="serve": serve(a.port)
    elif a.cmd=="export": export_project(a.project,a.output)
    elif a.cmd=="download": download_project(a.project)
    elif a.cmd=="interactive": interactive()
    else:
        server,thread,url=start_server(8000)
        print(f"Studio running at {url}")
        try:
            if not webbrowser.open(url): print(f"Open this URL in your browser: {url}")
            interactive(server_url=url)
        finally:
            stop_server(server,thread)
if __name__=="__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            input("\nAn error occurred. Press Enter to close...")
        except (EOFError, KeyboardInterrupt):
            pass
