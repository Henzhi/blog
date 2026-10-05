# tutorials/ —— 系列教程写作底稿

这个目录**不参与网站构建**,Astro 不会读它。放在这里是为了管理写作过程:
一个主题从大纲、素材、草稿到定稿的完整轨迹。

## 发布流水线

```
tutorials/<主题>/          写作阶段:大纲、素材、草稿
        ↓  定稿后手工搬
src/content/posts/<主题>/   发布阶段:参与构建,生成页面
```

**成品必须搬进 `src/content/posts/<主题>/` 才会发布**,这里的稿子写完不等于上线。

## 为什么文章要放子目录

`src/content/posts/` 下**可以直接建子目录**,Astro 的 content collection 会递归读取
(已实测:放在 `posts/lexagent/` 下能正常构建、索引、生成页面)。

代价是 **URL 会带上子目录名**,因为 `[...slug].astro` 用 `entry.slug` 当路由参数,
而 Astro 的 `entry.slug` 包含子目录路径:

| 放法 | 生成的 URL |
|---|---|
| `posts/xxx.md` | `/blog/posts/xxx/` |
| `posts/lexagent/xxx.md` | `/blog/posts/lexagent/xxx/` |

**⚠️ 所以已经发布的文章不要随意移动**——改路径等于改 URL,旧链接会 404。
2026-10-05 做过一次**有意的迁移**:把 `lexagent-architecture-tutorial.md` 搬进
`posts/lexagent/01-architecture-overview.md`(当时无外链引用、无站内引用,影响可控)。
之后发布的新文一律直接放子目录,**不要再搬已经上线的文章**。

## ⚠️ 文件名不要用下划线开头

Astro 的 content collection **会忽略 `_` 开头的文件**(下划线约定为私有/非内容文件)。
实测:在 `posts/lexagent/` 下放 `_draft-test.md`,即使 `draft: false`,构建照样跳过它,
`Indexed N pages` 的数字不涨、`dist/` 下也不生成产物。

**这个坑的危险之处在于它和 `draft: true` 的表现完全一样**——两者都不进构建,
光看构建输出区分不出来,很容易把「文件名违例」误判成「草稿状态没改」,
然后反复去改 frontmatter 也解决不了。

判断方法:产物没生成时,**先 `ls` 看文件名有没有下划线前缀**,再去怀疑 frontmatter。
想标记草稿请用 `draft: true`,不要用文件名前缀。

## 从底稿到发布

```bash
cp tutorials/lexagent/02-retrieval.md src/content/posts/lexagent/02-retrieval.md
```

搬过去时注意三件事:

1. **frontmatter 要补齐**——底稿可以只写 `title`/`tags`/`category`,成品必须还有
   `published`(日期)、`description`、`draft: false`;
2. **`category` 只能填 `生活记录` / `学习笔记` / `教程笔记`**——
   `src/content/config.ts` 有 refine 校验,写别的构建直接失败;
3. **站内链接用相对路径**——子路径部署,裸 `/` 开头会跳到站点根目录 404。
   引用另一篇文章时注意子目录层数变了,相对路径也要跟着变。

然后跑验证:

```bash
npm run lint     # biome,CI 会拦
npm run build    # 真正验证:schema 校验 + 页面生成 + Pagefind 索引
```

**最后确认产物真的落地**:`ls dist/posts/<子目录>/<slug>/index.html`。
不要只看构建过程的绿色输出——`Indexed N pages` 的数字也要对得上。

之后 push,1-2 分钟自动上线。

## 目录约定

```
tutorials/
  README.md              ← 本文件
  <主题>/                ← 一个系列一个目录,如 lexagent/
    OUTLINE.md           ← 系列大纲:分几章、每章讲什么、发布状态
    <章节序号>-<slug>.md ← 章节底稿
```

**章节序号用两位数**(`01-`、`02-`),避免第 10 章排在第 2 章前面。
底稿的 slug 与最终 `src/content/posts/<主题>/` 里的文件名保持一致,便于对应。

## 已有系列

| 系列 | 目录 | 状态 |
|---|---|---|
| LexAgent 架构教程 | [`lexagent/`](./lexagent/) | 进行中,已发布 1 篇 |
