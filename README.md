# Henzhi 的博客

线上在 http://82.156.238.96，源码在 [github.com/Henzhi/blog](https://github.com/Henzhi/blog)。

底子是 Astro + [Fuwari](https://github.com/saicaca/fuwari) 主题，纯静态输出；样式用 Tailwind，搜索框和主题切换那几个小组件是 Svelte 写的，搜索索引靠 Pagefind 在构建时生成，不需要后端。托管在腾讯云一台 2 核 2G 的轻量服务器上，就一个 Caddy 的 Docker 容器，没别的中间件。

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

```bash
bash scripts/publish.sh
```

它会构建、打包、传到服务器，最后自己 curl 一下首页确认返回 200。`SERVER`、`REMOTE_DIR`、`SITE_URL` 三个环境变量能覆盖默认值，一般用不上。

前提是本机能免密 ssh 到服务器。`~/.ssh/config` 里早就配了 `tencent` 这个别名（root@82.156.238.96），但服务器上一直没放公钥，所以先装一次：

```bash
cat ~/.ssh/id_ed25519.pub | ssh root@82.156.238.96 \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

会问一次 root 密码，之后就免密了（忘了可以在腾讯云控制台重置）。

不想跑脚本就手动来：

```bash
npm run build
tar czf - -C dist . | ssh tencent "rm -rf /srv/blog/* && tar xzf - -C /srv/blog"
```

## 几个坑，别再踩一遍

**别整目录替换 `/srv/blog`**。Caddy 是只读挂载这个目录的，你要是删完再把一个新目录 `mv` 过去，容器里那个挂载点还指着旧 inode，页面纹丝不动，很容易怀疑人生。清空内容再原地覆盖才对（上面的命令就是这么写的），`rsync --delete` 同理。

**Caddy 得用 `--network host`**。一开始用 `-p 80:80` 的 bridge 模式，容器 stop 再 start 之后端口映射就丢了，外面访问直接 502。换成 host 网络后 Caddy 直接绑宿主机 80，没这毛病：

```bash
docker run -d --name blog-caddy --network host --restart unless-stopped \
  -v /srv/blog:/srv/blog:ro \
  caddy:2-alpine caddy file-server --root /srv/blog --listen :80
```

**用 npm 的话先删掉 `package.json` 里的 `preinstall`**。那行是 `npx only-allow pnpm`，主题官方推荐 pnpm，用 npm 装依赖会被它拦下来。

还有两处为了过 CI 的类型检查动过主题源码，以后升级 Fuwari 时注意别被覆盖掉：`ArchivePanel.svelte` 里 `Post.category` 的类型放宽成了 `string | null`（content collection 给的是这个）；`LightDarkSwitch.svelte` 里补了一句宽松的 props 声明，因为 Svelte 5 的 runes 组件不声明 props 时类型是 `Record<string, never>`，Astro 传下去的 `client:only` 会被判成非法属性。

## 以后要是绑域名

域名加一条 A 记录指向 `82.156.238.96`，防火墙放行 443，把 `astro.config.mjs` 里的 `site` 换成正式域名，然后 Caddy 改成读配置文件启动：

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

证书 Caddy 自己申请和续期，不用管。

## 许可

主题 MIT。文章内容默认 CC BY-NC-SA 4.0，不想要就在 `src/config.ts` 里把 `licenseConfig` 关掉。
