# LexAgent 架构教程系列

面向**关注架构设计**的读者,把 LexAgent(法律 RAG 自主 Agent 问答系统)的设计决策
摊开讲。重点不在"最终形态长什么样",而在**取舍过程**,包括那些被自己推翻的决策。

## 写作原则

1. **不写最终形态展示,写决策演进**。最终形态看起来总是合理,但"为什么否掉了备选方案"
   才是能复用的东西。
2. **代码引用必须核对实际代码**,不抄文档。这个项目的文档普遍滞后于代码
   (旧文的 4 节点图 vs 实际的 3 张图 6 个工具就是实例)。
3. **数字要带口径**。"约 1.9 万行"、"18~20 次 LLM 调用/查询" 这类,说清来源和配置。
4. **踩坑必留**。静默失效、假阳性测试这类"看起来没问题其实错了"的坑,价值最高。

## 素材来源

主仓库:`C:/Code/py_code/PythonProject/LexAgent`(**不在 `C:/Code/VibeCoding/` 下**)

按信息密度排序的素材:

| 文件 | 用途 |
|---|---|
| `DECISIONS.md` | **最值钱**。完整决策链,含被推翻项与否决理由 |
| `src/agents/graph.py` | 图结构唯一真相源(三张编译图) |
| `docs/M1-架构设计.md` | 分层设计、节点边、数据结构、SSE 契约 |
| `docs/M4-多Agent路线图.md` | 多 Agent 演进原则与阶段划分 |
| `src/agents/tools/base.py` | 工具层抽象(@tool 装饰器) |
| `docs/代码审查报告-2026-09-01.md` | 问题清单与整改,踩坑富矿 |

**排除项**:`docs/面试问答-*.md`、`docs/resume-*.tex`、`docs/简历-*.md` 三个文件
已被 `.gitignore` 排除、git 未跟踪,**读者在公开仓库里看不到**,引用等于死链。
(核实命令:`git check-ignore -v` + `git ls-files`)

## 章节状态

### 01 架构全链路 ✅ 已发布

- **底稿**:`01-architecture-overview.md`
- **成品**:`src/content/posts/lexagent-architecture-tutorial.md`(平铺层)
- **URL**:https://henzhi.github.io/blog/posts/lexagent-architecture-tutorial/
- ⚠️ 这篇在平铺层是**历史原因**——发布时还没有子目录约定。它后续发布的文章
  一律走 `src/content/posts/lexagent/`,URL 会带一层 `lexagent/`。
- 五层结构 → 三张编译图 → 工具层 → 双后端降级 → 预算熔断 → 检索 → 部署 → 收口
- 含 5 个真实教训:reducer 被绕过致 400、公开入口被绕过致重试与降级静默失效、
  预算 TOCTOU、纯按分截断致网络线索被挤空、`Param` 类被 LangChain 静默丢弃

### 02 检索层深挖 ⬜ 待写

- **成品路径**:`src/content/posts/lexagent/02-retrieval.md`(子目录首篇)
- **URL 预告**:`/blog/posts/lexagent/02-retrieval/`

候选内容(需先核代码再定稿):

- 双路融合:为什么稠密 + 稀疏,reranker 放在哪一步
- **法名推断**:口语化查询("试用期被辞退有赔偿吗")怎么映射到法条。
  `docs/检索评测与优化报告` 提到无法名的口语查询命中率是个已知短板
- 融合截断的保底配额(`FUSION_WEB_MIN_SLOTS`)——权重设计导致网络结果被挤空
- 评测集:`multi100`(100 条多跳)与 `colloq148`(148 条口语化)怎么构造、怎么用
- 知识库版本治理:新旧版本共存导致召回已废止条文,`documents.status` 标记处置

### 03 流式与断线重连 ⬜ 待写

- **成品路径**:`src/content/posts/lexagent/03-streaming.md`

- SSE 事件契约(thinking / token / meta / tool_call / tool_result)
- **断线重连**:Redis 事件日志 + seq 游标重放,为什么不接 checkpointer
- 易混淆的一对概念:「等人确认」(interrupt)与「网络断了接着看」(resume)是正交的
- 孤儿流宽限回收:用户关掉标签页后,怎么避免白烧 Token
- 前端侧:路由/会话切换不 abort、刷新后自动续流

### 04 多 Agent 演进(生长式迁移) ⬜ 待写

- **成品路径**:`src/content/posts/lexagent/04-multi-agent.md`

- 原则一:**按场景拆出口,不按工具拆内脏**——为什么检索不该拆成子 Agent
- 原则二:生长式迁移,主 Agent 自有循环不重写
- Agent 判定三问(自主多步 / 独立确认契约 / 独立输出契约)
- 审核子图:三层审核(L1 规则守卫 / L2 LLM 审核 / L3 定向回源核验)
- 成本约束:为什么 A 类路径必须保持零编排

## 待澄清事项

- 旧文 `lexagent-langgraph.md` 的架构描述已过时(4 节点图 vs 实际 3 张图),
  决定:**合并后删除**(待执行)。合并时保留其独有内容:
  "为什么放弃 LangChain 工具绑定"的早期论证、"为什么需要双路融合"的说明。
