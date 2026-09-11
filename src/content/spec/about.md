# 关于我

我是 **Henzhi**，北京化工大学计算机科学与技术专业 2027 届，坐标北京。

做的事可以概括成一句话：**把大模型的能力落到真正能跑起来的工程里**。跑通一个 demo 不算完，检索准不准、编排稳不稳、成本控不控得住、出问题能不能定位，这些才是分水岭。

## 正在推进的项目

- **LexAgent** — 基于 LangGraph 的法律检索问答 Agent。流式输出 + 双路检索融合 + 自研工具协议，后端 DeepSeek / Ollama 可降级。
- **Law-RAG-Agent** — 自治法律 RAG Agent，混合检索（pgvector + BM25 + reranker），内部知识库优先级严格高于网页搜索。
- **select-ask-ai** — 跨平台「选中即问」工具：浏览器 Tampermonkey 脚本 + Python 桌面客户端，覆盖 PDF / Word / WPS 等场景。
- **gk-line-test** — 公考行测刷题系统，SpringBoot 3.5 + Vue3 全栈，题库由多模态大模型从 PDF 解析。

## 技术栈

- **语言**：Python、TypeScript / JavaScript、Java、SQL
- **AI 工程**：LangGraph、RAG、pgvector、BM25、reranker、Prompt 设计、Agent 编排
- **后端 / 前端**：FastAPI、Spring Boot、Redis、PostgreSQL、Vue、Astro
- **工程化**：Docker、CI、测试与 lint 门禁、成本熔断

## 工作方式上的偏好

- 架构上倾向**根因治理**，而不是给症状打补丁
- 测试和 lint 必须进 CI，作为合并前的硬性门禁
- 愿意用一点响应延迟换回答准确性

## 联系

- GitHub：[github.com/Henzhi](https://github.com/Henzhi)

> 这个站点用 [Astro](https://astro.build) 搭配 [Fuwari](https://github.com/saicaca/fuwari) 主题搭建，跑在一台腾讯云轻量服务器上。
