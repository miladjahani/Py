"""
SPARK AUTONOMOUS CODING AGENT (agent.py)
----------------------------------------
یک ابرمهارت جامع (All-in-One Autonomous Agent Skill) شامل:
- موتور شناختی ReAct (Thought -> Action -> Observation)
- فشردهسازی خودکار حافظه و برش کانتکست (Context Pruning & Summarization)
- مدیریت فایل و پچ جراحی (Surgical Patching)
- ناوبری ساختار کد، اسکلت توابع (AST Outline) و جستجوی Regex
- بازرسی امنیتی و اعتبارسنجی نحوی استاتیک (AST Security Guard)
- رانر سرورهای پسزمینه (Vite/Node/FastAPI Dev Servers)
- رانر تستهای واحد (Pytest) و تستر API (HTTP Client)
- بازرسی بصری چندحالته و ثبت خطاهای فرانتاند (Playwright Multimodal UI)
- چکپوینتهای خودکار و بازیابی نسخه (Git Rollback)
- چرخه خودترمیمی و ردیابی خطوط تغییریافته (Self-Healing & Git Diff)
"""

import ast
import base64
import collections
import difflib
import fnmatch
import json
import os
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set, Tuple, Union

import httpx
try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageToolCall
except ImportError:
    OpenAI = None  # type: ignore
    ChatCompletionMessageToolCall = None  # type: ignore

from pydantic import BaseModel, Field

def get_model_schema(model_cls) -> Dict[str, Any]:
    if hasattr(model_cls, 'model_json_schema'):
        return model_cls.model_json_schema()
    return model_cls.schema()


# =====================================================================
# بخش ۱: گاردریلهای امنیتی و تحلیل استاتیک کد (AST Security & Syntax)
# =====================================================================

class ASTSecurityGuard:
    """تحلیل استاتیک درخت نحو انتزاعی بدون اجرای کد جهت مسدودسازی دستورات پرخطر."""

    BANNED_BUILTINS: Set[str] = {"eval", "exec", "compile", "__import__"}
    DANGEROUS_CALLS: Dict[str, Set[str]] = {
        "os": {"system", "popen", "spawn", "remove", "rmdir", "unlink"},
        "shutil": {"rmtree", "move"},
        "subprocess": {"run", "Popen", "call"},
    }
    BANNED_ATTRIBUTES: Set[str] = {"__subclasses__", "__globals__", "__code__", "__bases__"}

    @classmethod
    def validate_syntax(cls, code: str) -> Tuple[bool, Optional[str]]:
        try:
            tree = ast.parse(code)
            if not tree.body:
                return False, "کد ارسالی فاقد هرگونه عبارت اجرایی پایتون است."
            return True, None
        except SyntaxError as exc:
            pointer = " " * ((exc.offset or 1) - 1) + "^"
            return False, f"SyntaxError on line {exc.lineno}:\n  {exc.text or ''}  {pointer}\n{exc.msg}"

    @classmethod
    def audit_security(cls, code: str) -> Tuple[bool, List[str]]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, ["خطای سینتکسی در حین ارزیابی امنیتی."]

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                mod_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    mod_name = node.func.value.id
                    func_name = node.func.attr

                if func_name in cls.BANNED_BUILTINS:
                    violations.append(f"خط {node.lineno}: استفاده از تابع ممنوعه '{func_name}'")
                if mod_name in cls.DANGEROUS_CALLS and func_name in cls.DANGEROUS_CALLS[mod_name]:
                    violations.append(f"خط {node.lineno}: فراخوانی متد سیستمی پرخطر '{mod_name}.{func_name}'")

            elif isinstance(node, ast.Attribute) and node.attr in cls.BANNED_ATTRIBUTES:
                violations.append(f"خط {node.lineno}: تلاش برای دسترسی به صفت سیستمی '{node.attr}'")

        return len(violations) == 0, violations


# =====================================================================
# بخش ۲: مدلهای Pydantic برای ورودی و خروجی ابزارها
# =====================================================================

