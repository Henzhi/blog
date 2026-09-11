---
title: 这个站点是怎么搭起来的（以及踩的几个坑）
published: 2026-09-08
description: Astro + Fuwari 主题跑在 2 核 2G 的轻量服务器上，记录 Caddy 网络模式、装包缓存锁、无 SSH 上传这几个真实的坑。
tags: [Astro, 部署, Docker, 服务器]
category: 工程
draft: false
---

第一版站点做完之后我自己都看不下去：一个字母方块当头像、项目状态用 `● 维护中` 这种纯文本凑、博客只有一篇 hello world。所以推倒重来了一遍，顺手把过程记下来。

## 选型

服务器是 2 核 2G，跑不了什么重东西，所以技术选型上只有一个原则：**构建要轻，运行要静**。

- **Astro** — 静态输出，默认零 JS，构建完就是一堆 HTML/CSS
- **Fuwari** — Astro 生态里的博客主题，自带搜索、标签、归档、RSS、代码高亮、暗色模式
- **Caddy** — 一个二进制搞定静态托管，以后上 HTTPS 只要改一行配置

## 坑一：Caddy 用 bridge 映射，容器重启后就失联

最初是这么起的：

```bash
docker run -d -p 80:80 -v /srv/blog:/srv/blog:ro caddy:2-alpine ...
```

能访问。但 `docker stop` 再 `docker start` 之后，外部访问直接 **502**。查下来是 bridge 模式的端口映射在重启后没生效：`docker inspect` 里 `PortBindings` 配置还在，但 `docker port` 返回空，docker-proxy 没起来。

改成 host 网络，Caddy 直接绑宿主机的 80 端口，绕开 docker-proxy：

```bash
docker run -d --name blog-caddy --network host --restart unless-stopped \
  -v /srv/blog:/srv/blog:ro \
  caddy:2-alpine caddy file-server --root /srv/blog --listen :80
```

重启之后不再出问题。

## 坑二：装包卡在缓存锁上

`npm install` 跑了十分钟没动静，看 `node_modules` 是空的。逐步排查：

```bash
npm install --cache /tmp/npmcache2 --registry https://registry.npmmirror.com
```

换一个独立的缓存目录立刻就装上了。原因是有另一个 npm 进程占着默认缓存目录的锁，新进程拿不到写权限就直接卡住——而且**不报错**，只是静默等待。

判断方法：`node_modules` 长时间为空 + 没有网络错误，八成是锁，不是网。

## 坑三：没有 SSH 通道时怎么把产物传上去

沙箱环境连不上服务器的 SSH，常规的 `rsync` 走不通。临时方案是在服务器上起一个一次性接收端：

```python
# 服务器上临时运行
import http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        open("/tmp/blog.tar.gz", "wb").write(self.rfile.read(n))
        self.send_response(200); self.end_headers()
http.server.ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
```

本地打包上传：

```bash
tar czf dist.tar.gz -C dist .
cat dist.tar.gz | curl -s -X POST --data-binary @- http://<ip>/
```

能用，但不体面——不可复现、不能回滚。正经做法还是配好 SSH key 走 rsync，或者让服务器直接 `git pull` 后自己构建。这个后面会换掉。

## 现在的状态

- 主题换成 Fuwari，配置集中在 `src/config.ts` 一个文件里
- 内容用 Content Collections 管理，写文章就是往 `src/content/posts/` 丢 Markdown
- 搜索由 pagefind 在构建后生成索引，不需要服务端
- 部署目录 `/srv/blog`，Caddy 以 host 网络常驻

接下来要补的是：域名 + HTTPS、正规化部署流程、以及把内容写厚。
