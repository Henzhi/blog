# 博客 UI 重构方案

> 撰写日期：2026-10-04
> 站点：https://henzhi.github.io/blog/
> 当前实现：Fuwari 主题（`src/layouts/MainGridLayout.astro` + `src/components/PostCard.astro`），仅改了 `config.ts` 里的 `themeColor.hue = 220`

---

## 一、结论先行

**现在的站点不是"丑"，是"没有判断"。** 它长得像任何一版 Fuwari：动漫头像、左侧三面板侧栏、右侧带边框的文章卡片、Roboto 正文。访客学到的是"这是个 Astro 博客"，不是"这是 Henzhi"。

**重构的目标不是换主题，是做三个决定**：

1. **首屏回答"你是谁"** —— 现在首屏是文章列表，看不到人，也看不到作品
2. **列表靠排版区分，不靠容器** —— 现在用卡片边框切分内容，改建制式排版（typographic rhythm）
3. **给中文长文配字体系统** —— 现在 Roboto 16px 撑中文技术长文，读久了累

**主参考选两个**：`leerob.io`（列表结构与求职属性）+ `joshwcomeau.com`（长文阅读体验）。这两个一个解决"首屏给人看什么"，一个解决"文章读着累不累"。

---

## 二、参考站点筛查（8 组，4 类取向）

### 实际走访并截图对比的站点

| 站点 | 取向 | 一句话评价 | 处置 |
|---|---|---|---|
| **leerob.io** | 编辑体 + 密排列表 | 文章用「标题 —— 日期」两列密排，零卡片零边框；Bio 支持 Default/Long 切换 | ✅ **主参考** |
| **joshwcomeau.com** | 技术长文阅读体 | 主栏文章 + 右栏分类/热门，非对称双栏；正文 18px / 行高 1.6 | ✅ **主参考** |
| **paco.me** | 极致留白 | 三栏并列（Building/Projects/Writing），灰阶 + 单点彩色；但字号偏小 | ⚠️ 备选，中文需上调整体 1–2px |
| **rauno.me** | 实验印刷体 | 单色块 + 大字号声明式排版，冲击力强 | ⚠️ 只借"敢留白"的态度，不照抄 |
| **astro-paper.pages.dev** | 极简单栏 | 纯反时序流，橙色调，结构最干净但也最没有个性 | ⚠️ 只借信息层级，不借视觉 |
| **simonwillison.net** | 日期分组时间轴 | 左正文右 Highlights 双栏，信息密度极高 | ⚠️ 只取"日期分组"这个结构 |
| **stephango.com** | 年份密排存档 | `2025 · 10` 前缀 + 标题，一行一条，密度冠军 | ✅ 存档页直接抄这个形式 |
| **jvns.ca** | 纯 HTML 编辑流 | 可用性顶级，视觉上刻意不出彩 | ❌ 不学视觉 |

### 从参考里明确"取"的六条

1. **文章列表密排**（leerob）—— 标题 + 日期两列，无边框无卡片，同屏 8–10 条
2. **右栏而非左栏**（joshwcomeau）—— 导航类信息放右侧窄栏，主栏优先给内容
3. **小写字距标签做分节**（joshwcomeau）—— `ARTICLES AND TUTORIALS` 式的节标题，中文对应「最新文章」加宽字距
4. **Bio 长度切换**（leerob）—— Default/Long 两档，兼顾扫读与深读
5. **年份密排存档**（stephango）—— `2025 · 10` 前缀 + 标题，替代现在的卡片流
6. **日期分组时间轴**（simonwillison）—— 首页文章列表按年/月分组，而非纯倒序

### 明确"不学"的四条

1. **不学 **rauno.me** 的单色块冲击** —— 求职场景需要展示具体产物（项目、技术栈），一张纯色块没有任何信息量
2. **不学 **jvns.ca** 的原色橙 + 斜纹边框** —— 视觉噪音大，且与"工程严谨"的定位冲突
3. **不学 **paco.me** 的小字号** —— 那是英文几何无衬线的特权，中文 13px 会糊
4. **不学 **simonwillison.net** 的信息密度** —— 他日均 3–5 条链接摘录，你日均 0.2 篇长文，密度不是你的问题