class ReadFileInput(BaseModel):
    file_path: str = Field(..., description="مسیر فایل نسبت به ریشه پروژه")
    start_line: Optional[int] = Field(None, description="شماره خط شروع (1-indexed)")
    end_line: Optional[int] = Field(None, description="شماره خط پایان")

class WriteFileInput(BaseModel):
    file_path: str = Field(..., description="مسیر فایل جهت ساخت یا بازنویسی کامل")
    content: str = Field(..., description="محتوای کامل فایل")

class PatchFileInput(BaseModel):
    file_path: str = Field(..., description="مسیر فایل هدف جهت اعمال پچ")
    target_block: str = Field(..., description="بخش کدی که باید دقیقاً پیدا شود (باید یکتا باشد)")
    replacement_block: str = Field(..., description="کد جایگزین")

class StartServerInput(BaseModel):
    command: str = Field(..., description="دستور شل اجرای سرور (مانند 'npm run dev' یا 'uvicorn main:app --port 8000')")
    cwd: str = Field(".", description="پوشه محل اجرای دستور")
    port: int = Field(..., description="پورت مورد انتظار جهت بررسی وضعیت آمادگی")
    server_id: Optional[str] = Field(None, description="شناسه یکتا برای سرور")
    ready_timeout: int = Field(25, description="سقف ثانیه انتظار برای باز شدن پورت")

class InspectUIInput(BaseModel):
    target: str = Field(..., description="آدرس URL یا مسیر نسبی فایل HTML (مانند index.html یا http://localhost:5173)")
    viewport_width: int = Field(1280, description="عرض پنجره مرورگر (375 موبایل، 1280 دسکتاپ)")
    viewport_height: int = Field(800, description="ارتفاع پنجره مرورگر")
    click_selector: Optional[str] = Field(None, description="سلکتور CSS برای کلیک قبل از اسکرینشات")


# =====================================================================
# بخش ۳: جعبه ابزار جامع زیرساختی (Core Engineering Toolset)
# =====================================================================

@dataclass
class ManagedDevServer:
    server_id: str
    command: str
    port: int
    process: subprocess.Popen
    log_buffer: Deque[str] = field(default_factory=lambda: collections.deque(maxlen=200))


