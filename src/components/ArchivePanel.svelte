<script lang="ts">
import { onMount } from "svelte";

import { getPostUrlBySlug } from "../utils/url-utils";

// 这两个值实际由组件自己从 URL 查询参数解析（见下方 params），给默认值让它们成为可选 props，
// 否则 archive.astro 只传 sortedPosts 会触发 ts(2322)。
export let tags: string[] = [];
export let categories: string[] = [];
export let sortedPosts: Post[] = [];

const params = new URLSearchParams(window.location.search);
tags = params.has("tag") ? params.getAll("tag") : [];
categories = params.has("category") ? params.getAll("category") : [];
const uncategorized = params.get("uncategorized");

interface Post {
	slug: string;
	data: {
		title: string;
		tags: string[];
		category?: string | null;
		published: Date;
	};
}

let filteredPosts: Post[] = sortedPosts;

$: activeFilters = [
	...tags.map((t) => `#${t}`),
	...categories,
	...(uncategorized ? ["未分类"] : []),
];

function formatYearMonth(date: Date) {
	const year = date.getFullYear();
	const month = (date.getMonth() + 1).toString().padStart(2, "0");
	return `${year} · ${month}`;
}

onMount(async () => {
	let result: Post[] = sortedPosts;

	if (tags.length > 0) {
		result = result.filter(
			(post) =>
				Array.isArray(post.data.tags) &&
				post.data.tags.some((tag) => tags.includes(tag)),
		);
	}

	if (categories.length > 0) {
		result = result.filter(
			(post) => post.data.category && categories.includes(post.data.category),
		);
	}

	if (uncategorized) {
		result = result.filter((post) => !post.data.category);
	}

	filteredPosts = result;
});
</script>

<!-- stephango 式年份密排：等宽「年 · 月」前缀 + 标题，一行一条 -->
<div>
    {#if activeFilters.length > 0}
        <div class="mb-6 flex flex-wrap items-center gap-2 text-[0.8125rem] text-50">
            <span>筛选：</span>
            {#each activeFilters as filter}
                <span class="inline-flex items-center h-6 px-2 rounded-md border border-[var(--border-subtle)] text-75">{filter}</span>
            {/each}
            <a href="./" class="ml-1 transition-colors hover:text-[var(--primary)]">清除 ×</a>
        </div>
    {/if}

    {#each filteredPosts as post (post.slug)}
        <a
                href={getPostUrlBySlug(post.slug)}
                aria-label={post.data.title}
                class="group flex items-baseline gap-4 py-2.5 -mx-2 px-2 rounded-lg transition-colors hover:bg-[var(--btn-plain-bg-hover)]"
                style="border-bottom: 0.5px solid var(--border-subtle)"
        >
            <span class="shrink-0 w-[5.5rem] font-mono text-[0.8125rem] tabular-nums text-30">
                {formatYearMonth(post.data.published)}
            </span>
            <span class="min-w-0 truncate text-[0.9375rem] text-black/90 dark:text-white/90 transition-colors group-hover:text-[var(--primary)]">
                {post.data.title}
            </span>
            <span class="ml-auto hidden md:block shrink-0 max-w-[12rem] truncate text-[0.8125rem] text-30">
                {post.data.tags.map((t) => t.trim()).join(" · ")}
            </span>
        </a>
    {/each}

    {#if filteredPosts.length === 0}
        <div class="py-12 text-center text-[0.9375rem] text-30">该筛选条件下暂无文章</div>
    {/if}
</div>
