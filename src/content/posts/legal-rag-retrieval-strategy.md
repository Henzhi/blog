---
title: 法律 RAG 的检索优先级：为什么网页搜索只能做「发现」
published: 2026-08-26
description: 内部知识库 > 官方库校验 > 网页搜索仅作发现——一套把引用准确率放在首位的检索策略，以及日/周预算熔断设计。
tags: [RAG, 检索, 法律, 架构]
category: AI 工程
draft: false
---

做法律 RAG 最容易犯的错，是把「联网搜索」当成增强手段直接接进去。看起来答案更全了，实际上引入了最危险的东西：**来源不可控**。

一个法律问答系统，回答里出现一条不存在的法条，比回答"我不知道"要糟糕得多。

## 三级优先级

所以检索策略被定死成一个明确的层级：

```
1. 内部知识库（pgvector + BM25 混合检索）  ← 最高优先级
2. 官方数据库校验                          ← 引用前的强制关口
3. 网页搜索（Tavily）                      ← 仅用于「发现」，不直接作为答案来源
```

关键在于第 2 步：**任何要写进回答的法条引用，必须先过官方库校验**。网页搜索召回的内容只能用来"提示我可能有哪些相关法规"，真正的条文内容必须回到权威来源确认。

这条规则牺牲了响应速度，但换来了引用可信度。在这个场景里，我认为这个交换是必须的。

## 混合检索的具体配置

| 组件 | 选型 | 说明 |
| --- | --- | --- |
| 稠密检索 | pgvector + bge-m3 | 1024 维，HalfVec 存储 |
| 稀疏检索 | BM25 | 处理法条名称、专有术语的精确匹配 |
| 重排 | bge-reranker | 两路召回融合后统一重排 |
| 网页搜索 | Tavily | 仅作发现，不进答案 |
| 编排 | LangGraph 1.2 | intent → retrieve → generate → validate |

## 预算熔断：自治 Agent 的必需品

Agent 一旦自治，就有了「自己决定调多少次 API」的能力。这在成本上是不可控的——一个死循环的重试就能烧掉一天额度。

所以熔断是设计的一部分，不是事后补丁：

```python
class BudgetCircuitBreaker:
    def __init__(self, daily_limit: float, weekly_limit: float):
        self.daily_limit = daily_limit
        self.weekly_limit = weekly_limit

    def check(self) -> None:
        if self.spent_today() >= self.daily_limit:
            raise BudgetExceeded("daily budget exhausted")
        if self.spent_this_week() >= self.weekly_limit:
            raise BudgetExceeded("weekly budget exhausted")
```

阈值触达后直接暂停，而不是降级继续跑——因为降级继续跑，用户拿到的是一条没经过完整校验的回答，这比没有回答更危险。

## 部署上的现实约束

目标机器是 2 核 2G 的轻量服务器，这个配置跑完整检索栈是吃紧的：

- 必须配 swap（2G）；
- Ollama 只跑量化后的 bge-m3；
- PostgreSQL / Redis / 应用容器要在 compose 里做内存限制。

如果内存压力还是大，更现实的做法是把嵌入服务拆到另一台机器，或者直接用云端嵌入 API。这个权衡我还在做。
