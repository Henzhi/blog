# 个人博客与作品集

基于 **Astro** 的纯静态站点，部署在腾讯云轻量应用服务器（2 核 2G）上，通过 Docker 中的 Caddy 提供 HTTP 服务。

## 目录结构

- `src/pages/` 页面（首页 `index.astro`、博客 `blog/`、关于 `about.astro`）
- `src/content/posts/` 博客文章（Markdown）
- `src/data/projects.ts` 作品集数据
- `src/components/` 组件（Header / Footer / ProjectCard）
- `src/layouts/BaseLayout.astro` 页面外壳
- `docker/` 服务器 Caddy 配置
- `scripts/deploy.sh` 本地构建 + 上传脚本

## 本地开发

```bash
cd C:\Code\VibeCoding\blog
npm install
npm run dev      # 本地预览 http://localhost:4321
```

## 写内容

- **新博客**：在 `src/content/posts/` 新建 `xxx.md`，头部写 frontmatter：

  ```md
  ---
  title: 标题
  description: 简介
  pubDate: 2026-08-31
  tags: ["标签"]
  ---
  正文用 Markdown 写。
  ```

- **加作品**：编辑 `src/data/projects.ts`，往 `projects` 数组里加一项。

## 构建

```bash
npm run build    # 产物在 dist/
```

## 部署到服务器（本地构建 + 上传）

1. 第一次：在服务器上做一次准备（见下）。
2. 之后每次更新：

   ```bash
   bash scripts/deploy.sh
   ```

   脚本会 `npm run build` 并把 `dist/` 用 rsync 上传到服务器的 `/srv/blog`。
   上传前请把 `scripts/deploy.sh` 里的 `SERVER` 改成你的 `用户名@82.156.238.96`，并确保本机到服务器已配置 SSH（密钥或密码）。

## 服务器一次性准备（SSH 登录后执行）

```bash
# 建站点目录
sudo mkdir -p /srv/blog

# 写 Caddy 配置（HTTP 80）
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
:80 {
	root * /srv/blog
	file_server
	encode gzip
}
EOF

# 起 Caddy 容器（Docker 已预装）
docker run -d --name blog-caddy --restart unless-stopped \
  -p 80:80 \
  -v /srv/blog:/srv/blog:ro \
  -v /etc/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  caddy:2-alpine
```

之后访问 `http://82.156.238.96` 即可。

## 以后绑定域名 + 上 HTTPS

1. 域名 A 记录指向 `82.156.238.96`。
2. 防火墙加一条 443(TCP) 放行规则。
3. 把 Caddyfile 改成：

   ```
   your-domain.com {
   	root * /srv/blog
   	file_server
   	encode gzip
   }
   ```

   Caddy 会自动申请并续期 Let's Encrypt 证书，无需手动操作。
4. 重启容器：`docker restart blog-caddy`。

## 资源占用说明

纯静态托管，运行时几乎只消耗文件 IO 与少量内存，2 核 2G 完全够用；构建在本地完成，不占服务器算力。
