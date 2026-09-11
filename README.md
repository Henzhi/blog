# Henzhi 的个人博客与作品集

静态站点，用 [Astro](https://astro.build) + [Fuwari](https://github.com/saicaca/fuwari) 主题构建，部署在腾讯云轻量应用服务器（2 核 2G）上，由 Caddy 提供静态托管。

- 线上地址：http://82.156.238.96
- 源码仓库：https://github.com/Henzhi/blog

## 技术栈

| 层 | 选型 |
| --- | --- |
| 框架 | Astro 5（静态输出，默认零 JS） |
| 主题 | Fuwari |
| 样式 | Tailwind CSS 3 |
| 交互组件 | Svelte 5（搜索框、主题切换等） |
| 搜索 | Pagefind（构建后生成静态索引，不需要后端） |
| 代码高亮 | Expressive Code（Shiki） |
| 托管 | Caddy 2（Docker，`--network host`） |

## 本地开发

```bash
npm install          # 如果用 pnpm：pnpm install
npm run dev          # 起本地服务，默认 localhost:4321
npm run build        # 构建到 ./dist/，并生成 pagefind 搜索索引
npm run preview      # 本地预览构建产物
npm run check        # 类型检查
npm run new-post <filename>   # 新建一篇文章
```

> 主题官方推荐 pnpm。用 npm 也能跑，但 `package.json` 里的 `preinstall` 强制校验 pnpm，用 npm 时需要删掉那一行。

## 目录结构

```
src/
├── config.ts                 # ★ 站点配置集中在这里（标题、导航、头像、社交链接）
├── content/
│   ├── posts/                # ★ 博客文章，一个 .md 一篇
│   └── spec/about.md         # ★ 关于页内容
├── pages/projects.astro      # ★ 作品集页面（项目数据在文件顶部的数组里）
├── assets/images/            # 头像等本地图片
└── components/ layouts/      # 主题组件，一般不用改
```

要改的东西基本就四处在上面标了 ★ 的位置。

## 写文章

新建 `src/content/posts/xxx.md`：

```markdown
---
title: 文章标题
published: 2026-09-08
description: 列表页和 SEO 用的一句话摘要
tags: [LangGraph, RAG]
category: AI 工程
draft: false
---

正文。
```

frontmatter 字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | ✅ | 标题 |
| `published` | ✅ | 发布日期 |
| `description` |  | 摘要，不填会自动截取正文开头 |
| `tags` |  | 标签数组，用于标签页和筛选 |
| `category` |  | 分类，单值 |
| `draft` |  | `true` 时不进构建 |
| `image` |  | 封面图，相对当前 md 文件的路径 |

Markdown 额外支持：Admonitions（`> [!NOTE]`）、GitHub 仓库卡片（`::github{repo="..."}`）、KaTeX 数学公式、带行号和折叠的代码块。

## 部署到服务器

站点产物是纯静态的 `dist/`，服务器上的发布目录是 `/srv/blog`。

### 方式一：SSH + rsync（推荐）

先配好 SSH 免密登录，然后：

```bash
npm run build
rsync -avz --delete ./dist/ <用户名>@82.156.238.96:/srv/blog/
```

### 方式二：服务器自拉取源码构建

服务器上装好 Node 后：

```bash
cd /opt/blog && git pull && npm install && npm run build
sudo cp -r dist/* /srv/blog/
```

> 2 核 2G 跑 `npm run build` 内存偏紧，建议提前加 2G swap。

### 服务器上的 Caddy

```bash
docker run -d --name blog-caddy --network host --restart unless-stopped \
  -v /srv/blog:/srv/blog:ro \
  caddy:2-alpine caddy file-server --root /srv/blog --listen :80
```

⚠️ **必须用 `--network host`**。用 bridge + `-p 80:80` 时，容器 stop 再 start 后端口映射会失效，外部访问直接 502。

## 绑定域名 + HTTPS

1. 域名加 A 记录指向 `82.156.238.96`；
2. 腾讯云防火墙放行 443（TCP）；
3. 把 `astro.config.mjs` 里的 `site` 改成 `https://你的域名`；
4. Caddy 换成用配置文件启动：

   ```
   your-domain.com {
       root * /srv/blog
       file_server
       encode gzip
   }
   ```

   ```bash
   docker run -d --name blog-caddy --network host --restart unless-stopped \
     -v /srv/blog:/srv/blog:ro \
     -v /etc/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
     caddy:2-alpine
   ```

   Caddy 会自动申请并续期 Let's Encrypt 证书。

## 主题许可

Fuwari 基于 MIT License。文章内容默认采用 CC BY-NC-SA 4.0（可在 `src/config.ts` 的 `licenseConfig` 里关闭）。