---

## 三、当前站点的四个结构性问题

### 1. 阅读体验被卡片切碎

`PostCard.astro` 每篇文章是一个 `card-base` 容器，配 `border-dashed` 移动端分隔线。视觉重心落在**容器边框**而非**标题文字**上——扫读时眼睛要先跨过边框再找内容。列表页读起来像应用面板，不像目录。

### 2. 侧边栏信息权重过高

`MainGridLayout.astro` 的栅格是 `grid-cols-[17.5rem_auto]`，即固定 280px 侧栏。侧栏里塞了 `Profile` + `Categories` + `Tags` 三个面板，标签云 20+ 个 pill 无优先级无分组。**内容只有 5 篇时，侧栏比正文还重**，首屏约 40% 宽度给了导航。

### 3. 没有"我是谁"的落点

头像 `src/assets/images/avatar.png` 是动漫人物图，与"计算机科学与技术 · AI 应用开发"的定位错位。作品集、关于都在二级导航里，访客进来第一眼看到的是文章，看不到产物。**对求职场景，第一印象是"这人写博客"，而不是"这人做过什么"。**

### 4. 排版没有观点

正文 Roboto 16px / 行高 1.75——这是模板默认值，不是设计决定。标题与正文对比不足，层级主要靠字重（400/500/700）区分。代码块、引用、表格沿用 Fuwari 默认样式，无特色。

---

## 四、设计 Token（可直接落地）

### 4.1 栅格与断点

```css
/* 替换 MainGridLayout.astro 的 grid-cols-[17.5rem_auto] */
--page-width: 78rem;      /* 原 72rem 左右，主栏需要空间 */
--sidebar-width: 12.5rem; /* 原 17.5rem，收掉 5rem */
--gap: 3rem;              /* 原 1rem(gap-4)，栏间距拉开 */
```

| 断点 | 布局 |
|---|---|
| `< 768px` | 单栏，窄栏内容折叠为汉堡菜单 |
| `768–1024px` | 单栏主内容 + 顶部横向导航 |
| `≥ 1024px` | 主栏 + 右窄栏（`grid-cols-[minmax(0,1fr)_12.5rem]`） |
| `≥ 1440px` | 同上，主栏上限 `max-width: 44rem` 保证行长 |

**关键约束**：正文行长控制在 `38–44rem`（约 42–48 个中文字符/行）。中文比英文宽，行长超过 48 字阅读时容易跳行。

### 4.2 字体系统

```css
--font-sans: "Inter", "Noto Sans SC", -apple-system, "PingFang SC",
             "Microsoft YaHei", sans-serif;
--font-serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
--font-mono: "JetBrains Mono", "Cascadia Code", "SF Mono", Consolas, monospace;
```

**改动的关键点**：正文从中性的 Roboto 换成 `Inter + Noto Sans SC` 组合。Inter 的几何骨架在英文/数字上比 Roboto 更利落，Noto Sans SC 是思源黑体，与 Inter 的字面比例接近，混排不会断层。

```css
/* 字号阶梯（替换 Fuwari 默认） */
--text-hero: 3rem;       /* 48px · 权重 500 · 行高 1.1 */
--text-h1: 2rem;         /* 32px · 权重 500 · 行高 1.25 */
--text-h2: 1.5rem;       /* 24px · 权重 500 · 行高 1.35 */
--text-h3: 1.25rem;      /* 20px · 权重 500 · 行高 1.4  */
--text-body: 1.125rem;   /* 18px · 权重 400 · 行高 1.75 ← 从 16px 提到 18px */
--text-small: 0.9375rem; /* 15px · 权重 400 · 行高 1.6  */
--text-meta: 0.8125rem;  /* 13px · 权重 400 · 行高 1.5  */
--text-label: 0.75rem;   /* 12px · 权重 500 · 字距 0.08em · 大写 */
```

