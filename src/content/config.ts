import { defineCollection, z } from "astro:content";
import type { BaseSchema, CollectionConfig } from "astro/content/config";
import { CATEGORY_NAMES, isCategoryName } from "../data/categories";

const postsSchema = z.object({
	title: z.string(),
	published: z.date(),
	updated: z.date().optional(),
	draft: z.boolean().optional().default(false),
	description: z.string().optional().default(""),
	image: z.string().optional().default(""),
	tags: z.array(z.string()).optional().default([]),
	// 分类只允许取 src/data/categories.ts 里的三个方向（留空 = 未分类）。
	// 写错不会悄悄生成一个游离分类，而是构建时直接报错。
	category: z
		.string()
		.refine((v) => v.trim() === "" || isCategoryName(v.trim()), {
			message: `category 只能是：${CATEGORY_NAMES.join(" / ")}（留空表示未分类）`,
		})
		.optional()
		.nullable()
		.default(""),
	lang: z.string().optional().default(""),
	// 首页精选标记：true 的文章优先展示在首页「最新文章」之前
	featured: z.boolean().optional().default(false),

	/* For internal use */
	prevTitle: z.string().default(""),
	prevSlug: z.string().default(""),
	nextTitle: z.string().default(""),
	nextSlug: z.string().default(""),
});

const postsCollection: CollectionConfig<typeof postsSchema> = defineCollection({
	schema: postsSchema,
});
const specSchema = z.object({});
const specCollection: CollectionConfig<typeof specSchema> = defineCollection({
	schema: specSchema,
});
export const collections: Record<
	"posts" | "spec",
	CollectionConfig<BaseSchema>
> = {
	posts: postsCollection,
	spec: specCollection,
};