class CoreToolbox:
    def __init__(self, workspace_root: Path, client: Optional[Any] = None):
        self.root = workspace_root.resolve()
        self.client = client
        self.active_servers: Dict[str, ManagedDevServer] = {}
        self.task_state_file = self.root / ".spark_tasks.json"

    def _resolve_safe(self, rel_path: str) -> Path:
        target = (self.root / rel_path).resolve()
        if not target.is_relative_to(self.root):
            raise PermissionError(f"دسترسی به مسیر خارج از ریشه مجاز نیست: {rel_path}")
        return target

    # --- عملیات فایل ---
    def read_file(self, **kwargs) -> Dict[str, Any]:
        params = ReadFileInput(**kwargs)
        target = self._resolve_safe(params.file_path)
        if not target.exists():
            return {"success": False, "error": f"فایل {params.file_path} یافت نشد."}

        lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        start = (params.start_line - 1) if params.start_line else 0
        end = params.end_line if params.end_line else len(lines)
        numbered = "".join(f"{i + start + 1:4d} | {line}" for i, line in enumerate(lines[start:end]))
        return {"success": True, "total_lines": len(lines), "content": numbered}

    def write_file(self, **kwargs) -> Dict[str, Any]:
        params = WriteFileInput(**kwargs)
        target = self._resolve_safe(params.file_path)
        
        # اگر فایل پایتون است، اعتبارسنجی سینتکس و امنیت انجام شود
        if target.suffix == ".py":
            valid, err = ASTSecurityGuard.validate_syntax(params.content)
            if not valid:
                return {"success": False, "error": f"کد دارای خطای نحوی است و ذخیره نشد:\n{err}"}
            safe, violations = ASTSecurityGuard.audit_security(params.content)
            if not safe:
                return {"success": False, "error": f"کد دارای موارد نقض امنیتی است:\n" + "\n".join(violations)}

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(params.content, encoding="utf-8")
        return {"success": True, "message": f"فایل {params.file_path} ذخیره شد."}

    def patch_file(self, **kwargs) -> Dict[str, Any]:
        params = PatchFileInput(**kwargs)
        target = self._resolve_safe(params.file_path)
        if not target.exists():
            return {"success": False, "error": f"فایل {params.file_path} وجود ندارد."}

        content = target.read_text(encoding="utf-8")
        count = content.count(params.target_block)
        if count == 0:
            return {"success": False, "error": "بلاک هدف برای جایگزینی یافت نشد. خطوط اطراف را بررسی کنید."}
        if count > 1:
            return {"success": False, "error": f"بلاک هدف {count} بار در فایل تکرار شده است؛ لطفاً کانتکست یکتا ارائه دهید."}

        new_content = content.replace(params.target_block, params.replacement_block, 1)
        if target.suffix == ".py":
            valid, err = ASTSecurityGuard.validate_syntax(new_content)
            if not valid:
                return {"success": False, "error": f"اعمال پچ خطای نحوی ایجاد میکند:\n{err}"}

        target.write_text(new_content, encoding="utf-8")
        return {"success": True, "message": f"فایل {params.file_path} با موفقیت پچ شد."}

    # --- ناوبری و درک پروژه ---
    def list_dir_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        ignored = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
        tree = []
        for root_dir, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in ignored]
            rel = Path(root_dir).relative_to(self.root)
            depth = len(rel.parts)
            if depth > max_depth:
                continue
            indent = "  " * depth
            tree.append(f"{indent}📁 {rel.name if rel.name else '.'}/")
            if depth < max_depth:
                for f in files:
                    tree.append(f"{indent}  📄 {f}")
        return {"success": True, "tree": "\n".join(tree)}

    def grep_search(self, query: str, file_pattern: str = "*.*") -> Dict[str, Any]:
        matches = []
        pattern = re.compile(query, re.IGNORECASE)
        ignored = {".git", "node_modules", "__pycache__"}
        for root_dir, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in ignored]
            for file in files:
                if fnmatch.fnmatch(file, file_pattern):
                    p = Path(root_dir) / file
                    try:
                        for idx, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                            if pattern.search(line):
                                matches.append({"file": str(p.relative_to(self.root)), "line": idx, "text": line.strip()})
                                if len(matches) >= 35:
                                    break
                    except Exception:
                        continue
        return {"success": True, "matches": matches}

    def get_code_outline(self, file_path: str) -> Dict[str, Any]:
        target = self._resolve_safe(file_path)
        if not target.exists():
            return {"success": False, "error": f"فایل {file_path} یافت نشد."}
        try:
            tree = ast.parse(target.read_text(encoding="utf-8", errors="ignore"))
            symbols = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    symbols.append({"type": "class", "name": node.name, "methods": methods, "line": node.lineno})
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append({"type": "function", "name": node.name, "line": node.lineno})
            return {"success": True, "file": file_path, "symbols": symbols}
        except Exception as e:
            return {"success": False, "error": f"خطا در استخراج ساختار فایل: {e}"}

    # --- مدیریت برنامهریزی تسکها ---
    def init_task_plan(self, task_list: List[Dict[str, str]]) -> Dict[str, Any]:
        tasks = [{"id": i + 1, "title": t["title"], "status": "pending"} for i, t in enumerate(task_list)]
        self.task_state_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True, "tasks": tasks}

    def update_task_status(self, task_id: int, status: str) -> Dict[str, Any]:
        if not self.task_state_file.exists():
            return {"success": False, "error": "برنامهای مقداردهی نشده است."}
        tasks = json.loads(self.task_state_file.read_text(encoding="utf-8"))
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = status
                break
        self.task_state_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True, "updated_id": task_id, "status": status}

    # --- تست و کیفیتسنجی ---
    def run_unit_tests(self, test_target: str = "tests/") -> Dict[str, Any]:
        target = (self.root / test_target).resolve()
        if shutil.which("pytest"):
            cmd = ["pytest", str(target), "-v", "--tb=short"]
        else:
            if target.is_file():
                cmd = [sys.executable, "-m", "unittest", "-v", str(target)]
            else:
                cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(target), "-v"]
        res = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, check=False)
        out = res.stdout if res.stdout else res.stderr
        lines = out.splitlines() if out else []
        return {
            "success": res.returncode == 0,
            "exit_code": res.returncode,
            "summary": lines[-1] if lines else "",
            "output_tail": out[-2000:] if out else ""
        }

    def test_api_endpoint(self, url: str, method: str = "GET", json_body: Optional[Dict] = None) -> Dict[str, Any]:
        t0 = time.time()
        try:
            with httpx.Client(timeout=6.0) as c:
                resp = c.request(method.upper(), url, json=json_body)
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "data": resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text[:500]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- گیت و چکپوینت ---
    def git_checkpoint(self, message: str) -> Dict[str, Any]:
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=False)
        subprocess.run(["git", "add", "-A"], cwd=self.root, capture_output=True, check=False)
        res = subprocess.run(["git", "commit", "-m", f"[Spark] {message}"], cwd=self.root, capture_output=True, text=True, check=False)
        return {"success": res.returncode == 0, "message": message}

    def git_rollback(self) -> Dict[str, Any]:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.root, capture_output=True, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=self.root, capture_output=True, check=False)
        return {"success": True, "message": "تغییرات به آخرین چکپوینت سالم بازگردانده شد."}

    # --- مدیریت سرور توسعه محلی ---
    def start_dev_server(self, **kwargs) -> Dict[str, Any]:
        params = StartServerInput(**kwargs)
        work_dir = (self.root / params.cwd).resolve()
        sid = params.server_id or f"srv_{params.port}"

        proc = subprocess.Popen(
            params.command,
            cwd=work_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid if os.name != "nt" else None
        )

        srv = ManagedDevServer(server_id=sid, command=params.command, port=params.port, process=proc)
        def drain():
            if proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    srv.log_buffer.append(line.rstrip())
        threading.Thread(target=drain, daemon=True).start()
        self.active_servers[sid] = srv

        start_t = time.time()
        while time.time() - start_t < params.ready_timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.4)
                if s.connect_ex(("127.0.0.1", params.port)) == 0:
                    return {"success": True, "server_id": sid, "url": f"http://localhost:{params.port}"}
            time.sleep(0.3)

        return {"success": False, "error": f"سرور روی پورت {params.port} در زمان مجاز لود نشد."}

    def stop_dev_server(self, server_id: str) -> Dict[str, Any]:
        srv = self.active_servers.pop(server_id, None)
        if not srv:
            return {"success": False, "error": f"سرور {server_id} یافت نشد."}
        try:
            os.killpg(os.getpgid(srv.process.pid), signal.SIGTERM)
        except Exception:
            pass
        return {"success": True, "message": f"سرور {server_id} متوقف شد."}

    # --- بازرسی بصری با Playwright ---
    def inspect_web_ui(self, **kwargs) -> Dict[str, Any]:
        params = InspectUIInput(**kwargs)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {"success": False, "error": "پکیج playwright نصب نیست (pip install playwright && playwright install chromium)."}

        url = params.target
        if not url.startswith("http"):
            url = (self.root / params.target).resolve().as_uri()

        console_errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": params.viewport_width, "height": params.viewport_height})
                page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                page.goto(url, wait_until="networkidle", timeout=12000)
                if params.click_selector:
                    page.click(params.click_selector, timeout=3000)
                    page.wait_for_timeout(400)
                ss_bytes = page.screenshot(full_page=True)
                browser.close()

            # تحلیل ظاهر با مدل بینایی GPT-4o
            b64_img = base64.b64encode(ss_bytes).decode("utf-8")
            res = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "UI Inspector: Check layout integrity, overlapping text, and responsiveness. State issues clearly or confirm layout health."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}", "detail": "low"}}
                    ]
                }],
                max_tokens=300
            )
            return {
                "success": True,
                "console_errors": console_errors,
                "visual_critique": res.choices[0].message.content
            }
        except Exception as err:
            return {"success": False, "error": f"خطا در آزمون بصری: {err}"}