**只有三档字重**：400（正文）/ 500（标题与强调）/ 600（仅 Hero 与页面大标题）。

### 4.3 色彩

现在的 `variables.styl` 用 `oklch(0.70 0.14 var(--hue))` 派生全套色彩，体系是好的，**问题是强调色用得太广**——标题前的竖条、chevron 箭头、分类计数、标签 pill、分页按钮全是同一个蓝。

**改动策略：把彩色收回来，只保留两处。**

```css
/* 深色模式（主场景） */
--bg-page:      oklch(0.145 0.008 240);  /* 近黑，比现在 0.16 略深 */
--bg-surface:   oklch(0.205 0.010 240);  /* 卡片/浮层 */
--bg-elevated:  oklch(0.255 0.012 240);  /* 悬浮态 */

--text-primary:   oklch(0.96 0.005 240);
--text-secondary: oklch(0.72 0.010 240);
--text-tertiary:  oklch(0.52 0.010 240);

--border-subtle: oklch(0.30 0.010 240);  /* 0.5px 细线 */
--accent:        oklch(0.72 0.15 250);   /* 保留蓝，仅用于链接与当前态 */
--accent-muted:  oklch(0.45 0.06 250);   /* 弱化强调，用于时间线节点 */
```

**两处保留彩色**：① 正文内链接；② 导航当前项。其余全部走灰阶。

- 分类计数徽标 → 从彩色 pill 改为纯文本数字
- 文章卡片 chevron → 删除
- 标题前竖条 → 删除
- 标签 pill → 改为无底色 + 细边框

### 4.4 间距与圆角

```css
--space-unit: 0.25rem;
--space-section: 4rem;    /* 主要区块间距 */
--space-block: 2rem;      /* 区块内间距 */
--space-item: 1.25rem;    /* 列表项之间 */

--radius-sm: 4px;
--radius-md: 8px;         /* 输入框、小元件 */
--radius-lg: 12px;        /* 卡片 */
/* 全局移除更大的圆角与多重阴影 */
```

---

## 五、页面级改造清单

### 5.1 首页（`src/pages/index.astro`）

**改造后结构**（自上而下）：

| 区块 | 内容 | 参考来源 |
|---|---|---|
| ① Hero | 姓名 + 一句话定位 + 两个入口按钮（「看作品集」/「读文章」） | leerob |
| ② 精选作品 | 4 个项目横向密排，每项：项目名 + 状态 + 一句话 + 技术栈纯文本 | 现有 projects.astro 改造 |
| ③ 最新文章 | 标题 + 日期两列密排，显示 6 条，底部「全部文章 →」 | leerob |
| ④ 右窄栏 | 分类 4 项、标签 Top 8、最近更新 | joshwcomeau |

**Hero 文案建议**（现在的 `subtitle` 偏长，且"把模型能力落到能跑的工程上"是个抽象说法）：

```
Henzhi
计算机科学与技术 · 北京化工大学 2027 届

我在做法律 RAG 与 AI Agent —— 关心的是它跑不跑得起来、
答得准不准、钱花不花得起。

[看作品集 →]  [读文章 →]
```

**为什么这么改**：现在 `subtitle` 是"AI Agent · 全栈 · 把模型能力落到能跑的工程上"，三个并列词 + 一句抽象描述。改成具体的三件事（跑得起来 / 答得准 / 花得起钱），既扣住你做 LexAgent 时真实关注的点，也让访客 3 秒内知道你的技术判断力在哪。

### 5.2 文章列表（`PostCard.astro` 重写）

**删除**：`card-base` 容器、圆角、封面图位、hover 遮罩、chevron 图标、`border-dashed` 分隔线

**改为**：

```
标题（18px/500，链接色）                                    2026-09-08
一句话摘要（15px，次级色，最多两行）
LangGraph · RAG · Agent                          800 字 · 4 分钟
────────────────────────────────────────────────────────────
```

