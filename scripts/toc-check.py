#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TOC（左侧目录）回归验证。

自己起静态服务、自己起 headless Chrome、自己收尾，一条命令跑完：
    python scripts/toc-check.py              # 测 dist 构建产物
    python scripts/toc-check.py --build      # 先 npm run build 再测
    python scripts/toc-check.py --url https://henzhi.github.io/blog   # 测线上

覆盖：rail/drawer 两种形态、多级缩进、点击平滑滚动、滚动高亮跟随、触底、
折叠展开 + localStorage 记忆、swup 换页后重建、目录超长内部滚动、亮/暗主题、
非文章页不渲染、横向溢出。退出码 0=全通过，1=有失败项。

改 CSS / 断点 / 滚动逻辑之后跑一遍，比肉眼刷页面可靠得多。
"""

# 依赖：websocket-client（pip install websocket-client）
import argparse
import base64
import functools
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

try:
    import websocket
except ImportError:
    sys.exit("缺依赖：pip install websocket-client")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = os.getcwd()

DIST = os.path.join(ROOT, "dist")
FAILS = []
SHOTS = None

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def check(name, ok, detail=""):
    if not ok:
        FAILS.append(name)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    found = shutil.which("chrome") or shutil.which("google-chrome")
    if found:
        return found
    sys.exit("找不到 Chrome，用 --chrome 指定路径")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class BaseRewritingHandler(http.server.SimpleHTTPRequestHandler):
    """把 /<base>/xxx 映射到 <dist>/xxx，这样才能测子路径部署的产物。"""

    base = "/blog"

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if self.base and clean.startswith(self.base + "/"):
            clean = clean[len(self.base):]
        elif self.base and clean.rstrip("/") == self.base:
            clean = "/"
        return super().translate_path(clean)

    def log_message(self, *args):
        pass


def start_server(directory, base):
    handler = functools.partial(BaseRewritingHandler, directory=directory)
    BaseRewritingHandler.base = base
    port = free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}{base}", server


def start_chrome(binary, port, width, height):
    profile = tempfile.mkdtemp(prefix="toccheck-")
    proc = subprocess.Popen(
        [
            binary, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
            "--remote-allow-origins=*",  # 不加这行 WebSocket 握手 403
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "--hide-scrollbars",
            f"--window-size={width},{height}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
            return proc, profile
        except Exception:
            time.sleep(0.25)
    proc.kill()
    sys.exit("Chrome DevTools 端点没起来")


class Page:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.n = 0

    def send(self, method, params=None):
        self.n += 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expr, await_promise=True):
        r = self.send("Runtime.evaluate", {
            "expression": expr, "awaitPromise": await_promise,
            "returnByValue": True, "userGesture": True,
        })
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:400])
        return r.get("result", {}).get("value")

    def viewport(self, w, h, mobile=False):
        self.send("Emulation.setDeviceMetricsOverride", {
            "width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile,
            "screenWidth": w, "screenHeight": h,
        })

    def goto(self, url, settle=1.4):
        self.send("Page.navigate", {"url": url})
        for _ in range(120):
            time.sleep(0.1)
            if self.js("document.readyState", await_promise=False) == "complete":
                break
        time.sleep(settle)

    def shot(self, name):
        data = self.send("Page.captureScreenshot", {"format": "png"})["data"]
        path = os.path.join(SHOTS, name)
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(data))
        print(f"       截图 -> {path}")


def page_ws(port):
    for _ in range(60):
        try:
            items = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list").read())
            pages = [t for t in items if t.get("type") == "page"]
            if pages:
                return pages[0]["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.25)
    sys.exit("拿不到 page target")


ERROR_HOOK = """
window.__errs = [];
window.addEventListener('error', e => window.__errs.push('error: ' + (e.message || e.type)));
window.addEventListener('unhandledrejection', e => window.__errs.push('reject: ' + e.reason));
"""

PROBE = """
(() => {
  const q = (s) => document.querySelector(s);
  const root = q('.toc-root'), panel = q('.toc-panel'), tab = q('.toc-tab'), fab = q('.toc-fab');
  const items = [...document.querySelectorAll('.toc-item')];
  const art = document.getElementById('post-container');
  const cs = (el) => el ? getComputedStyle(el) : null;
  const box = (el) => { if (!el) return null; const r = el.getBoundingClientRect();
    return {x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)}; };
  const crumb = q('.toc-item[aria-current="location"]');
  return {
    mode: root ? root.dataset.mode : null,
    open: root ? root.dataset.open : null,
    ready: root ? root.hasAttribute('data-ready') : false,
    scrollable: root ? root.dataset.scrollable : null,
    hasToc: !!root,
    count: items.length,
    levels: [...new Set(items.map(a => a.dataset.level))].sort(),
    texts: items.map(a => a.querySelector('.toc-text').textContent),
    panelBox: box(panel), panelPos: cs(panel) ? cs(panel).position : null,
    panelVis: cs(panel) ? cs(panel).visibility : null,
    panelInert: panel ? panel.hasAttribute('inert') : null,
    tabBox: box(tab), tabVis: cs(tab) ? cs(tab).visibility : null,
    fabBox: box(fab), fabVis: cs(fab) ? cs(fab).visibility : null,
    articleBox: box(art),
    active: crumb ? crumb.dataset.slug : null,
    overflowX: document.documentElement.scrollWidth > window.innerWidth + 1,
    errors: window.__errs ? window.__errs.slice() : [],
  };
})()
"""

CLICK_ITEM = """
(idx) => {
  const a = document.querySelectorAll('.toc-item')[idx];
  a.scrollIntoView({block: 'nearest'});
  a.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
  return a.dataset.slug;
}
"""

CLICK_SEL = """
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;
  el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
  return true;
}
"""

AFTER_CLICK = """
(slug) => {
  const h = document.getElementById(slug);
  const a = document.querySelector('.toc-item[aria-current="location"]');
  return {headingTop: h ? Math.round(h.getBoundingClientRect().top) : null,
          active: a ? a.dataset.slug : null,
          scrollY: Math.round(window.scrollY),
          hash: decodeURIComponent(location.hash)};
}
"""

NAVBAR_OFFSET = 88  # 吸顶导航 4.5rem + 呼吸；跳转后标题应落在这里


def suite(page, base, deep, shallow):
    # ---------------- A. rail ----------------
    print("\n=== A. 桌面 1680x1000（rail 固定竖栏） ===")
    page.viewport(1680, 1000)
    page.goto(deep)
    p = page.js(PROBE)
    print("       ", json.dumps({k: v for k, v in p.items() if k != "texts"}, ensure_ascii=False))
    check("A1 进入 rail 模式", p["mode"] == "rail", f"mode={p['mode']}")
    check("A2 默认展开", p["open"] == "true")
    check("A3 面板挂在栅格外（absolute）", p["panelPos"] == "absolute")
    check("A4 面板不压正文", p["articleBox"]["x"] - p["panelBox"]["x"] - p["panelBox"]["w"] >= 16,
          f"gap={p['articleBox']['x'] - p['panelBox']['x'] - p['panelBox']['w']}px")
    check("A5 面板没被挤出视口左侧", p["panelBox"]["x"] >= 0, f"x={p['panelBox']['x']}")
    check("A6 多级目录（含 level 1）", p["levels"] == ["0", "1"], f"levels={p['levels']}")
    check("A7 文本已削掉 autolink 的 #", not any(t.endswith("#") for t in p["texts"]))
    check("A8 无 JS 报错", p["errors"] == [], str(p["errors"]))
    page.shot("01-rail-open.png")

    # ---------------- B. 点击跳转 ----------------
    print("\n=== B. 点击目录项 ===")
    slug = page.js(f"({CLICK_ITEM})(6)")
    time.sleep(1.2)
    after = page.js(f"({AFTER_CLICK})({json.dumps(slug)})")
    check("B1 顶部对齐到导航栏下方", abs(after["headingTop"] - NAVBAR_OFFSET) <= 6,
          f"headingTop={after['headingTop']} 期望≈{NAVBAR_OFFSET}")
    check("B2 目标项高亮", after["active"] == slug)
    check("B3 URL hash 同步", after["hash"] == f"#{slug}", after["hash"])
    page.shot("02-rail-jumped.png")

    # ---------------- C. 滚动高亮 ----------------
    print("\n=== C. 滚动高亮跟随 ===")
    marks = []
    for y in (0, 900, 2200, 4000, 99999):
        page.js(f"window.scrollTo({{top: {y}, behavior: 'instant'}}); 1")
        time.sleep(0.35)
        marks.append(page.js(
            "(() => { const a=document.querySelector('.toc-item[aria-current=\"location\"]');"
            "return {y: Math.round(window.scrollY), slug: a ? a.dataset.slug : null}; })()"))
    print("       ", json.dumps(marks, ensure_ascii=False))
    check("C1 页面顶部不高亮任何章节", marks[0]["slug"] is None, str(marks[0]))
    check("C2 滚动过程命中多个章节", len({m["slug"] for m in marks[1:4]}) >= 3,
          str([m["slug"] for m in marks[1:4]]))
    last = page.js("(() => { const a=document.querySelectorAll('.toc-item');"
                   "return a[a.length-1].dataset.slug; })()")
    check("C3 触底高亮最后一节", marks[-1]["slug"] == last, f"{marks[-1]['slug']} vs {last}")
    page.js("window.scrollTo({top: 0, behavior: 'instant'}); 1")
    time.sleep(0.3)

    # ---------------- D. 折叠 / 展开 ----------------
    print("\n=== D. 折叠与展开 ===")
    page.js(f"({CLICK_SEL})('.toc-icon-btn')")
    time.sleep(0.5)
    c = page.js(PROBE)
    check("D1 点击后收起", c["open"] == "false")
    check("D2 面板隐藏且移出可达树", c["panelVis"] == "hidden" and c["panelInert"] is True)
    check("D3 竖排「目录」标签出现", c["tabVis"] == "visible" and c["tabBox"]["w"] > 0, str(c["tabBox"]))
    check("D4 状态写入 localStorage", page.js("localStorage.getItem('toc-collapsed')") == "1")
    page.shot("03-rail-collapsed.png")
    page.js(f"({CLICK_SEL})('.toc-tab')")
    time.sleep(0.5)
    check("D5 点标签可重新展开", page.js(PROBE)["open"] == "true")

    # ---------------- E. swup 换页 ----------------
    print("\n=== E. swup 无刷新换页 ===")
    page.js(f"({CLICK_SEL})('.toc-icon-btn')")  # 收起，验证状态能跨页保持
    time.sleep(0.4)
    page.js("window.scrollTo({top:0,behavior:'instant'}); 1")
    href = page.js("""(() => {
      const a = document.querySelector('#post-container nav a[href]');
      if (!a) return null;
      a.scrollIntoView({block: 'center'});
      a.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
      return a.getAttribute('href');
    })()""")
    print(f"       点击站内链接 -> {href}")
    time.sleep(2.2)
    f = page.js(PROBE)
    check("E1 已无刷新换页", f["hasToc"] and f["count"] != p["count"], f"{p['count']} -> {f['count']}")
    check("E2 换页后目录重建并就绪", f["ready"] is True and f["count"] > 0)
    check("E3 收起状态跨页保持", f["open"] == "false")
    check("E4 换页后无 JS 报错", f["errors"] == [], str(f["errors"]))

    # ---------------- F/G/H. drawer ----------------
    print("\n=== F. 移动端 390x844（左侧抽屉） ===")
    page.viewport(390, 844, mobile=True)
    page.goto(deep)
    m = page.js(PROBE)
    check("F1 进入 drawer 模式", m["mode"] == "drawer", f"mode={m['mode']}")
    check("F2 默认收起", m["open"] == "false")
    check("F3 面板 fixed 且移到视口左外侧", m["panelPos"] == "fixed" and m["panelBox"]["x"] < 0,
          f"x={m['panelBox']['x']}")
    check("F4 悬浮按钮可见", m["fabVis"] == "visible", f"vis={m['fabVis']}")
    check("F5 悬浮按钮在视口内", 0 < m["fabBox"]["x"]
          and m["fabBox"]["x"] + m["fabBox"]["w"] <= 390, str(m["fabBox"]))
    check("F6 无横向溢出", not m["overflowX"], f"scrollWidth={page.js('document.documentElement.scrollWidth')}")
    page.shot("04-mobile-closed.png")

    print("\n=== G. 抽屉交互 ===")
    page.js(f"({CLICK_SEL})('.toc-fab')")
    time.sleep(0.6)
    g = page.js(PROBE)
    check("G1 抽屉打开且左边缘贴齐 0", g["open"] == "true" and g["panelBox"]["x"] == 0,
          f"x={g['panelBox']['x']}")
    check("G2 面板不再 inert", g["panelInert"] is False)
    check("G3 打开时入口按钮让位", g["fabVis"] == "hidden")
    page.shot("05-mobile-open.png")
    slug2 = page.js(f"({CLICK_ITEM})(3)")
    time.sleep(1.3)
    h = page.js(f"({AFTER_CLICK})({json.dumps(slug2)})")
    check("H1 点击后抽屉自动收起", page.js(PROBE)["open"] == "false")
    check("H2 页面滚到目标章节", abs(h["headingTop"] - NAVBAR_OFFSET) <= 6, f"headingTop={h['headingTop']}")
    check("H3 目标项高亮", h["active"] == slug2)
    page.shot("06-mobile-after-jump.png")

    # ---------------- I. 模式热切换 ----------------
    print("\n=== I. 断点热切换 ===")
    page.viewport(1680, 1000)
    time.sleep(0.4)
    page.js("window.dispatchEvent(new Event('resize')); 1")
    time.sleep(0.6)
    i = page.js(PROBE)
    check("I1 切回 rail（沿用已保存的收起偏好）", i["mode"] == "rail" and i["open"] == "false",
          f"mode={i['mode']} open={i['open']}")
    check("I2 抽屉专属按钮已隐藏", i["fabVis"] == "hidden")
    page.js("localStorage.removeItem('toc-collapsed'); 1")
    page.goto(deep)
    i2 = page.js(PROBE)
    check("I3 无偏好时 rail 默认展开", i2["mode"] == "rail" and i2["open"] == "true",
          f"open={i2['open']}")
    page.viewport(1024, 800)
    time.sleep(0.4)
    page.js("window.dispatchEvent(new Event('resize')); 1")
    time.sleep(0.6)
    i3 = page.js(PROBE)
    check("I4 1024px 退回 drawer 且收起", i3["mode"] == "drawer" and i3["open"] == "false",
          f"mode={i3['mode']} open={i3['open']}")

    # ---------------- J. 目录超长 ----------------
    print("\n=== J. 矮视口下目录内部滚动 ===")
    page.viewport(1680, 560)
    page.goto(deep)
    j = page.js(PROBE)
    check("J1 判定为可滚动", j["scrollable"] == "true")
    mask = page.js("getComputedStyle(document.querySelector('.toc-scroll')).maskImage")
    check("J2 渐隐遮罩已应用", "gradient" in (mask or ""), (mask or "")[:50])
    page.js("window.scrollTo({top: document.documentElement.scrollHeight, behavior:'instant'}); 1")
    time.sleep(0.9)
    vis = page.js("""(() => {
      const b = document.querySelector('.toc-scroll');
      const a = document.querySelector('.toc-item[aria-current="location"]');
      if (!a) return {ok: false};
      const br = b.getBoundingClientRect(), ar = a.getBoundingClientRect();
      return {ok: true, inView: ar.top >= br.top - 1 && ar.bottom <= br.bottom + 1,
              scrollTop: Math.round(b.scrollTop)};
    })()""")
    check("J3 高亮项自动滚进目录可视区", vis.get("inView") is True, str(vis))
    page.shot("07-rail-scrollable.png")

    # ---------------- K. 亮色 ----------------
    print("\n=== K. 亮色主题 ===")
    page.viewport(1680, 1000)
    page.goto(deep)
    page.js("localStorage.setItem('theme','light'); 1")
    page.goto(deep)
    check("K1 已切到亮色", page.js("document.documentElement.classList.contains('dark')") is False)
    page.js("window.scrollTo({top: 3000, behavior:'instant'}); 1")
    time.sleep(0.6)
    active_color = page.js("(() => { const a=document.querySelector('.toc-item[aria-current=\"location\"]');"
                           "return a ? getComputedStyle(a).color : null; })()")
    plain_color = page.js("getComputedStyle(document.querySelectorAll('.toc-item')[2]).color")
    check("K2 亮色下高亮项用主色（区别于普通项）",
          active_color is not None and active_color != plain_color, f"{active_color} vs {plain_color}")
    page.shot("08-rail-light.png")
    page.js("localStorage.setItem('theme','auto'); 1")

    # ---------------- L. 非文章页 ----------------
    print("\n=== L. 非文章页不渲染目录 ===")
    for name, path in (("首页", "/"), ("归档", "/archive/"), ("分类", "/categories/"), ("关于", "/about/")):
        page.goto(f"{base}{path}")
        l = page.js("""(() => {
          const toc = document.getElementById('toc');
          return {
            hasToc: !!document.querySelector('.toc-root'),
            container: !!toc,
            // #toc 里会残留 Astro 提升的 <script type="module">，别用 innerHTML==='' 判空
            empty: toc ? ![...toc.children].some(el => el.tagName.toLowerCase() !== 'script') : false,
            overflowX: document.documentElement.scrollWidth > window.innerWidth + 1,
            errs: window.__errs ? window.__errs.slice() : [],
          };
        })()""")
        check(f"L {name}", (not l["hasToc"]) and l["container"] and l["empty"]
              and (not l["overflowX"]) and l["errs"] == [], json.dumps(l, ensure_ascii=False))

    # ---------------- M. 首页 -> 文章（最常见的真实路径） ----------------
    print("\n=== M. 首页点文章卡进详情页（Swup） ===")
    page.goto(f"{base}/")
    page.js("""(() => {
      const a = [...document.querySelectorAll('main a[href*="/posts/"]')][0];
      a.scrollIntoView({block: 'center'});
      a.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
      return a.getAttribute('href');
    })()""")
    time.sleep(2.2)
    m2 = page.js(PROBE)
    check("M1 已进入文章页", "/posts/" in (page.js("location.pathname") or ""),
          page.js("location.pathname"))
    # 关键：customElements.define 只在首次加载执行一次，换页后靠元素升级重建目录
    check("M2 换页后目录出现且已就绪", m2["ready"] is True and m2["count"] > 0, f"count={m2['count']}")
    check("M3 换页后无 JS 报错", m2["errors"] == [], str(m2["errors"]))
    page.js("window.scrollTo({top: 1500, behavior:'instant'}); 1")
    time.sleep(0.5)
    check("M4 新目录立刻响应滚动高亮", page.js(
        "(() => { const a=document.querySelector('.toc-item[aria-current=\"location\"]');"
        "return a ? a.dataset.slug : null; })()") is not None)
    page.shot("09-home-to-post.png")


def main():
    global SHOTS
    ap = argparse.ArgumentParser(description="TOC（左侧目录）回归验证")
    ap.add_argument("--url", help="直接测线上站点（默认测 dist 构建产物）")
    ap.add_argument("--base", default="/blog", help="子路径前缀，默认 /blog")
    ap.add_argument("--dist", default=DIST, help="构建产物目录，默认 <repo>/dist")
    ap.add_argument("--build", action="store_true", help="先跑 npm run build")
    ap.add_argument("--chrome", help="Chrome 可执行文件路径")
    ap.add_argument("--out-dir", default="toc-shots", help="截图输出目录")
    ap.add_argument("--deep", help="多级标题的样例文章路径")
    ap.add_argument("--shallow", help="只有一级标题的样例文章路径")
    args = ap.parse_args()

    if args.build:
        print("npm run build ...")
        subprocess.run("npm run build", cwd=ROOT, shell=True, check=True,
                       stdout=subprocess.DEVNULL)

    SHOTS = os.path.abspath(args.out_dir)
    os.makedirs(SHOTS, exist_ok=True)

    server = None
    if args.url:
        base = args.url.rstrip("/")
    else:
        if not os.path.isdir(args.dist):
            sys.exit(f"找不到构建产物 {args.dist}，先跑 npm run build 或加 --build")
        base, server = start_server(args.dist, args.base)
        print(f"静态服务: {base}  <-  {args.dist}")

    deep = (base + (args.deep or "/posts/lexagent/01-architecture-overview/"))
    shallow = (base + (args.shallow or "/posts/build-this-site/"))

    port = free_port()
    chrome_proc, profile = start_chrome(args.chrome or find_chrome(), port, 1680, 1000)
    try:
        page = Page(page_ws(port))
        page.send("Page.enable")
        page.send("Runtime.enable")
        page.send("Page.addScriptToEvaluateOnNewDocument", {"source": ERROR_HOOK})
        suite(page, base, deep, shallow)
    finally:
        chrome_proc.kill()
        if server:
            server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)

    print("\n================ 结果 ================")
    if FAILS:
        print(f"{len(FAILS)} 项未通过：")
        for name in FAILS:
            print(f"  - {name}")
        sys.exit(1)
    print("全部通过")
    print(f"截图目录：{SHOTS}")


if __name__ == "__main__":
    main()