# =====================================================================
# بخش ۴: موتور خودترمیمی کد (Self-Healing Loop)
# =====================================================================

class SelfHealingEngine:
    """اجرای اسکریپت با ردیابی خطا و پچ خودکار بر پایه Git Diff."""

    def __init__(self, workspace_root: Path, client: Optional[Any] = None, model: str = "gpt-4o"):
        self.root = workspace_root
        self.client = client
        self.model = model

    def run_and_heal(self, file_path: str, max_attempts: int = 3) -> Dict[str, Any]:
        target = (self.root / file_path).resolve()
        if not target.exists():
            return {"success": False, "error": f"فایل {file_path} وجود ندارد."}

        initial_code = target.read_text(encoding="utf-8")
        current_code = initial_code
        diffs = []

        for attempt in range(1, max_attempts + 1):
            proc = subprocess.run([sys.executable, str(target)], cwd=self.root, capture_output=True, text=True, timeout=15)
            if proc.returncode == 0:
                return {
                    "success": True,
                    "attempts": attempt,
                    "stdout": proc.stdout.strip(),
                    "diffs": diffs,
                    "message": f"اسکریپت در دور {attempt} بدون خطا اجرا شد."
                }

            error_log = proc.stderr if proc.stderr else proc.stdout
            if attempt < max_attempts:
                prompt = f"Fix this Python code based on the terminal error.\nCode:\n```python\n{current_code}\n```\nError:\n```\n{error_log}\n```\nReturn ONLY the corrected Python code."
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                fixed = resp.choices[0].message.content or ""
                if "```" in fixed:
                    fixed = fixed.split("```")[1].replace("python", "").strip()

                diff = "".join(difflib.unified_diff(current_code.splitlines(True), fixed.splitlines(True), fromfile=f"a/{file_path}", tofile=f"b/{file_path}"))
                diffs.append({"attempt": attempt, "diff": diff})
                target.write_text(fixed, encoding="utf-8")
                current_code = fixed

        return {"success": False, "attempts": max_attempts, "last_error": error_log, "diffs": diffs}


