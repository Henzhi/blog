---
title: LexAgent 架构全链路：一个法律 RAG Agent 是怎么从零长出来的
published: 2026-10-05
description: 从分层设计、七节点编译图、工具层抽象，到双后端降级、预算熔断和容器化部署——把 LexAgent 的每一个架构决策摊开讲，包括被推翻的那些。
tags: [架构, LangGraph, RAG, Agent, 部署]
category: 教程笔记
draft: false
featured: true
---

写过几篇 LexAgent 的片段，但一直缺一篇**从上往下看**的东西：这套系统为什么长成现在这样，每一层解决什么问题，哪些决策后来被推翻了。

这篇就当是补上。

需要先说明一件事：这不是「跟着敲一遍就能跑」的入门教程，更像一份**架构演进记录**。里面有不少地方是"当时的结论后来被自己否掉了"，我认为这比只讲最终形态有价值——最终形态看起来总是很合理，但决策过程里的取舍才是真正能复用的东西。

---

## 一、先看全局：五层结构

LexAgent 是法律领域的 RAG 问答系统，代码约 1.9 万行 Python，分五层：

```
src/api/         FastAPI 路由、SSE 桥接、鉴权、会话存储
src/agents/      LangGraph 编排、节点、状态、审核子图
src/llm/         双后端（DeepSeek / Ollama）+ 降级 + 重试 + 预算回调
src/rag/         检索：意图识别、场景分类、混合检索、重排、法名推断
src/search/      Tavily 网络搜索、官方源（国家法律法规数据库）、法宝 MCP
src/knowledge/   爬虫、解析、切分、pgvector 入库
```

分层的依据是**变化频率**，不是功能分类。

- `src/knowledge/` 变化最慢——法律数据本身几年才更新一次；
- `src/rag/` 中等——检索策略调优会很频繁；
- `src/agents/` 最快——编排逻辑几乎每周都在动；
- `src/llm/` 特殊：**它被设计成可以被整体替换掉的一层**。

最后这条很关键。整个项目有一半的架构决策，都是在为"换模型不用动业务代码"这件事服务。

---

## 二、核心：三张编译图

LexAgent 的编排用的是 LangGraph。有意思的是它**不是一张图，而是三张**：

| 图 | 用途 | 入口 | 节点数 |
|---|---|---|---|
| `_build_graph` | 固定管线（兼容路径） | `intent` | 6 |
| `_build_react_graph` | 完整 ReAct 管线（`ask()` 同步用） | `intent` | 8 |
| `_build_react_loop_graph` | 纯 ReAct 循环子图（`stream()` 流式用） | `agent` | 2 |

固定管线图长这样：

```python
builder.add_node("intent", nodes["classify_intent"])
builder.add_node("memory_retrieve", nodes["memory_retrieve"])
builder.add_node("retrieve", nodes["retrieve"])
builder.add_node("generate", nodes["generate"])
builder.add_node("validate", self._validate_node)

builder.add_edge("memory_retrieve", "retrieve")
builder.add_edge("retrieve", "generate")   # 检索是固定动作
builder.add_edge("generate", "validate")
```

而 ReAct 图把中间的 `retrieve → generate` 换成了 `agent ⇄ tools` 循环：

```
intent → memory_retrieve → ┌─→ agent ─┐
                           │     ↓    │
                           │   tools ─┘
                           └─→ validate → END
```

差别在于：**检索从"固定动作"变成了"LLM 自主决定要不要调用的工具"**。模型可以自己选择先查内部库、还是先搜网络找线索、还是直接回答。

### 为什么流式路径要单独建一张子图

这是第一个值得展开的决策。

流式路径（`stream()`）理论上可以复用完整的 ReAct 图，但实际上它**单独建了一张只有 `agent` 和 `tools` 两个节点的子图**。原因有两个：

1. 流式路径在调图之前，已经完成了意图识别、FAQ 缓存检查和记忆检索，走完整图会重复执行，而且 FAQ 命中时还有提前 return 的分支；
2. 更关键的是——**状态合并**。

