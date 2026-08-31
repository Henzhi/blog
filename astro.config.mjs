import { defineConfig } from 'astro/config';

// 站点根地址，用于生成 sitemap / 规范链接。
// 当前用服务器 IP 走 HTTP；以后绑定域名改成 https://你的域名
export default defineConfig({
  site: 'http://82.156.238.96',
  server: { host: true },
});
