---
title: select-ask-ai：做一款「选中即问」的工具，最大的坑不在 AI
published: 2026-09-01
description: 浏览器脚本 + Python 桌面客户端覆盖 PDF / Word / WPS 场景，难点全在取词和打包上。
tags: [Python, Tampermonkey, 工具, 桌面端]
category: 工具
draft: false
---

想法很简单：在任何地方选中一段文字，一键丢给大模型。真正做下去才发现，**AI 调用只占工作量的两成**，剩下八成全在"怎么拿到选中的文字"和"怎么让它在不同软件里都能用"。

## 两条路：浏览器 vs 桌面

浏览器场景最好办，一个 Tampermonkey 脚本就够：

```javascript
document.addEventListener("mouseup", () => {
  const selected = window.getSelection().toString().trim();
  if (selected) showAskButton(selected);
});
```

但出了浏览器就不行了——PDF 阅读器、Word、WPS、Markdown 编辑器，每个都有自己的取词方式，没有统一 API。

桌面端走的是另一条路：监听全局热键，用剪贴板做中介：

```python
import pyperclip
from pynput import keyboard

def on_activate():
    backup = pyperclip.paste()      # 先备份用户剪贴板
    trigger_copy()                  # 模拟复制，把选中内容取到剪贴板
    text = pyperclip.paste()
    pyperclip.copy(backup)          # 用完还回去
    ask(text)
```

用剪贴板做中转是有代价的：会覆盖用户原本复制的内容。所以必须先备份再还原——这种细节不处理，工具就会被默默卸载。

## 打包才是真麻烦

桌面端用 tkinter 做浮窗界面，PyInstaller 打包分发。踩到的坑：

- **体积**：直接打包会把整个环境打进去，产物几百 MB。后来用干净虚拟环境 + `--onefile` + 排除无关依赖才压下来；
- **pynput 的全局监听**打包后偶尔失效，需要在 spec 文件里显式声明隐藏导入；
- **跨平台差异**：Windows 和 macOS 的热键注册、剪贴板行为都不一致，目前 Windows 版本最完整。

## 回头看

这个项目技术难度不高，但很锻炼一件事：**把工具做到别人真的愿意用**。

延迟够不够低、要不要装额外依赖、会不会打断原有工作流——这些比模型能力强弱更能决定一个工具会不会被留下来。
