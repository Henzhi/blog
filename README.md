# Henzhi 的博客

线上在 https://henzhi.github.io/blog/，源码在 [github.com/Henzhi/blog](https://github.com/Henzhi/blog)。

底子是 Astro + [Fuwari](https://github.com/saicaca/fuwari) 主题，纯静态输出；样式用 Tailwind，搜索框和主题切换那几个小组件是 Svelte 写的，搜索索引靠 Pagefind 在构建时生成，不需要后端。托管在 GitHub Pages 上，push 到 `main` 就自动构建发布，不用自己碰服务器。

## 设计体系

2026-10 做过一轮全面重做，方向是「长文阅读 + 密排列表」，参考 leerob.io 的列表密度和 joshwcomeau.com 的正文排版。核心是**去卡片化**：正文和列表不再各自装进圆角卡片，改用细分隔线 + 留白划分层次。

- **字体**：`Inter Variable`（拉丁）+ `PingFang SC` / `Microsoft YaHei` / `Noto Sans SC`（中文）系统栈。**没引 Noto Sans SC 的 webfont**——中文全量包约 1.5MB/字重，不值当，系统字体已经够好。
- **正文**：18px / 1.75 行高，正文栏 `max-w-[42rem]`（672px，约 45 个中文字符一行）。
- **色板**：主色锁定 hue 250（`oklch(0.55 0.14 250)`），`themeColor.fixed: true`。强调色只出现在链接和当前态两处，不再满屏点缀。
- **圆角**：`--radius-lg` 从 1rem 收到 0.75rem，阴影基本去掉。
- **布局**：主栏 + **右侧** 12.5rem 窄栏（原左侧 280px 侧栏）。TOC 宽度从靠 `100vw` 反推的 `calc()` 改成固定 `11rem`，解掉了和栅格的隐式耦合。

设计令牌（字号阶梯、字体栈、圆角、间距）都集中在 `src/styles/variables.styl`。

## 平时怎么用

```bash
npm install
npm run dev        # localhost:4321
```

写文章就是在 `src/content/posts/` 里新建一个 `.md`。头部固定这几个字段：

```markdown
---
title: 文章标题
published: 2026-09-11
description: 一句话摘要，列表页和搜索结果里会显示
tags: [LangGraph, RAG]
category: AI 工程
draft: false
featured: false
---

正文。
```

`title` 和 `published` 是必须的，其余可省。`draft: true` 的文章不进构建，写一半先放着挺方便。`featured: true` 是给首页精选预留的标记，**目前首页还没接这个字段的读取逻辑**（首页现在直接取最新几篇），想用的话在 `src/pages/[...page].astro` 里按它筛。

正文除了标准 Markdown，还支持这些：

- `> [!NOTE]` 一类的小提示框（还有 TIP / WARNING / IMPORTANT）
- `::github{repo="owner/repo"}` 嵌一张仓库卡片
- KaTeX 数学公式
- 代码块自动带高亮、行号、复制按钮

其余常改的地方：

| 想改什么 | 去哪儿 |
|---|---|
| 站点标题、导航、社交链接、主题色 | `src/config.ts` |
| 首页简介文案（Default / Long 两版） | `src/components/Hero.astro` |
| 作品集列表 | `src/data/projects.ts` |
| 关于页 | `src/content/spec/about.md` |
| 设计令牌（字体、字号、圆角、色板） | `src/styles/variables.styl` |
| 样式入口（引入顺序） | `src/layouts/Layout.astro` |

头像那块现在不用图片了，首页是 `Hero.astro` 里一个纯文字 monogram（`H` 字母 + accent 色圆底），`src/assets/images/` 下的头像和 banner 图都已经删掉。

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

`scripts/publish.sh` 和 `scripts/local-server.ps1` 是早期部署在腾讯云轻量服务器（Caddy 容器跑 `--network host` + 只读挂载 `/srv/blog`）时写的，服务器到期后换成了 GitHub Pages，这俩已经用不上了，留着只是懒得删。现在本地起服务用 `scripts/serve-local.sh`。

## 许可

主题 MIT。文章内容默认 CC BY-NC-SA 4.0，不想要就在 `src/config.ts` 里把 `licenseConfig` 关掉。
