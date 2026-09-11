---
title: 用 LangGraph 搭法律 RAG Agent：为什么我放弃了 LangChain 的工具绑定
published: 2026-08-22
description: 记录 LexAgent 从手写 ReAct 循环到编译图流式的演进，以及自研 @tool 装饰器替代 bind_tools 的取舍。
tags: [LangGraph, RAG, Agent, Python]
category: AI 工程
draft: false
---

法律问答这个场景有几个硬约束：答案必须能追溯到具体法条、检索不能靠"语义相似就行"、成本要可控。这三条叠在一起，意味着不能简单套一个「LLM + 向量库」的 demo 就交差。

LexAgent 做的事情，就是把这些约束变成工程上可验证的东西。

## 从手写 ReAct 循环到编译图

第一版是手写的 ReAct 循环：LLM 输出 → 解析工具调用 → 执行 → 回灌，直到拿到最终答案。能跑，但很快就撞上两个问题：

1. **中断恢复困难** — 用户中途打断、或者某一步超时，整个状态就丢了；
2. **流式输出要自己拼装** — 和工具调用交错时容易乱序，前端渲染经常跳字。

换成 LangGraph 的编译图之后，这两件事变成了图的固有能力：

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("intent", classify_intent)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("validate", validate_answer)

graph.add_conditional_edges("intent", route_by_intent, {
    "legal_qa": "retrieve",
    "chitchat": "generate",
})
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "validate")
graph.add_conditional_edges("validate", should_retry, {
    "retry": "retrieve",
    "done": END,
})

app = graph.compile(checkpointer=checkpointer)
```

配了 checkpointer 之后，中断恢复几乎是免费的：每个节点的状态都被持久化，重连后能从断点继续。这比我手写快照逻辑要可靠得多。

## 决策 D1：放弃 LangChain 的 @tool / bind_tools

这是项目里最早落定的决策。原因很直接：

- `bind_tools` 把工具 schema **强绑定在模型客户端上**，换后端（DeepSeek ↔ Ollama）时要连带改工具定义；
- 工具调用结果的解析逻辑被藏在框架里，出错时不好定位；
- 我们本来就要做降级：DeepSeek 不可用时切 Ollama，而两套后端的工具调用格式并不完全一致。

于是自研了一套 `ToolSpec` + `OpenAICompatibleBackend`：

```python
@tool(name="search_law", description="按关键词检索内部法律知识库")
async def search_law(query: str, top_k: int = 5) -> list[LawChunk]:
    ...
```

装饰器负责生成 JSON Schema、校验入参；后端只管把 schema 塞进请求、把模型返回的调用参数丢回来。模型和工具之间解耦了，换后端只改一层。

代价是要自己处理参数校验和错误提示，多写了大概两百行。但换来「换模型不用动业务代码」，我认为值。

## 检索：为什么要双路融合

纯向量检索在法律文本上表现并不好——「合同解除」和「解除合同」语义接近但对应的法条不同，字面匹配反而更准。所以走的是双路：

- **稠密**：pgvector + bge-m3（1024 维 HalfVec）
- **稀疏**：BM25

两路召回后做融合，再交给 reranker 重排。

这里踩过一个坑：换嵌入模型要**全量重建索引**。评测阶段换过一次，整个库重跑了一遍。后来把维度写死在迁移脚本里，避免误改。

评测用两个固定集合：

- `multi100`：100 条多跳查询
- `colloq148`：148 条口语化查询，模拟真实用户的提问方式

## 还没解决的

- **预算熔断**（F14）还在做：日 / 周阈值触达后自动暂停，避免一次误调用烧掉一天额度；
- **场景分类**（F11）和**人工确认**（F12）被上游一个设计问题阻塞，暂时搁置。

这两块做完后会再写一篇。
