// 项目数据：首页精选与作品集页共用，状态决定左侧色条颜色
export type ProjectTone = "active" | "maintained" | "refactor";

export interface Project {
	name: string;
	status: string;
	tone: ProjectTone;
	year: string;
	desc: string;
	stack: string[];
	repo: string;
}

export const projects: Project[] = [
	{
		name: "LexAgent",
		status: "M3 进行中",
		tone: "active",
		year: "2026",
		desc: "基于 LangGraph 的法律检索问答 Agent：流式输出 + 双路检索融合 + 自研工具协议，DeepSeek / Ollama 双后端可降级。",
		stack: ["LangGraph", "RAG", "Agent", "PostgreSQL"],
		repo: "https://github.com/Henzhi/LexAgent",
	},
	{
		name: "Law-RAG-Agent",
		status: "重构中",
		tone: "refactor",
		year: "2026",
		desc: "自治法律 RAG Agent：pgvector + BM25 + reranker 混合检索，内部知识库优先于网页搜索，带日/周预算熔断。",
		stack: ["RAG", "pgvector", "LangGraph", "Tavily"],
		repo: "https://github.com/Henzhi/Law-RAG-Agent",
	},
	{
		name: "select-ask-ai",
		status: "维护中",
		tone: "maintained",
		year: "2025",
		desc: "跨平台「选中即问」工具：浏览器 Tampermonkey 脚本 + Python 桌面客户端，覆盖 PDF / Word / Markdown / WPS 场景。",
		stack: ["Python", "Tampermonkey", "PyInstaller"],
		repo: "https://github.com/Henzhi/select-ask-ai",
	},
	{
		name: "gk-line-test",
		status: "从零搭建",
		tone: "active",
		year: "2026",
		desc: "公考行测刷题系统：SpringBoot 3.5 + Vue3 全栈，题库由多模态大模型从 PDF 解析提取。",
		stack: ["SpringBoot", "Vue3", "MySQL"],
		repo: "https://github.com/Henzhi/gk-line-test",
	},
];

// 状态色条：进行中=accent，维护中=绿，重构中=琥珀
export const toneColor: Record<ProjectTone, string> = {
	active: "oklch(0.72 0.15 250)",
	maintained: "oklch(0.72 0.14 155)",
	refactor: "oklch(0.75 0.13 75)",
};
