/* 新建一篇博客的骨架文件
 *
 * 用法：
 *   npm run new-post -- <slug> ["文章标题"]
 *
 * slug 会成为文件名和 URL，用英文小写加连字符；中文标题作为第二个参数传入。
 * 例如：npm run new-post -- lexagent-budget-breaker "LexAgent 的预算熔断是怎么做的"
 * 不传标题时，slug 本身充当 title。
 */

import fs from "node:fs"
import path from "node:path"

const [slugArg, titleArg] = process.argv.slice(2)

if (!slugArg) {
	console.error(`用法：npm run new-post -- <slug> ["文章标题"]

  slug   文件名与 URL，英文小写加连字符，例如 lexagent-budget-breaker
  title  中文标题，可选；不传则用 slug 充当

示例：npm run new-post -- lexagent-budget-breaker "LexAgent 的预算熔断是怎么做的"`)
	process.exit(1)
}

const slug = slugArg.replace(/\.(md|mdx)$/i, "")
const title = titleArg?.trim() || slug
const targetDir = "./src/content/posts"
const fullPath = path.join(targetDir, `${slug}.md`)

if (fs.existsSync(fullPath)) {
	console.error(`文件已存在：${fullPath}`)
	process.exit(1)
}

const now = new Date()
const published = [
	now.getFullYear(),
	String(now.getMonth() + 1).padStart(2, "0"),
	String(now.getDate()).padStart(2, "0"),
].join("-")

// 字段与 src/content/config.ts 的 schema 对齐（另外还支持 image / lang，需要时自己加）。
// category 只能填 生活记录 / 学习笔记 / 教程笔记，留空即「未分类」；填别的构建会直接报错。
const content = `---
title: ${title}
published: ${published}
description: ''
tags: []
category: ''
draft: false
featured: false
---

`

fs.writeFileSync(fullPath, content, "utf8")
console.log(`已创建 ${fullPath}
写一半想先存着，把 draft 改成 true；写完确认 category 填了三个分类之一。`)
