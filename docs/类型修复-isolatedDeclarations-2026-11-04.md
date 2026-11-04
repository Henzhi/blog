# isolatedDeclarations 显式类型问题修复记录

- 日期：2026-11-04
- 状态：已完成修复与验证
- 范围：`npm run type-check`（TypeScript 5.9.3，`tsc --noEmit --isolatedDeclarations`）
- 基线提交：`b1331e8 feat: 优化移动端阅读体验与信息层级`
- 处理原则：不修改业务逻辑、不删除文件、不新增诊断抑制、不关闭 `isolatedDeclarations`

## 1. 问题基线

修复前运行 `npm run type-check` 得到 12 条诊断，普通 `tsc --noEmit --project tsconfig.json` 通过。说明当前问题集中在导出声明的可移植性，而不是已证实的运行时错误或普通类型检查错误。

| 文件与位置 | 数量 | 诊断 | 直接原因 |
| --- | ---: | --- | --- |
| `src/constants/constants.ts:6,11` | 2 | TS9010 | 导出常量由其他常量或算术表达式初始化，缺少显式类型标注 |
| `src/constants/local-icons.ts:16` | 1 | TS9010 | `as const satisfies` 不能替代 isolatedDeclarations 要求的变量类型标注 |
| `src/content/config.ts:38,39` | 2 | TS9013 | 导出 `collections` 的属性依赖 `defineCollection` 的复杂 Zod 泛型推断，无法直接生成可移植声明 |
| `src/pages/rss.xml.ts:19` | 1 | TS9007 | 导出 `GET` 缺少返回类型，当前经 `rss()` 推断为 `Promise<Response>` |
| `src/plugins/expressive-code/custom-copy-button.ts:4` | 1 | TS9007 | 插件工厂函数缺少返回类型 |
| `src/plugins/expressive-code/language-badge.ts:6` | 1 | TS9007 | 插件工厂函数缺少返回类型 |
| `src/utils/content-utils.ts:20` | 1 | TS9007 | `getSortedPosts` 依赖 Astro Collection 返回类型推断 |
| `src/utils/setting-utils.ts:30` | 1 | TS9007 | `applyThemeToDocument` 缺少 `void` 返回类型 |
| `src/utils/url-utils.ts:4,42` | 2 | TS9007 | `pathsEqual`、`url` 缺少返回类型 |

## 2. 影响范围

- 不影响当前页面运行逻辑；普通 TypeScript 检查已通过。
- 阻塞将 `npm run type-check` 作为质量门禁的提交或 CI 流程。
- 若需要生成 `.d.ts`，这些导出边界不能由 TypeScript 在 isolatedDeclarations 模式下可靠地产出声明。
- 修复只涉及类型标注、类型导入和本地图标生成器的类型保留方式，不调整页面结构、样式、数据处理、RSS 内容或插件行为。

## 3. 原因分析

`isolatedDeclarations` 要求导出的变量和函数具有无需跨文件、跨包深入推断即可生成的显式类型。当前代码在普通类型检查下可以依赖推断，但以下边界不满足声明生成要求：

1. 简单导出值和函数依赖初始化表达式或返回表达式推断。
2. Astro Content Collection 的 Zod schema 类型较复杂，不能直接把推断结果作为可移植声明。
3. Expressive Code 插件工厂的返回类型来自第三方包，需要公开、稳定的返回类型契约。
4. 本地图标文件由脚本生成，不能只手改生成产物；同时不能用宽泛的 `Record<string, LocalIcon>` 覆盖原类型，否则 `LocalIconName` 会从具体图标名联合退化为 `string`。

## 4. 修复方案与顺序

### 第一批：简单类型标注

- `DEFAULT_THEME` 标注为 `typeof AUTO_MODE`，保留 `"auto"` 字面量类型。
- `BANNER_HEIGHT_HOME` 标注为 `number`。
- `pathsEqual`、`url`、`applyThemeToDocument` 分别标注 `boolean`、`string`、`void`。

### 第二批：公开函数与第三方库边界

- RSS `GET` 标注为 `Promise<Response>`。
- 两个 Expressive Code 插件工厂使用包内导出的 `ExpressiveCodePlugin` 作为返回类型。
- `getSortedPosts` 标注为 `Promise<CollectionEntry<"posts">[]>`。

### 第三批：Content Collection 类型

