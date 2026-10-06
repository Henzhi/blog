# Henzhi 的博客

线上在 https://henzhi.github.io/blog/，源码在 [github.com/Henzhi/blog](https://github.com/Henzhi/blog)。

定位是**个人记录型博客**，不承担求职展示功能：写日常生活、整理学习笔记、分享教程笔记。全站内容按这三个分类组织（见 `src/data/categories.ts`），首页与关于页的文案都围绕这个定位，不放简历入口、不放面向招聘方的项目清单。

底子是 Astro + [Fuwari](https://github.com/saicaca/fuwari) 主题，纯静态输出；样式用 Tailwind，搜索框和主题切换那几个小组件是 Svelte 写的，搜索索引靠 Pagefind 在构建时生成，不需要后端。托管在 GitHub Pages 上，push 到 `main` 就自动构建发布，不用自己碰服务器。

## 设计体系

2026-10 做过一轮全面重做，方向是「长文阅读 + 密排列表」，参考 leerob.io 的列表密度和 joshwcomeau.com 的正文排版。核心是**去卡片化**：正文和列表不再各自装进圆角卡片，改用细分隔线 + 留白划分层次。

- **字体**：`Inter Variable`（拉丁）+ `PingFang SC` / `Microsoft YaHei` / `Noto Sans SC`（中文）系统栈。**没引 Noto Sans SC 的 webfont**——中文全量包约 1.5MB/字重，不值当，系统字体已经够好。
- **正文**：18px / 1.75 行高，正文栏 `max-w-[42rem]`（672px，约 45 个中文字符一行）。
- **色板**：主色锁定 hue 250（`oklch(0.55 0.14 250)`），`themeColor.fixed: true`。强调色只出现在链接和当前态两处，不再满屏点缀。
- **圆角**：`--radius-lg` 从 1rem 收到 0.75rem，阴影基本去掉。
- **布局**：xl（1280px）起是**左右等宽的三栏** `[12.5rem 正文 12.5rem]`，lg 是两栏（主栏 + 右侧窄栏）。
  正文永远落在**视口正中**——左右两栏等宽是数学前提，只要一侧宽了就偏。
- **`--page-width` = 75rem（1200px）**，不是随手定的：
  `px-4(16×2) + 12.5rem + gap 3rem + 42rem + gap 3rem + 12.5rem = 1200px`，
  这样中间列正好 672px，正文顶满 42rem 上限。**改栅格或栏间距必须同步重算这个值**，
  否则行长上限形同虚设（`constants.ts` 里有推导）。
- **目录（TOC）**：左侧竖栏，是对齐到栅格第一列的固定浮层，宽 12.5rem。
  `≥ 1280px`（= tailwind `xl`，也是三栏开始的地方）显示竖栏，可收起成一枚竖排「目录」标签，
  状态存 `localStorage.toc-collapsed`；更窄退化成右下角悬浮按钮 + 左侧滑出抽屉。
  - 目录**不是栅格里的元素**，而是浮层。所以开合不改变栅格宽度，正文**零位移**——
    这是「收起时正文仍居中」的实现方式，不是靠动画遮掩。
  - 收起后标签的右边缘与展开时面板的右边缘严格对齐，开合之间不跳位。
  - 定位/样式全在 `src/components/widget/TOC.astro` 内，断点只由 JS 的 `matchMedia` 决定
    （`data-mode`），CSS 不重复写一遍——避免两处断点写歪。**这个断点必须用 px 且与 tailwind 的
    `xl` 一致**（改成 em 会因为默认字号偏差导致栅格与竖栏错位）。
  - 1024–1280px 区间没有左栏可放竖栏，所以走抽屉；正文在该区间是「在阅读区内居中」，
    严格居中只在 xl 以上成立。

设计令牌（字号阶梯、字体栈、圆角、间距）都集中在 `src/styles/variables.styl`。

### 目录的回归验证

目录这块的行为（断点、折叠、滚动高亮、swup 换页后重建）肉眼刷页面很难覆盖全，
改完跑一遍脚本：

```bash
npm run build && python scripts/toc-check.py        # 测构建产物
python scripts/toc-check.py --url https://henzhi.github.io/blog   # 测线上
```

脚本自己起静态服务（把 `/blog/` 映射到 `dist/`）、自己起 headless Chrome、自己收尾，
**不用手动 `&` 起后台进程**（沙箱会在命令结束时回收后台进程，手动起的服务经常是假故障）。
45 项断言覆盖 rail/drawer 两种形态、多级缩进、点击跳转、滚动高亮跟随、触底、
折叠展开 + `localStorage` 记忆、swup 换页重建、目录超长内部滚动、亮暗主题、非文章页。
截图落在 `toc-shots/`（已 gitignore），退出码 0 = 全通过。

依赖 `websocket-client`；Chrome 路径能自动找，找不到用 `--chrome` 指定。

## 平时怎么用

```bash
npm install
npm run dev        # 本地预览 http://localhost:4321/blog/
```

写文章就是在 `src/content/posts/` 里新建一个 `.md`，也可以让脚本生成骨架。slug 会成为文件名和 URL（用英文小写加连字符），中文标题走第二个参数：

```bash
npm run new-post -- lexagent-budget-breaker "LexAgent 的预算熔断是怎么做的"
```

头部固定这几个字段：

```markdown
---
title: 文章标题
published: 2026-09-11
description: 一句话摘要，列表页和搜索结果里会显示
tags: [LangGraph, RAG]
category: 教程笔记
draft: false
featured: false
---

正文。
```

`title` 和 `published` 是必须的，其余可省。schema（`src/content/config.ts`）里另外还有 `image`（封面图）和 `lang` 两个可选字段，目前没用上，需要时自己加。`draft: true` 的文章不进构建，写一半先放着挺方便。

**注意 slug 就是 URL**，所以文件名用英文小写加连字符（`lexagent-budget-breaker`），中文标题写在 `title` 里。文件名用中文的话链接会变成一长串 URL 编码。`featured: true` 是给首页精选预留的标记，**目前首页还没接这个字段的读取逻辑**（首页现在直接取最新几篇），想用的话在 `src/pages/[...page].astro` 里按它筛。

**`category` 只允许三个值**：`生活记录` / `学习笔记` / `教程笔记`，留空则算「未分类」。取值来源是 `src/data/categories.ts`，`src/content/config.ts` 里挂了 `refine` 校验——写别的词构建会直接报错，不会悄悄多出一个游离分类。要加分类就改那个文件，`/categories/` 索引页和侧栏都会跟着变。

正文除了标准 Markdown，还支持这些：

- `> [!NOTE]` 一类的小提示框（还有 TIP / WARNING / IMPORTANT）
- `::github{repo="owner/repo"}` 嵌一张仓库卡片
- KaTeX 数学公式
- 代码块自动带高亮、行号、复制按钮

**正文里的站内链接要写相对路径**（`[分类](../categories/)`），不能写 `/categories/`。站点在 GitHub Pages 的 `/blog/` 子路径下，裸 `/` 开头会解析到站点根目录直接 404。这条对 `.md` 内容同样适用。

其余常改的地方：

| 想改什么 | 去哪儿 |
|---|---|
| 站点标题、副标题、导航、社交链接、主题色 | `src/config.ts` |
| 分类定义（三个方向的名称与说明） | `src/data/categories.ts` |
| 首页简介文案（Default / Long 两版） | `src/components/Hero.astro` |
| 分类索引页 | `src/pages/categories.astro` |
| 关于页 | `src/content/spec/about.md` |
| 设计令牌（字体、字号、圆角、色板） | `src/styles/variables.styl` |
| 样式入口（引入顺序） | `src/layouts/Layout.astro` |

头像走的是 GitHub 头像外链（`profileConfig.avatar`，`https://github.com/Henzhi.png?size=128`），改了 GitHub 资料头像这里会自动跟着变，`src/assets/images/` 下的图片已经删掉了。

## 发布

**正常流程就是 push**，没有别的动作：

```bash
git add -A && git commit -m "post: 新文章" && git push
```

`.github/workflows/deploy.yml` 会跑 `npm ci` → `npm run build`（含 Pagefind 索引）→ 传到 GitHub Pages。一两分钟看 https://henzhi.github.io/blog/ 就更新了。也可以在 Actions 页面手动点 `workflow_dispatch` 触发一次。

CI 里还跑一个 biome 检查（`format` + `lint`）。本地提交前顺手跑一下：

```bash
npm run lint      # biome check --write ./src
```

导入顺序写错会被 CI 拦下来。

### 首次部署要做的事

代码 push 上去还不够，Pages 得先在仓库里启用一次（这是 GitHub 的硬性要求，没有纯 API 的绕过路径）：

1. 仓库是**公开**的（Settings → 最下面 Danger Zone → Change visibility）。私有仓发布 Pages 需要 Pro。
2. **Settings → Pages → Build and deployment → Source 选 `GitHub Actions`**（不是 "Deploy from a branch"）。
3. 去 Actions 页手动跑一次 `Deploy to GitHub Pages`，或者在设置里点 Save 后会自动重跑。

**没做第 2 步会怎样**：workflow 会在 `Configure Pages` 步骤失败，报

```
HttpError: Not Found - https://docs.github.com/rest/pages/pages#get-a-pages-site
Get Pages site failed. Please verify that the repository has Pages enabled...
```

这个报错挺误导人的——它看起来像配置写错了，其实前面 `Install dependencies` 和 `Build site` 都是成功的，代码一点问题没有，就是 Pages 还没开。

### 本地预览

GitHub Pages 部署在 `/blog/` 子路径下，所以本地验证也必须带着这个前缀，否则测不出 CSS/JS 404 这类问题：

```bash
npm run build && bash scripts/serve-local.sh     # http://localhost:4321/blog/
```

### 站点地址配置

`astro.config.mjs` 里这两行是一对，改一个必须改另一个：

```js
site: "https://henzhi.github.io",
base: "/blog",       // 必须和仓库名一致
```

`base` 写错的表现是全站 CSS/JS 404、页面变成裸 HTML。换自定义域名时，把 `site` 换成域名、`base` 改成 `"/"` 即可。

### 两个只有部署时才暴露的坑

**RSS 的 `<channel><link>` 会漏掉 base**。`context.site` 只返回 origin（`https://henzhi.github.io/`），不含 base。`src/pages/rss.xml.ts` 里已经用 `new URL(import.meta.env.BASE_URL, context.site)` 补上了，改这块时留意别改回去。

**用 `file://` 直接打开 `dist/index.html` 看不出问题**。根路径 `/blog/_astro/...` 在 file 协议下会解析成 `C:\blog\...`，CSS 全丢，页面是裸的 HTML——这是假象不是 bug。要验证就得起个 HTTP 服务，且目录结构得是 `根/blog/dist内容`。

## 几个坑，别再踩一遍

**`src/styles/` 下的样式文件必须被 import，否则全是死文件。** 这是本项目最大的一个历史遗留坑，也是「改了样式线上没生效」的真正原因。Fuwari 重做那次（`893c721`）把 8 个样式文件复制了进来却没在 `Layout.astro` 里接 import——被替换掉的旧 `BaseLayout.astro` 原本是有一行 `import '../styles/global.css'` 的。后果是 `variables.styl` 里改的任何设计令牌**都不会进浏览器**，页面只拿到 Tailwind 扫 class 字面量生成的单属性规则，表现得像「Tailwind 配置改了没用」。现在 `Layout.astro` 顶部按依赖顺序统一 import，**顺序不能乱**：`variables.styl`（定义令牌）→ `main.css`（定义组件类）→ 其余细化样式。

顺带一提，网上流传的「构建报 `The link class does not exist` 就清 `node_modules/.vite`」是**错的诊断**。真实原因就是这个——样式文件没被 import，`@apply link` 自然找不到 `link` 类。清缓存只是碰巧让构建重跑。

**别在样式文件之间用 `@apply` 引用自定义类。** 这是上面那条坑的变体，而且更阴——它**随机复现**。Tailwind 的 `@apply` 只能解析「同一次处理里已经出现过」的自定义类，而 Astro 会把样式拆成多个 CSS chunk（`dist/_astro/` 下能看到两个 `Layout.*.css` 和两个 `_page_.*_.css`）。`main.css` 和 `markdown.css` 分到同一个 chunk 时构建通过，分到不同 chunk 时报：

```
[vite:css] [postcss] src/styles/markdown.css:86:9: The `btn-regular-dark` class does not exist.
```

`markdown.css` 的 `.copy-btn` 原本就是 `@apply btn-regular-dark ...`——那是全项目唯一一处跨文件自定义类依赖，构建大约三次挂一次。2026-10-05 已把它就地展开成等价的工具类（见该处注释），之后连续 6 次构建全部通过。**新增样式时如果要用 `@layer components` 里的自定义类，就地展开，或者改成普通 CSS 属性**；`@apply` 引用 Tailwind 自带工具类（含 `dark:` 变体和 `bg-[var(--x)]` 这种任意值）不受影响。

**改样式后别信肉眼，去 CDP 里量 `getComputedStyle`。** 两个真实翻车案例：

1. `text-[var(--text-hero)]` 实测 16px。Tailwind 无法从 `text-[var(--x)]` 判断类型——`text-` 既是 font-size 又是 color，它猜成了 **color**。必须写 `text-[length:var(--text-hero)]`。
2. `font-size: var(--text-body)` 不生效。`@tailwindcss/typography` 的 `.prose` 是同权重的单类选择器且在后面定义，压过了 `.custom-md`。改成 `.custom-md.prose` 双类选择器解决。

还有，`text-[length:var(--x)]/[1.1]` 这种连写语法压缩后会失效，`leading` 要分开写 `leading-[1.1]`。

**Windows 下 `npm run build` 可能被安全删除 shim 拦下来**（vite 清 `.vite/deps`、astro 清 `dist/` 时会触发 `SAFE_DELETE_BULK_CONFIRM_REQUIRED`）。临时绕法：

```bash
CODEBUDDY_SAFE_DELETE_ENABLED=0 npm run build
```

**别用无头浏览器截图判断页面是否正常**。Fuwari 的 `.onload-animation` 初始是 `opacity: 0`，靠 CSS 动画淡入。截图跑太早会拍到一片空白，看起来像渲染坏了。加 `--virtual-time-budget=6000` 等动画播完再截。另外截图命令**必须带 `--user-data-dir`**，否则 `--screenshot` 会静默不产出文件（无报错、exit 0）。

**为了过 CI 类型检查，动过两处主题源码**，以后升级 Fuwari 时注意别被覆盖掉：

- `ArchivePanel.svelte:22` —— `Post.category` 的类型放宽成 `string | null`（content collection 给的是这个）
- `LightDarkSwitch.svelte:17` —— 补了一句宽松的 props 声明，因为 Svelte 5 的 runes 组件不声明 props 时类型是 `Record<string, never>`，Astro 传下去的 `client:only` 会被判成非法属性

**根目录 `docs/` 下是 Fuwari 主题自带的多语言 README**（`README.ja.md` 之类），跟这个仓库无关，别去改。本项目自己的文档只有 `docs/UI重构方案.md`。

## 以后要是绑自定义域名

仓库 Settings → Pages → Custom domain 填域名，域名那边加 CNAME 指向 `henzhi.github.io`，然后把 `astro.config.mjs` 的 `site` 改成域名、`base` 改成 `"/"`。HTTPS 证书 GitHub 自动签，勾上 Enforce HTTPS 就行。

## 遗留

`scripts/local-server.ps1` + `scripts/serve-hidden.cmd` 是早期在 Windows 下起本地静态服务的方案（用 `CREATE_NO_WINDOW` 拉一个无黑窗的 python `http.server` 伺服 `dist/`），功能与 `scripts/serve-local.sh` 完全重叠。现在一律用 `serve-local.sh`。`serve-hidden.cmd` 里还硬编码了 `C:\Tools\miniconda3\pythonw.exe`，换机器就失效。

原先还有个 `scripts/publish.sh`，是部署到腾讯云轻量服务器（Caddy 容器跑 `--network host` + 只读挂载 `/srv/blog`）用的，服务器停用后已于 2026-10-05 删除。**部署现在只有 push 一条路径**，别再找别的入口；万一在别的地方见到这个脚本的引用，那是过期的。

## 许可

主题 MIT。文章内容默认 CC BY-NC-SA 4.0，不想要就在 `src/config.ts` 里把 `licenseConfig` 关掉。
