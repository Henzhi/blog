# Henzhi 的博客

线上在 https://henzhi.github.io/blog/，源码在 [github.com/Henzhi/blog](https://github.com/Henzhi/blog)。

底子是 Astro + [Fuwari](https://github.com/saicaca/fuwari) 主题，纯静态输出；样式用 Tailwind，搜索框和主题切换那几个小组件是 Svelte 写的，搜索索引靠 Pagefind 在构建时生成，不需要后端。托管在 GitHub Pages 上，push 到 `main` 就自动构建发布，不用自己碰服务器。

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
---

正文。
```

`title` 和 `published` 是必须的，其余可省。`draft: true` 的文章不进构建，写一半先放着挺方便。

正文除了标准 Markdown，还支持这些：

- `> [!NOTE]` 一类的小提示框（还有 TIP / WARNING / IMPORTANT）
- `::github{repo="owner/repo"}` 嵌一张仓库卡片
- KaTeX 数学公式
- 代码块自动带高亮、行号、复制按钮

其余要改的地方不多：站点信息（标题、导航、头像、社交链接）都在 `src/config.ts`；作品集列表在 `src/pages/projects.astro` 顶部的数组里；关于页是 `src/content/spec/about.md`。

## 发布

**正常流程就是 push**，没有别的动作：

```bash
git add -A && git commit -m "post: 新文章" && git push
```

`.github/workflows/deploy.yml` 会跑 `npm ci` → `npm run build`（含 Pagefind 索引）→ 传到 GitHub Pages。一两分钟看 https://henzhi.github.io/blog/ 就更新了。也可以在 Actions 页面手动点 `workflow_dispatch` 触发一次。

### 本地预览

GitHub Pages 部署在 `/blog/` 子路径下，所以本地验证也必须带着这个前缀，否则测不出 CSS/JS 404 这类问题：

```bash
npm run build && bash scripts/local-server.sh start   # http://localhost:4321/blog/
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
**用 npm 的话先删掉 `package.json` 里的 `preinstall`**。那行是 `npx only-allow pnpm`，主题官方推荐 pnpm，用 npm 装依赖会被它拦下来。

**构建报 `The link class does not exist` 就把 `node_modules/.vite` 删了**。这是 Tailwind 的 content 缓存坏了，把 `@layer` 里定义的自定义类当成没人用给裁掉了，于是另一处 `@apply link` 就找不到它。清 `.astro` 和 `dist` 都没用，得清 `.vite`。（Windows 下文件太多会被安全删除拦下来，用 `python -c "import shutil; shutil.rmtree('node_modules/.vite', ignore_errors=True)"` 稳一点。）

还有两处为了过 CI 的类型检查动过主题源码，以后升级 Fuwari 时注意别被覆盖掉：`ArchivePanel.svelte` 里 `Post.category` 的类型放宽成了 `string | null`（content collection 给的是这个）；`LightDarkSwitch.svelte` 里补了一句宽松的 props 声明，因为 Svelte 5 的 runes 组件不声明 props 时类型是 `Record<string, never>`，Astro 传下去的 `client:only` 会被判成非法属性。

**别用无头浏览器截图判断页面是否正常**。Fuwari 的 `.onload-animation` 初始是 `opacity: 0`，靠 300ms 的 CSS 动画淡入。截图跑太早会拍到一片空白，看起来像渲染坏了。加 `--virtual-time-budget=6000` 等动画播完再截。

## 以后要是绑自定义域名

仓库 Settings → Pages → Custom domain 填域名，域名那边加 CNAME 指向 `henzhi.github.io`，然后把 `astro.config.mjs` 的 `site` 改成域名、`base` 改成 `"/"`。HTTPS 证书 GitHub 自动签，勾上 Enforce HTTPS 就行。

（原来是部署在腾讯云轻量服务器上的，Caddy 容器跑 `--network host` + 只读挂载 `/srv/blog`。服务器到期后换成了 GitHub Pages，那套配置和 `scripts/publish.sh` 已经用不上了。）

## 许可

主题 MIT。文章内容默认 CC BY-NC-SA 4.0，不想要就在 `src/config.ts` 里把 `licenseConfig` 关掉。
