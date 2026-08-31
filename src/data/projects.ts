export interface Project {
  name: string;
  description: string;
  link?: string;
  tags: string[];
}

export const projects: Project[] = [
  {
    name: 'select-ask-ai',
    description: '跨平台选词询问 AI 工具，覆盖浏览器与桌面文档场景。',
    link: 'https://github.com/Henzhi/select-ask-ai',
    tags: ['Python', 'Tampermonkey', 'AI'],
  },
  {
    name: 'LexAgent',
    description: '基于 LangGraph 的法律检索问答 Agent，支持流式与多路融合。',
    link: 'https://github.com/Henzhi/LexAgent',
    tags: ['LangGraph', 'RAG', 'Agent'],
  },
  {
    name: 'gk-line-test',
    description: '公考行测刷题系统，SpringBoot + Vue3 全栈。',
    link: 'https://github.com/Henzhi/gk-line-test',
    tags: ['SpringBoot', 'Vue3', 'MySQL'],
  },
];