- 提取 `postsSchema` 与 `specSchema`，保留原有 `z.object(...)` 定义及运行时值。
- 使用 `CollectionConfig<typeof postsSchema>` 和 `CollectionConfig<typeof specSchema>` 标注两个 collection。
- 给导出的 `collections` 增加 `Record<"posts" | "spec", CollectionConfig<BaseSchema>>` 类型边界，避免声明生成继续深入私有 schema 推断，同时不使用 `any`。

### 第四批：本地图标生成器

- 修改 `scripts/gen-local-icons.mjs`，从实际图标数据生成 `LocalIconKey` 字面量联合。
- 使用 `Readonly<Record<LocalIconKey, LocalIcon>>` 显式标注导出的 `localIcons`，再重新运行生成器更新 `src/constants/local-icons.ts`。
- 保留 `LocalIconName = keyof typeof localIcons`，使其仍是六个具体图标名的联合，而不是 `string`。

## 5. 验收标准

1. `npm run type-check` 退出码为 0，12 条诊断全部清零。
2. `npm run check`、`npm run lint`、`npm run build` 通过。
3. `python scripts/toc-check.py` 的 109 项断言通过，排除意外行为回归。
4. 连续运行两次图标生成器结果一致，且 `LocalIconName` 仍保留具体图标名联合类型。
5. diff 不包含业务逻辑变化、文件删除、新增 `@ts-ignore` / `@ts-expect-error` 或关闭 `isolatedDeclarations` 的配置变化。

## 6. 实际修改内容

| 文件 | 修改内容 | 对应诊断 |
| --- | --- | ---: |
| `src/constants/constants.ts` | 为 `DEFAULT_THEME`、`BANNER_HEIGHT_HOME` 增加显式类型 | 2 |
| `src/utils/url-utils.ts` | 为 `pathsEqual`、`url` 增加 `boolean`、`string` 返回类型 | 2 |
| `src/utils/setting-utils.ts` | 为 `applyThemeToDocument` 增加 `void` 返回类型 | 1 |
| `src/pages/rss.xml.ts` | 为 `GET` 增加 `Promise<Response>` 返回类型 | 1 |
| `src/plugins/expressive-code/custom-copy-button.ts` | 引入 `ExpressiveCodePlugin` 类型并标注插件工厂返回值 | 1 |
| `src/plugins/expressive-code/language-badge.ts` | 引入 `ExpressiveCodePlugin` 类型并标注插件工厂返回值 | 1 |
| `src/utils/content-utils.ts` | 为 `getSortedPosts` 标注 `Promise<CollectionEntry<"posts">[]>` | 1 |
| `src/content/config.ts` | 提取两个 schema，标注 collection，并为导出的 `collections` 建立可移植的 `CollectionConfig<BaseSchema>` 边界 | 2 |
| `scripts/gen-local-icons.mjs` | 生成 `LocalIconKey` 联合及 `localIcons` 显式类型，修复生成源头 | 1 |
| `src/constants/local-icons.ts` | 通过生成器写入上述类型，保留六个图标的精确键约束 | 随生成器完成 |

合计 12 条诊断均已处理。未修改常量值、schema 字段、RSS 生成过程、插件 hooks、URL 处理或主题行为；未删除文件，未新增 `@ts-ignore` / `@ts-expect-error`，未修改 `type-check` 脚本或关闭 `isolatedDeclarations`。

## 7. 验证结果

| 验证项 | 实测结果 |
| --- | --- |
| `npm run type-check` | 通过，退出码 0；TS9007 / TS9010 / TS9013 从 12 条降为 0 条 |
| `npm run check` | 通过；58 个文件，0 errors、0 warnings、1 个既有 hint（`language-badge.ts:10` 的 `_cssVar` 未使用） |
| `npm run lint` | 通过；Biome 检查 67 个文件，生成产物已格式化 |
| `npm run build` | 通过；10 个页面完成构建，Pagefind 索引 6 个页面、1754 个词 |
| `python scripts/toc-check.py` | 全部通过，109 项目录、布局、滚动、换页和移动端断言无回归 |
| 图标生成器幂等 | 连续两次生成后的 SHA-256 均为 `00ad48fee2d3f49d7c72ed7101cb47444b82e3a58d21ae11adc7c71f790079e1` |
| 图标键类型 | 通过 TypeScript Compiler API 展开确认，`LocalIconName` 仍由六个具体图标名字面量组成 |
| `git diff --check` | 通过，无空白错误 |

构建仍会输出两个与本次修改无关的非阻塞提示：`astro-icon` 未找到可选的 `src/icons` 目录，以及 Pagefind 不支持中文词干提取；两者均未导致构建失败。

最终 `npm run lint && npm run type-check && git diff --check` 已按顺序再次执行并通过。
