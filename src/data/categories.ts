// 全站内容分类：三个固定方向。
//
// 这里是分类名的唯一来源——content collection 的 schema（src/content/config.ts）
// 用它做写入校验，/categories/ 页面用它渲染，侧栏的顺序也以它为准。
// 想加分类只改这个文件，别在文章的 frontmatter 里自己造词。
export const CATEGORY_NAMES = ["生活记录", "学习笔记", "教程笔记"] as const;

export type CategoryName = (typeof CATEGORY_NAMES)[number];

export interface CategoryDef {
	name: CategoryName;
	/** 一句话说明这个分类收什么，出现在分类索引页 */
	tagline: string;
}

export const categoryDefs: CategoryDef[] = [
	{
		name: "生活记录",
		tagline: "日常、杂记、偶尔想到的东西。不一定有用，但确实发生过。",
	},
	{
		name: "学习笔记",
		tagline: "学过什么、当时怎么理解的、后来发现哪里想错了。为自己存一份档。",
	},
	{
		name: "教程笔记",
		tagline: "能照着做出来的东西：环境怎么配、命令怎么敲、坑在哪一步。",
	},
];

export function isCategoryName(value: string): value is CategoryName {
	return (CATEGORY_NAMES as readonly string[]).includes(value);
}