第二点踩过一个很深的坑，值得单独讲。

---

## 三、一个 400 错误引出的架构修正

早期版本手写 `while` 循环来步进 ReAct 节点，状态合并用 `dict.update()` 整体替换 messages：

```python
# 旧实现（已删除）
state.update(new_state)   # 整体替换，messages 直接覆盖
```

跑起来会偶发 DeepSeek 返回 400，然后自动降级到 Ollama。修的时候第一反应是"补一下合并逻辑"——手工复刻一遍 reducer 的行为。

但这是治标。**根因是：手写循环绕开了 LangGraph 的 `add_messages` reducer。**

LangGraph 的消息累积是靠 reducer 做的：`{"role": "assistant", "tool_calls": [...]}` 和后续的 `{"role": "tool", "tool_call_id": ...}` 之间有配对关系，整体替换 messages 会导致第 2 轮时丢失前一轮的 assistant 消息，模型收到的工具结果找不到对应的调用记录——400 就是这么来的。

最终解法是改成走编译图：

```python
self._react_loop_graph = self._build_react_loop_graph(react)

for chunk in graph.stream(state, stream_mode=["updates", "values"]):
    ...
```

让 reducer 和条件边各司其职，这个 Bug **从结构上不可能再复发**，而且代码还更短了。

> 教训：当你想给框架的行为打补丁时，先问一句"我是不是绕开了框架"。手工复刻 reducer 是典型的"用复杂度掩盖错误的分层"。

---

## 四、工具层：一个装饰器带来的收益

工具注册用的是一套自研的 `@tool` 装饰器：

```python
@tool(name="retrieve_knowledge", category=CATEGORY_KNOWLEDGE)
def build_retrieve_knowledge_spec(retriever, default_top_k=5) -> ToolSpec:
    ...
```

相比最初 `class + build_spec()` 的写法（约 40 行）缩到约 10 行。收益不只是行数——**schema 和实现同源**，改了函数签名 schema 自动跟着变，不会出现"文档说的和实际发出去的不一致"。

当前注册的工具：

| 工具 | 类别 | 作用 |
|---|---|---|
| `retrieve_knowledge` | 知识库 | 内部 pgvector 检索（最高优先级） |
| `web_search` | 网络 | Tavily 搜索，只作线索 |
| `legal_source_search` | 官方源 | 国家法律法规数据库 |
| `pkulaw_search` / `pkulaw_verify` | 官方源 | 北大法宝检索 / 条文回源核验 |

这里有个**被推翻的决策**很有意思。最初的决定是"不用 LangChain 的 `@tool`"，理由是它产出的 Tool 对象只有 `BaseChatModel.bind_tools` 能消费，会倒逼重写整个 LLM 层。

后来这个理由消失了——因为 LLM 层本身迁移到了 LangChain 生态。于是装饰器语法保留不变，但内部改为委托 LangChain 推导 schema。

**同一个结论，前提变了结论就变了。** 决策记录里如果把"为什么"写清楚，推翻的时候才知道该推翻哪一条。

不过迁移后有 4 个行为差异需要实测确认，其中一个是隐形的坑：

- `str | None` → `anyOf [string, null]`（语义等价，更规范）
- schema 会带上 `default`（对 LLM 是有益引导）
- dataclass 类型展开为对象 schema
- ⚠️ **枚举必须用 `Literal` 表达**——自定义的 `Param` 类 LangChain 不认识，会**静默丢弃** description 和 enum，不报错，只是发给模型的 schema 少了引导信息

最后一条如果没有测试守着，基本发现不了：编译通过、测试通过、线上只是"模型偶尔选错参数"。

---

## 五、双后端与降级：横切语义必须在正确的层

LLM 层是 `LLMBackend` 抽象，主后端 DeepSeek（OpenAI 兼容），备用 Ollama。

```python
class FailoverLLMBackend(LLMBackend):
    @property
    def active_backend(self) -> str: ...
    @property
    def degraded(self) -> bool: ...
```

降级规则经过两次修正：

