export interface Project {
  name: string;
  description: string;
  tags: string[];
  link?: string;
  demo?: string;
  year?: string;
  status?: string;
}

export const projects: Project[] = [
  {
    name: 'select-ask-ai',
    description:
      '跨平台「选词 → 询问 AI」工具：浏览器 Tampermonkey 脚本 + 桌面端 Python 客户端，把任意文本一键丢给大模型。',
    tags: ['Python', 'Tampermonkey', 'PyInstaller'],
    link: 'https://github.com/Henzhi/select-ask-ai',
    year: '2025',
    status: '维护中',
  },
  {
    name: 'LexAgent',
    description:
      '基于 LangGraph 的法律检索问答 Agent，流式输出 + 双路融合 + 自研 @tool，DeepSeek / Ollama 双后端可降级。',
    tags: ['LangGraph', 'RAG', 'Agent', 'PostgreSQL'],
    link: 'https://github.com/Henzhi/LexAgent',
    year: '2026',
    status: 'M3 进行中',
  },
  {
    name: 'gk-line-test',
    description:
      '公考行测刷题系统，SpringBoot 3.5 + Vue3 全栈，题库由多模态大模型从 PDF 解析提取。',
    tags: ['SpringBoot', 'Vue3', 'MySQL'],
    link: 'https://github.com/Henzhi/gk-line-test',
    year: '2026',
    status: '从零搭建',
  },
  {
    name: 'Law-RAG-Agent',
    description:
      '自治法律 RAG Agent：pgvector + BM25 + 重排混合检索，Tavily 联网发现，内部知识库优先于网页。',
    tags: ['RAG', 'pgvector', 'LangGraph'],
    link: 'https://github.com/Henzhi/Law-RAG-Agent',
    year: '2026',
    status: '重构中',
  },
];