分隔线用 `border-bottom: 0.5px solid var(--border-subtle)`，比现在的虚线干净。

**标签改为纯文本**：`LangGraph · RAG · Agent`，中间用 `·` 分隔，不用 pill 背景。理由——20 个配色 pill 会形成视觉噪音，而纯文本权重低、扫读时不会抢标题。

### 5.3 文章详情页

- **正文宽度**：`max-width: 42rem`，居中
- **TOC**：从右侧浮动改为主栏内左侧固定（`≥ 1280px`），或在窄栏内折叠
- **元信息行**：日期 · 阅读时长 · 分类，放在 H1 下方一行，13px 次级色
- **代码块**：保留 `github-dark`，但加大内边距（`1.25rem`）、行高提到 `1.7`
- **引用块**：从现在的左侧粗边框改为左侧 2px 细线 + 无背景
- **表格**：加 `border-collapse` + 行分隔细线，去掉外框

### 5.4 存档页（`archive.astro`）

**直接采用 stephango 的形式**：年份/月份前缀 + 标题密排。

```
2026 · 10   这个站点是怎么搭起来的（以及踩的几个坑）
2026 · 09   用多模态大模型从 PDF 里「抠」出结构化题库
2026 · 09   select-ask-ai：做一款「选中即问」的工具，最大的坑不在 AI
2026 · 08   用 LangGraph 搭法律 RAG Agent：为什么我放弃了 LangChain 的工具绑定
```

日期用等宽字体 `var(--font-mono)` 保证对齐，标题用链接色。一行一条，不做年份分组标题（内容量还不到需要分组的程度）。

### 5.5 作品集（`projects.astro`）

现在的实现已经是两列卡片网格，方向对，但视觉上和文章卡片同质。改动：

- 项目名 + 状态徽标（`进行中` / `维护中` / `重构中`）放一行
- 用**左侧色条**区分状态：进行中 = accent、维护中 = 绿、重构中 = 琥珀（各 3px 宽）
- 技术栈改为纯文本 `LangGraph · RAG · Agent · PostgreSQL`
- 「查看源码 →」改为整卡可点击，右下角一个 `↗` 图标

---

## 六、实施计划（分四阶段，每阶段可独立上线）

### 阶段 1 · Token 层（低风险，1 次提交）

**目标**：改 `variables.styl` + `postcss.config.mjs`，不动任何组件结构。

- [ ] 引入 Inter + Noto Sans SC（`@fontsource` 或本地 woff2，注意中文字体体积——建议只引 `Noto Sans SC` 的 `400/500` 两个字重，用 unicode-range 分包）
- [ ] 替换字号阶梯，正文 16px → 18px
- [ ] 色彩收敛：强调色限定到链接与当前态两处
- [ ] 移除大圆角与多重阴影

**验证**：截图对比改前改后，确认深色模式正文对比度 ≥ 7:1（WCAG AAA）。

⚠️ **风险**：中文字体文件大。`Noto Sans SC` 全量 woff2 约 1.5MB/字重。**必须用 Google Fonts 的 unicode-range 分包版本**，或直接依赖系统字体 `PingFang SC` / `Microsoft YaHei`。建议先只上 Inter（拉丁）+ 系统中文，观察效果再决定是否引入 Noto Sans SC。

### 阶段 2 · 布局层（中风险，需同步改组件）

**目标**：栅格从「左 280 + 右自适应」改为「主栏 + 右 200」。

- [ ] `MainGridLayout.astro` 的 `grid-cols` 改写，侧栏移到右侧
- [ ] `SideBar.astro` 拆解：`Profile` 移出侧栏（进 Hero），保留分类/标签/最近更新
- [ ] `Categories.astro` 计数徽标改纯文本
- [ ] `Tags.astro` 改为 Top 8 + 「全部标签 →」

⚠️ **同步检查（已核实）**：`MainGridLayout.astro:66` 的 `grid-cols-[17.5rem_auto]` 与 `variables.styl:96` 的 TOC 宽度是**隐式耦合**的——

