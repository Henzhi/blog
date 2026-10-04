---
title: 这个站点是怎么搭起来的（以及踩的几个坑）
published: 2026-09-08
description: Astro + Fuwari 静态站点，从自建服务器迁到 GitHub Pages，记录子路径部署、无头截图假象、配色缓存这几个真实的坑。
tags: [Astro, 部署, GitHub Pages, 工程]
category: 工程
draft: false
---

第一版站点做完之后我自己都看不下去：一个字母方块当头像、项目状态用 `● 维护中` 这种纯文本凑、博客只有一篇 hello world。所以推倒重来了一遍，顺手把过程记下来。

## 选型

- **Astro** — 静态输出，默认零 JS，构建完就是一堆 HTML/CSS
- **Fuwari** — Astro 生态里的博客主题，自带搜索、标签、归档、RSS、代码高亮、暗色模式
- **Pagefind** — 构建后扫描 HTML 生成搜索索引，纯静态，不需要任何服务端

一开始是跑在一台 2 核 2G 的轻量服务器上，用 Caddy 做静态托管。后来那台服务器到期没续费，就换成了 GitHub Pages —— 免费、有公网地址、不用自己维护机器，代价是部署在 `/<repo>/` 子路径下，多了一些坑。

## 坑一：子路径部署，`base` 配错会全站裸奔

GitHub Pages 的项目站地址是 `https://<user>.github.io/<repo>/`，所以 Astro 配置里必须同时写 `site` 和 `base`：

```js
site: "https://henzhi.github.io",
base: "/blog",       // 必须和仓库名一致
```

`base` 写错的症状很有辨识度：页面能打开，但**样式全丢，变成裸 HTML**。因为资源引用是根路径的 `/_astro/xxx.css`，在子路径下会请求到 `https://henzhi.github.io/_astro/xxx.css`，404。

改完一定要验一遍资源前缀：

```bash
grep -o '/blog/_astro/[^"]*' dist/index.html | head
```

**还有一个只有手写页面才会踩的坑**：Astro 官方的 sitemap 集成会自动带上 `base`，但自己写的 `rss.xml.ts` 不会 —— `context.site` 只返回 origin，不含 `base`。结果是 RSS 的 `<channel><link>` 指向了站点根目录。得手动补：

```ts
const siteRoot = new URL(import.meta.env.BASE_URL, context.site);
```

## 坑二：无头截图会把「动画没播完」看成「页面空白」

用 `chrome --headless --screenshot` 验证页面时，首页文章列表**一片空白**，侧边栏却正常。差点以为是渲染 bug。

实际上是 Fuwari 的入场动画在作祟：

```css
.onload-animation {
    opacity: 0;
    animation: 300ms fade-in-up;
    animation-fill-mode: forwards;
}
```

初始 `opacity: 0`，靠 CSS 动画淡入。截图拍得太早，动画还没开始，自然全黑。

解法是加 `--virtual-time-budget`，让 Chrome 推进虚拟时钟等动画播完：

```bash
chrome --headless=new --virtual-time-budget=6000 \
  --screenshot=out.png https://henzhi.github.io/blog/
```

## 坑三：`file://` 打开构建产物验证是无效的

想省事直接拿浏览器打开 `dist/index.html` 看效果 —— 结果是一片裸页面，同样会误判成构建坏了。

原因是根路径 `/blog/_astro/...` 在 `file://` 协议下会被解析成 `C:\blog\_astro\...`，文件根本不存在。**验证静态站点必须起 HTTP 服务，而且目录结构得是 `根/blog/构建产物`**，才能模拟出 Pages 的子路径环境。

## 坑四：装包卡在缓存锁上

`npm install` 跑了十分钟没动静，看 `node_modules` 是空的。逐步排查：

```bash
npm install --cache /tmp/npmcache2 --registry https://registry.npmmirror.com
```

换一个独立的缓存目录立刻就装上了。原因是有另一个 npm 进程占着默认缓存目录的锁，新进程拿不到写权限就直接卡住 —— 而且**不报错**，只是静默等待。

判断方法：`node_modules` 长时间为空 + 没有网络错误，八成是锁，不是网。

还有一个隐蔽的：Windows 下强杀 npm 进程会让包残缺。`taskkill` 打断了解压阶段，留下半截 `node_modules`，npm 不会自动修复，构建必然失败。判断「卡死还是慢」的办法是连续看 `ls node_modules/*/package.json | wc -l` 有没有在增长。

## 坑五：Tailwind 缓存坏了会报莫名其妙的错

构建报 `The link class does not exist`，看着像 CSS 写错了。实际是 Vite/Tailwind 的 content 缓存与当前依赖树不一致 —— 它把 `@layer` 里定义的自定义类当成「没人用」裁掉了，于是另一处 `@apply` 就找不到。

清 `.astro` 和 `dist` 都没用，**必须删 `node_modules/.vite`**。重装依赖之后尤其容易遇到。

## 部署流程

现在整个发布就是一次 push：

```bash
git add -A && git commit -m "post: 新文章" && git push
```

GitHub Actions 会跑 `npm ci` → `npm run build` → 发布到 Pages。

这里踩过一个坑：`configure-pages` 在仓库没启用 Pages 时会报

```
HttpError: Not Found
Get Pages site failed. Please verify that the repository has Pages enabled...
```

这个报错很误导 —— 看着像配置写错了，其实前一步 `Build site` 是成功的，纯粹是仓库设置里 Pages 还没开。**这一步只能手动点，没有纯 API 的路径**（那个 `enablement: true` 参数要求 `GITHUB_TOKEN` 之外、带 `repo` scope 的 token，CI 里拿不到）。

## 现在的状态

- 主题 Fuwari，配置集中在 `src/config.ts`
- 内容用 Content Collections 管理，写文章就是往 `src/content/posts/` 丢 Markdown
- 搜索由 Pagefind 在构建后生成索引，不需要服务端
- 托管在 GitHub Pages，push 即发布

接下来要补的是：自定义域名 + HTTPS、把内容写厚。