# =====================================================================
# بخش ۵: فشردهسازی خودکار کانتکست (Context Compressor)
# =====================================================================

class ContextCompressor:
    """کاهش مصرف حافظه و پیشگیری از تکمیل پنجره کانتکست با معماری ۳ لایه."""

    def __init__(self, client: Optional[Any] = None, model: str = "gpt-4o-mini", trigger_tokens: int = 12000, keep_recent: int = 4):
        self.client = client
        self.model = model
        self.trigger = trigger_tokens
        self.keep_recent = keep_recent

    def estimate_tokens(self, msgs: List[Dict[str, Any]]) -> int:
        chars = sum(len(str(m.get("content") or "")) for m in msgs)
        return int(chars / 3.5)

    def compress(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.estimate_tokens(messages) < self.trigger:
            return messages

        # هرس مشاهدات حجیم قدیمی
        cutoff = len(messages) - (self.keep_recent * 2)
        for i in range(2, max(2, cutoff)):
            if messages[i].get("role") == "tool" and len(messages[i].get("content", "")) > 300:
                messages[i]["content"] = "[خروجی طولانی ابزار جهت بهینهسازی کانتکست هرس شد]"

        if self.estimate_tokens(messages) < self.trigger:
            return messages

        # خلاصهسازی بخش میانی
        slice_idx = max(2, len(messages) - (self.keep_recent * 2))
        middle = messages[2:slice_idx]
        if not middle:
            return messages

        summary_prompt = f"Condense this agent development history into files modified, errors resolved, and immediate next goals:\n{json.dumps(middle, ensure_ascii=False)[:6000]}"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.1
        )
        milestone = {"role": "system", "content": f"[MEMORIZED STATE]:\n{resp.choices[0].message.content}"}
        return [messages[0], messages[1], milestone] + messages[slice_idx:]