```styl
--toc-width: calc((100vw - var(--page-width)) / 2 - 1rem)
```

TOC 宽度由 `100vw` 减页面宽度后除以 2 推出，而 `MainGridLayout.astro:109/112` 用 `-right-[var(--toc-width)]` 把它挂到主区右侧。

**这里有个隐藏问题**：`100vw` 包含滚动条宽度，且 TOC 本身定位在 `max-w-[var(--page-width)]` 容器之外。侧栏从左侧 280px 改到右侧 200px 后，若不同步调整，会出现两种失败：① TOC 与右栏重叠；② TOC 溢出视口产生横向滚动条。

**改法**：把 `--toc-width` 从 `calc(100vw...)` 改为固定值（如 `14rem`），并让 TOC 定位改为主栏内部的 `position: sticky`，不再依赖 `100vw` 反推。同时 `MainGridLayout.astro:106` 的 `hidden 2xl:block` 断点要跟着栅格调整。

另外注意 `PostCard.astro:109` 的 `<style define:vars={{coverWidth}}>` ——重写 PostCard 时删掉封面图逻辑后，这个 style 块也要一并清理。

### 阶段 3 · 组件层

- [ ] `PostCard.astro` 重写为密排列表项（删封面图逻辑，`PostMetadata` 简化）
- [ ] `Profile.astro` 改造为 Hero 组件，加 Default/Long 切换
- [ ] `archive.astro` 改为年份密排
- [ ] `projects.astro` 加状态色条

### 阶段 4 · 内容与素材（与代码解耦，可并行）

- [ ] **换头像**：替换 `src/assets/images/avatar.png`，或改为纯文字 monogram（`H` 字母 + accent 色圆底）——后者更省事且不会有"动漫头像 vs 工程师定位"的错位
- [ ] **补 `featured` 字段**：`src/content/config.ts` 的 `postsCollection` schema 当前字段为 `title / published / updated / draft / description / image / tags / category / lang` + 4 个内部字段，**没有 `featured`**。需新增 `featured: z.boolean().optional().default(false)`，用于首页精选。注意 `src/content/spec/about.md` 走的是另一个空 schema 集合，不受影响。
- [ ] **删无用素材**：`demo-avatar.png` / `demo-banner.png` 是模板自带，`banner.enable: false` 时用不到

---

## 七、验收标准

改完必须满足（逐条可验证）：

| 项 | 标准 | 验证方式 |
|---|---|---|
| 首屏信息 | 不滚动即可看到姓名 + 定位 + 作品入口 | 1440×900 截图 |
| 列表密度 | 同屏可见 ≥ 7 条文章 | 1440×900 截图计数 |
| 正文可读性 | 行长 ≤ 48 中文字符 | 量 `max-width` 实测 |
| 对比度 | 深色模式正文 ≥ 7:1 | Lighthouse / axe |
| 子路径资源 | 所有 `/_astro/*` 带 `/blog/` 前缀 | `grep -o '/blog/_astro/[^"]*'` 计数 |
| 无布局溢出 | 无横向滚动条 | CDP 查 `scrollWidth > clientWidth` |
| 入场动画 | 截图不空白 | 加 `--virtual-time-budget=6000` |
| 构建 | `npm run build` 通过且含 pagefind | 检查 `dist/pagefind/` 存在 |

---

## 八、明确不做

- ❌ **不换主题框架**。Fuwari 的组件划分是清楚的（`widget/` `control/` `misc/`），改造比迁移到 AstroPaper 便宜得多，且现有 5 篇文章的 frontmatter 不用动
- ❌ **不上重型动效**。`onload-animation` 已经够用，再加 Framer Motion 类的方案会拖慢首屏，且与"工程严谨"的定位不符
- ❌ **不加 hero 大插画**。leerob 的插画是雇人画的一整套视觉资产，自制成本高、效果差。用纯排版做视觉锚点更稳
- ❌ **不做亮色模式优先**。你现在的暗色是主场景，亮色作为兜底保持可用即可，不为它单独设计