| 异常类型 | 处理 | 原因 |
|---|---|---|
| 4xx（认证/权限） | 降级到 Ollama | 重试无意义 |
| 429 / 5xx / 超时 | 走 retry，不降级 | 暂时性故障 |
| 重试耗尽 | **降级** | 补强：说明主后端在当前窗口确实不可用 |

最后一行是后补的。原实现里重试耗尽抛的是裸 `RuntimeError`，没有状态码，被判定为"非 4xx"于是不降级——**Ollama 兜底在最需要的时候用不上**。修法是引入哨兵异常携带最后的状态码。

### 降级要能回切，但探测不能白花钱

降级如果是单向的，一次瞬时 401 就只能重启服务。

所以加了冷却窗口：降级后进入 300 秒冷却，冷却结束后**下一次真实请求兼作健康探测**——成功就回切，失败就继续降级并刷新冷却。

为什么不单独发 ping 探测？因为那要付真实 Token 和一次 RTT。复用下一次真实请求是零成本的，而且探测失败时请求仍由备用端应答，用户完全无感。

### 最贵的一课：绕过公开入口

这里有个我认为整个项目最有价值的教训。

LLM 层迁移到 LangChain 后，`agent_node` 的写法变成了：

```python
# 迁移时的写法（错误）
response = self.chat_model.bind_tools(tools).invoke(messages)
```

看起来是"标准写法"，测试也全绿。但实际上**重试和降级两层语义同时静默失效了**：

- 重试逻辑（`is_retryable` + `wait_and_log`）实现于 `chat_with_tools` 入口链路
- `FailoverLLMBackend` 的 4xx 运行期降级也实现于同一入口

绕过入口意味着：一次网络抖动整轮就失败、主后端 4xx 不再切 Ollama。而测试之所以通过，是因为假 LLM（FakeToolLLM）的两条路径行为等价，掩盖了差异。

修复后后端内部仍然是 `bind_tools + invoke`（迁移成果不变），只是必须经过 `chat_with_tools()` 公开入口。

> 这一课值得单独记下来：**"标准写法"不能替代项目自建的横切语义层。** 迁移框架时，凡是绕过公开入口的写法，都要逐项核对该入口承载的横切职责——本例中重试、降级、预算三件事里，只有预算挂在 ChatModel 上幸存了。

---

## 六、预算熔断：按次数，不按 token

F14 预算熔断解决的问题是：一次误调用可能烧掉一天额度。日上限默认 50 元，超限自动暂停。

### 口径选择

| 方案 | 否决原因 |
|---|---|
| 按 token 计数 | **流式响应拿不到 `usage`**，只能按字符估算，误差不可控 |
| **按逻辑调用次数**（采用） | 跨后端一致，不受重试影响，且 Tavily 本就按次计费 |

实测一次复杂查询约 **18~20 次 LLM 调用**，据此默认阈值设为 5000 次（约 250 次查询/天）。

### 两级熔断

不是所有东西超限都该整体停：

- **LLM 超限 → 整体熔断**（API 前置拦截）。LLM 是生成回答的必需品，超限后跑下去只会白烧钱；
- **Tavily 超限 → 局部降级**（工具返回 `ok=False`「搜索额度已用尽」）。搜索只是线索来源，内部库和官方源仍可作答，回答照常生成。

### 一个容易忽略的并发问题

最初的实现是"只读 check + 事后 record"，两次 Redis 往返之间存在 TOCTOU 窗口——**并发 N 个流会把日限额放大到 limit + N - 1**。

改成原子预占：`reserve()` / `release()` / `check_and_reserve()`，Redis 走 Lua 脚本（INCRBY → 比较 → 超限回滚），失败归还。

关键的是把拦截点**移到花钱之前**。事后 record 时才发现超限，钱已经花出去了——抛异常会截断生成中的回答，不抛就默默突破限额，两头都不对。

还有个细节：Lua 失败时退化到**非原子 Redis 路径**，而不是进程内计数。因为 reserve 写内存、used() 读 Redis 会让两边不一致，反而让熔断彻底失效。**宁失并发安全，不失存储一致性。**