# =====================================================================
# بخش ۶: مهارت اصلی ایجنت (AgentSkill - The Master Orchestrator)
# =====================================================================

class AgentSkill:
    """
    ابر-مهارت اسپارک؛ تلفیق اورکستریتور ReAct، تمام ابزارهای مهندسی نرمافزار،
    گاردریلهای امنیتی و خودترمیمی در یک رابط واحد.
    """

    SYSTEM_PROMPT = """You are "Spark", an elite autonomous software engineering agent.
You independently plan, build, refactor, test, visually inspect, and deliver production software.

Your ReAct Loop:
1. **Thought:** Reason about what needs to be done. Check the directory tree or outline if necessary.
2. **Action:** Call the most specific tool available (prefer `patch_file` over `write_file`).
3. **Observation:** Critically evaluate the tool output. If errors occur, diagnose and repair immediately.

When testing web UIs, start the server (`start_dev_server`), inspect visually (`inspect_web_ui`), and always stop the server (`stop_dev_server`) before finishing.
Once all requirements are implemented and verified, provide a clean closing summary without calling tools.
"""

    def __init__(self, workspace_root: Union[str, Path] = ".", openai_api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.workspace = Path(workspace_root).resolve()
        self.client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY")) if OpenAI else None
        self.model = model
        self.toolbox = CoreToolbox(self.workspace, self.client)
        self.healer = SelfHealingEngine(self.workspace, self.client, self.model)
        self.compressor = ContextCompressor(self.client)

        # نگاشت کامل ابزارهای قابل فراخوانی توسط مدل
        self.tools_registry = {
            "read_file": self.toolbox.read_file,
            "write_file": self.toolbox.write_file,
            "patch_file": self.toolbox.patch_file,
            "list_dir_tree": self.toolbox.list_dir_tree,
            "grep_search": self.toolbox.grep_search,
            "get_code_outline": self.toolbox.get_code_outline,
            "init_task_plan": self.toolbox.init_task_plan,
            "update_task_status": self.toolbox.update_task_status,
            "run_unit_tests": self.toolbox.run_unit_tests,
            "test_api_endpoint": self.toolbox.test_api_endpoint,
            "git_checkpoint": self.toolbox.git_checkpoint,
            "git_rollback": self.toolbox.git_rollback,
            "start_dev_server": self.toolbox.start_dev_server,
            "stop_dev_server": self.toolbox.stop_dev_server,
            "inspect_web_ui": self.toolbox.inspect_web_ui,
            "self_heal_script": self.healer.run_and_heal,
        }

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """تولید اسکیمای رسمی ابزارها برای OpenAI Function Calling."""
        return [
            {"type": "function", "function": {"name": "read_file", "description": "خواندن بخشی از خطوط یک فایل", "parameters": get_model_schema(ReadFileInput)}},
            {"type": "function", "function": {"name": "write_file", "description": "نوشتن یا بازنویسی فایل", "parameters": get_model_schema(WriteFileInput)}},
            {"type": "function", "function": {"name": "patch_file", "description": "پچ جراحی یک بلاک کد یکتا در فایل", "parameters": get_model_schema(PatchFileInput)}},
            {"type": "function", "function": {"name": "list_dir_tree", "description": "مشاهده ساختار درختی پروژه", "parameters": {"type": "object", "properties": {"max_depth": {"type": "integer", "default": 3}}}}},
            {"type": "function", "function": {"name": "grep_search", "description": "جستجوی عبارت یا رجکس در فایلها", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "file_pattern": {"type": "string", "default": "*.*"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "get_code_outline", "description": "استخراج اسکلت توابع و کلاسهای فایل بدون خواندن بدنه", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
            {"type": "function", "function": {"name": "init_task_plan", "description": "مقداردهی چکلیست مراحل پروژه", "parameters": {"type": "object", "properties": {"task_list": {"type": "array", "items": {"type": "object"}}}, "required": ["task_list"]}}},
            {"type": "function", "function": {"name": "update_task_status", "description": "تغییر وضعیت تسک (completed/in_progress)", "parameters": {"type": "object", "properties": {"task_id": {"type": "integer"}, "status": {"type": "string"}}, "required": ["task_id", "status"]}}},
            {"type": "function", "function": {"name": "run_unit_tests", "description": "اجرای مجموعه تستها با pytest", "parameters": {"type": "object", "properties": {"test_target": {"type": "string", "default": "tests/"}}}}},
            {"type": "function", "function": {"name": "test_api_endpoint", "description": "ارسال درخواست آزمایشی به یک اندپوئینت HTTP", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "method": {"type": "string", "default": "GET"}}, "required": ["url"]}}},
            {"type": "function", "function": {"name": "git_checkpoint", "description": "ثبت کامیت امنیتی از وضعیت پروژه", "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}},
            {"type": "function", "function": {"name": "git_rollback", "description": "بازگردانی به آخرین چکپوینت سالم", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "start_dev_server", "description": "اجرای سرور در پسزمینه تا باز شدن پورت", "parameters": get_model_schema(StartServerInput)}},
            {"type": "function", "function": {"name": "stop_dev_server", "description": "توقف سرور و آزادسازی پورت", "parameters": {"type": "object", "properties": {"server_id": {"type": "string"}}, "required": ["server_id"]}}},
            {"type": "function", "function": {"name": "inspect_web_ui", "description": "رندر فرانتاند با Playwright، تست بصری و استخراج ارورهای کنسول", "parameters": get_model_schema(InspectUIInput)}},
            {"type": "function", "function": {"name": "self_heal_script", "description": "اجرای اسکریپت پایتون و ترمیم خودکار در صورت کرش", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "max_attempts": {"type": "integer", "default": 3}}, "required": ["file_path"]}}},
        ]

    def run(self, user_mission: str, max_turns: int = 25) -> str:
        """اجرای حلقه خودمختار ReAct تا تکمیل نهایی تسک."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_mission},
        ]
        schemas = self.get_tool_schemas()

        print(f"\n🚀 [Agent Started] مأموریت: {user_mission}\n{'='*60}")

        for turn in range(1, max_turns + 1):
            # اعمال فشردهسازی حافظه در صورت عبور از سقف توکن
            messages = self.compressor.compress(messages)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=schemas,
                tool_choice="auto",
                temperature=0.1
            )
            msg = response.choices[0].message
            messages.append(msg)

            if msg.content:
                print(f"\n🧠 [Thought - دور {turn}]:\n{msg.content}")

            # اگر ابزاری فراخوانی نشده باشد، مأموریت تکمیل شده است
            if not msg.tool_calls:
                print(f"\n🏁 [Mission Completed] مأموریت با موفقیت به پایان رسید.")
                return msg.content or ""

            for call in msg.tool_calls:
                fn_name = call.function.name
                args = json.loads(call.function.arguments)
                print(f"⚡ [Action]: {fn_name}({json.dumps(args, ensure_ascii=False)[:100]}...)")

                handler = self.tools_registry.get(fn_name)
                res = handler(**args) if handler else {"success": False, "error": f"ابزار {fn_name} ناشناخته است."}
                
                res_str = json.dumps(res, ensure_ascii=False)
                print(f"👁️ [Observation]: {res_str[:120]}...")

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": res_str
                })

        return "حداکثر سقف دورهای مجاز برای مأموریت به پایان رسید."


# =====================================================================
# بخش ۷: نحوه استفاده و تست مستقیم
# =====================================================================

if __name__ == "__main__":
    # تست سریع اجرای مهارت روی محیط لوکال
    agent = AgentSkill(workspace_root=".")
    mission = (
        "یک اسکریپت پایتون به نام `calc.py` ایجاد کن که کلاسی به نام `Calculator` با قابلیت جمع و ضرب داشته باشد. "
        "سپس یک فایل تست به نام `test_calc.py` برای آن بساز، با ابزار `run_unit_tests` آن را اجرا و اعتبارسنجی کن، "
        "یک چکپوینت گیت ثبت کن و پایان کار را اعلام نما."
    )
    final_report = agent.run(mission)
    print("\nگزارش پایانی:\n", final_report)