---

## 七、检索：为什么不只靠向量

法律文本有个特点：「合同解除」和「解除合同」语义接近但对应不同法条，纯向量检索会混淆。所以走双路：

- **稠密**：pgvector + bge-m3（1024 维 HalfVec）
- **稀疏**：BM25
- 融合后交 reranker 重排

融合阶段做过一次修正。网络结果的权重是 0.5 × tavily_score，天然低于内部库（≥0.5）和官方源（0.85）。**纯按分截断时，top_k 一满网络结果一条都不剩**——Tavily 的钱花了，用户完全看不到，验证状态形同虚设。

解法是给网络线索**保底配额**（`FUSION_WEB_MIN_SLOTS=2`）：先占 min(配额, 网络条数, top_k) 个位置，其余给权威来源，最终仍按分排序保证权威在前。

为什么不是提高网络权重？因为那会违背"内部库优先"原则，让未验证内容挤掉权威内容。**配额只保底、不抢位**，而且可以用 `=0` 一键退回纯按分。

评测用两个固定集合：`multi100`（100 条多跳查询）和 `colloq148`（148 条口语化查询，模拟真实用户提问）。

---

## 八、部署：2C2G 上跑起来

部署形态是 Docker Compose，三个服务：

```yaml
db:     pgvector/pgvector:pg17
redis:  redis/redis-stack-server
app:    LexAgent 本体
```

两个安全细节值得说：

1. **数据库密码必填化**：`${POSTGRES_PASSWORD:?required}` 无默认值，未设置直接拒绝启动。原实现是明文写死在 compose 里的弱口令；
2. **移除 5432 宿主映射**：db 只在 compose 网络内被 app 访问。弱口令 + 端口暴露 = 局域网内可直连无防护 PG。

如果用 2C2G 的轻量服务器部署，还需要：配 2G swap、Ollama 只跑量化版 bge-m3、docker-compose 做资源限制。**Ollama 是内存大户**，2G 机器上不限制会直接把系统拖死。

启动顺序：配置 `.env` → 起 db/redis → 导入法律数据 → 起 app。

```bash
# .env 必填项
POSTGRES_PASSWORD=<强随机口令>
OPENAI_API_KEY=<DeepSeek API Key>
OPENAI_MODEL=deepseek-v4-flash    # deepseek-chat 已于 2026-07 弃用
AGENT_ENABLED=true
```

最后一行值得注意：**`deepseek-chat` 已经弃用**，继续用这个模型名请求会失败。文档和代码里的默认值如果还写着旧名字，就会出现"照着文档配，一上线就挂"。

---

## 九、值得记住的几条

写到这里，把反复出现的模式收一下：

**1. 横切语义要有唯一入口。** 重试、降级、预算都挂在 `chat_with_tools()` 上。绕过它 = 三件事一起失效，而且测试可能还是绿的。

**2. 从结构上消除 Bug，而不是打补丁。** 手写循环丢消息 → 不是补合并逻辑，是改用编译图让 reducer 接管。

**3. 决策要记录"为什么"，因为前提会变。** "不用 LangChain @tool"当时成立，LLM 层迁移后前提消失，结论就该重新评估。

**4. 工具失败不抛出。** 工具执行统一返回 `ToolResult(ok=False)`，让 LLM 知道"这个来源不可用"，而不是中断整轮。同一个原则贯穿了搜索失败、官方源失败、预算超限三处。

**5. 监控组件故障不应该拖垮主链路。** Redis 不可用时预算计数退化到进程内、健康检查取值一律 fail-open——信息缺失远好于 503。

---

目前在做的方向是 **M4 多 Agent 演进**：把重流程场景（类案报告、文书生成、合同审查）拆成独立子图，主 Agent 保持现有循环不动。原则是"**按场景拆出口，不按工具拆内脏**"——检索、搜索、核验继续当工具用，因为跨源迭代验证本身就是主 Agent 的核心智能，拆成子 Agent 等于在编排层把同一个循环重建一遍，还白付每跳的路由成本。

做完会再写一篇。
