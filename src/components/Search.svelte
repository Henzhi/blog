<script lang="ts">
import { localIcons } from "@constants/local-icons";
import I18nKey from "@i18n/i18nKey";
import { i18n } from "@i18n/translation";
import Icon from "@iconify/svelte";
import { url } from "@utils/url-utils.ts";
import { onMount } from "svelte";
import type { SearchResult } from "@/global";

let keywordDesktop = "";
let keywordMobile = "";
let result: SearchResult[] = [];
let isSearching = false;
let pagefindLoaded = false;
let initialized = false;
/** 上一次真正提交的查询词，用来区分「还没搜」与「搜了没结果」 */
let lastKeyword = "";
/** 键盘导航当前项，-1 表示未选中 */
let activeIndex = -1;
/** Pagefind 未就绪时挂起的查询，就绪后重放 */
let pendingQuery: { keyword: string; isDesktop: boolean } | undefined;
/** Pagefind 加载失败（脚本 404 / 被缓存拦下），用来给出区别于「没搜到」的提示 */
let searchFailed = false;

/** 输入防抖：连续输入只在停顿后查一次，避免每次击键都打一遍 Pagefind */
const DEBOUNCE_MS = 180;
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

const fakeResult: SearchResult[] = [
	{
		url: url("/"),
		meta: {
			title: "This Is a Fake Search Result",
		},
		excerpt:
			"Because the search cannot work in the <mark>dev</mark> environment.",
	},
	{
		url: url("/"),
		meta: {
			title: "If You Want to Test the Search",
		},
		excerpt: "Try running <mark>npm build && npm preview</mark> instead.",
	},
];

const panelEl = () => document.getElementById("search-panel");

const isPanelOpen = (): boolean =>
	!panelEl()?.classList.contains("float-panel-closed");

const setPanelVisibility = (show: boolean): void => {
	panelEl()?.classList.toggle("float-panel-closed", !show);
};

/**
 * 面板开合由 class 驱动（Layout 里「点击外部关闭」也改这个 class），
 * 所以 aria-expanded 必须跟着 class 走，否则读屏拿到的状态会和界面不一致。
 */
function syncPanelAria(): void {
	const open = isPanelOpen();
	// 只同步真正的可展开控件：移动端的开关按钮 + 两个搜索输入框
	for (const id of ["search-switch", "search-input", "search-input-mobile"]) {
		document.getElementById(id)?.setAttribute("aria-expanded", String(open));
	}
}

/** 催一下 Pagefind 加载 —— 加载逻辑在 Navbar 的脚本里（Serch 组件先于它可用也无妨） */
function requestPagefindLoad(): void {
	(window as unknown as { __startPagefind?: () => void }).__startPagefind?.();
}

/** 桌面搜索框（lg 以上可见）与面板内搜索框，聚焦要选当前可见的那个 */
function focusSearchInput(): void {
	const isDesktop = window.matchMedia("(min-width: 1024px)").matches;
	document
		.querySelector<HTMLInputElement>(
			isDesktop ? "#search-bar input" : "#search-bar-inside input",
		)
		?.focus();
}

function openSearch(): void {
	setPanelVisibility(true);
	focusSearchInput();
}

function closeSearch(): void {
	setPanelVisibility(false);
	activeIndex = -1;
	if (document.activeElement instanceof HTMLInputElement) {
		document.activeElement.blur();
	}
}

const search = async (keyword: string, isDesktop: boolean): Promise<void> => {
	const trimmed = keyword.trim();
	if (!trimmed) {
		lastKeyword = "";
		result = [];
		activeIndex = -1;
		setPanelVisibility(false);
		return;
	}

	if (!initialized) {
		// Pagefind 现在是延后加载的，可能还没就绪。挂起这次查询、
		// 顺手催一下加载，等 pagefindready 后重放 ——
		// 直接返回空结果会让用户误以为「没搜到」。
		pendingQuery = { keyword: trimmed, isDesktop };
		lastKeyword = trimmed;
		result = [];
		isSearching = true;
		requestPagefindLoad();
		return;
	}

	isSearching = true;
	searchFailed = false;

	try {
		let searchResults: SearchResult[] = [];

		if (import.meta.env.PROD && pagefindLoaded && window.pagefind) {
			const response = await window.pagefind.search(trimmed);
			searchResults = await Promise.all(
				response.results.map((item) => item.data()),
			);
		} else if (import.meta.env.DEV) {
			searchResults = fakeResult;
		} else {
			searchResults = [];
			searchFailed = true;
			console.error("Pagefind 未就绪或加载失败，无法执行搜索。");
		}

		// 竞态保护：慢查询返回时若输入已变，丢弃这次结果
		if (trimmed !== keyword.trim()) return;

		lastKeyword = trimmed;
		result = searchResults;
		activeIndex = -1;
		// 移动端没有常驻输入框，只在有结果时展开面板；桌面端保持展开以便显示空状态
		setPanelVisibility(isDesktop || result.length > 0);
	} catch (error) {
		console.error("Search error:", error);
		lastKeyword = trimmed;
		result = [];
		activeIndex = -1;
		setPanelVisibility(isDesktop);
	} finally {
		isSearching = false;
	}
};

function scheduleSearch(keyword: string, isDesktop: boolean): void {
	clearTimeout(debounceTimer);
	debounceTimer = setTimeout(() => {
		void search(keyword, isDesktop);
	}, DEBOUNCE_MS);
}

/** 把键盘选中项滚进可视区（面板自身 max-height + overflow-y: auto） */
function scrollActiveIntoView(): void {
	const options = panelEl()?.querySelectorAll("[role='option']");
	options?.[activeIndex]?.scrollIntoView({ block: "nearest" });
}

function navigateTo(target: string): void {
	const swup = window.swup as unknown as
		| { navigate?: (url: string) => unknown }
		| undefined;
	if (typeof swup?.navigate === "function") {
		void swup.navigate(target);
	} else {
		window.location.href = target;
	}
}

function onInputKeydown(event: KeyboardEvent): void {
	if (event.key === "Escape") {
		event.preventDefault();
		closeSearch();
		return;
	}
	if (result.length === 0) return;

	if (event.key === "ArrowDown") {
		event.preventDefault();
		activeIndex = (activeIndex + 1) % result.length;
		scrollActiveIntoView();
	} else if (event.key === "ArrowUp") {
		event.preventDefault();
		activeIndex = activeIndex <= 0 ? result.length - 1 : activeIndex - 1;
		scrollActiveIntoView();
	} else if (event.key === "Enter") {
		const target = result[activeIndex]?.url;
		if (target) {
			event.preventDefault();
			navigateTo(target);
		}
	}
}

function onGlobalKeydown(event: KeyboardEvent): void {
	if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
		event.preventDefault();
		openSearch();
		return;
	}
	if (event.key === "Escape" && isPanelOpen()) {
		closeSearch();
	}
}

onMount(() => {
	const initializeSearch = () => {
		initialized = true;
		pagefindLoaded =
			typeof window !== "undefined" &&
			!!window.pagefind &&
			typeof window.pagefind.search === "function";

		// 优先重放「还没就绪时输入的那次查询」
		const pending = pendingQuery;
		pendingQuery = undefined;
		if (pending) {
			void search(pending.keyword, pending.isDesktop);
		} else if (keywordDesktop) {
			void search(keywordDesktop, true);
		} else if (keywordMobile) {
			void search(keywordMobile, false);
		}
	};

	if (import.meta.env.DEV) {
		initializeSearch();
	} else if (window.pagefind) {
		// pagefind 已经就绪（比本组件先跑完）
		initializeSearch();
	} else {
		document.addEventListener("pagefindready", initializeSearch, {
			once: true,
		});
		document.addEventListener(
			"pagefindloaderror",
			() => {
				console.warn("Pagefind 加载失败，搜索将不可用。");
				initializeSearch();
			},
			{ once: true },
		);
	}

	document.addEventListener("keydown", onGlobalKeydown);

	const observer = new MutationObserver(syncPanelAria);
	const node = panelEl();
	observer.observe(node ?? document.body, {
		attributes: true,
		attributeFilter: ["class"],
	});
	syncPanelAria();

	return () => {
		document.removeEventListener("keydown", onGlobalKeydown);
		document.removeEventListener("pagefindready", initializeSearch);
		observer.disconnect();
		clearTimeout(debounceTimer);
	};
});

$: if (initialized && keywordDesktop !== undefined) {
	scheduleSearch(keywordDesktop, true);
}

$: if (initialized && keywordMobile !== undefined) {
	scheduleSearch(keywordMobile, false);
}
</script>

<!-- search bar for desktop view -->
<div id="search-bar" class="hidden lg:flex transition-all items-center h-11 mr-2 rounded-lg
      bg-black/[0.04] hover:bg-black/[0.06] focus-within:bg-black/[0.06]
      dark:bg-white/5 dark:hover:bg-white/10 dark:focus-within:bg-white/10
">
    <Icon icon={localIcons["material-symbols:search"]} class="absolute text-[1.25rem] pointer-events-none ml-3 transition my-auto text-black/45 dark:text-white/45"></Icon>
    <input id="search-input" placeholder="{i18n(I18nKey.search)}"
           aria-label="站内搜索，按 Ctrl 或 Command 加 K 唤起"
           aria-controls="search-panel" aria-expanded="false" autocomplete="off"
           bind:value={keywordDesktop}
           on:focus={() => { if (keywordDesktop) void search(keywordDesktop, true); }}
           on:keydown={onInputKeydown}
           class="transition-all pl-10 text-sm bg-transparent
         h-full w-40 active:w-60 focus:w-60 text-black/70 dark:text-white/60 placeholder:text-black/55 dark:placeholder:text-white/55"
    >
</div>

<!-- toggle btn for phone/tablet view -->
<button on:click={() => (isPanelOpen() ? closeSearch() : openSearch())}
        aria-label="打开搜索" aria-controls="search-panel" aria-expanded="false"
        id="search-switch"
        class="btn-plain scale-animation lg:!hidden rounded-lg w-11 h-11 active:scale-90">
    <Icon icon={localIcons["material-symbols:search"]} class="text-[1.25rem]"></Icon>
</button>

<!-- search panel -->
<div id="search-panel" role="dialog" aria-label="站内搜索结果"
     class="float-panel float-panel-closed search-panel absolute md:w-[30rem]
top-20 left-4 md:left-[unset] right-4 shadow-2xl rounded-2xl p-2">

    <!-- search bar inside panel for phone/tablet -->
    <div id="search-bar-inside" class="flex relative lg:hidden transition-all items-center h-11 rounded-xl
      bg-black/[0.04] hover:bg-black/[0.06] focus-within:bg-black/[0.06]
      dark:bg-white/5 dark:hover:bg-white/10 dark:focus-within:bg-white/10
  ">
        <Icon icon={localIcons["material-symbols:search"]} class="absolute text-[1.25rem] pointer-events-none ml-3 transition my-auto text-black/45 dark:text-white/45"></Icon>
        <input id="search-input-mobile" placeholder="{i18n(I18nKey.search)}" aria-label="站内搜索"
               aria-controls="search-panel" autocomplete="off"
               bind:value={keywordMobile} on:keydown={onInputKeydown}
               class="pl-10 absolute inset-0 text-sm bg-transparent
               focus:w-60 text-black/70 dark:text-white/60 placeholder:text-black/55 dark:placeholder:text-white/55"
        >
    </div>

    {#if searchFailed}
        <div class="px-3 py-4 text-sm text-50">
            <p>搜索暂时不可用。</p>
            <a href={url("/archive/")} class="mt-1 inline-block text-[var(--primary)] underline underline-offset-2">
                先去归档页翻一翻 →
            </a>
        </div>
    {:else if isSearching && result.length === 0}
        <p class="px-3 py-4 text-sm text-50">搜索中…</p>
    {:else if lastKeyword && result.length === 0}
        <div class="px-3 py-4 text-sm text-50">
            <p>没有匹配「{lastKeyword}」的内容。</p>
            <a href={url("/archive/")} class="mt-1 inline-block text-[var(--primary)] underline underline-offset-2">
                去归档页翻一翻 →
            </a>
        </div>
    {/if}

    <!-- search results -->
    <ul role="listbox" aria-label="搜索结果">
        {#each result as item, i}
            <li role="none">
                <a href={item.url} role="option" aria-selected={i === activeIndex}
                   on:mouseenter={() => (activeIndex = i)}
                   class="{i === activeIndex ? 'bg-[var(--btn-plain-bg-hover)]' : ''}
                   transition block rounded-xl text-lg px-3 py-2 mt-0.5
                   hover:bg-[var(--btn-plain-bg-hover)] active:bg-[var(--btn-plain-bg-active)]">
                    <div class="transition text-90 inline-flex font-bold">
                        {item.meta.title}<Icon icon={localIcons["fa6-solid:chevron-right"]} class="transition text-[0.75rem] translate-x-1 my-auto text-[var(--primary)]"></Icon>
                    </div>
                    <div class="transition text-sm text-50">
                        {@html item.excerpt}
                    </div>
                </a>
            </li>
        {/each}
    </ul>
</div>

<style>
  .search-panel {
    max-height: calc(100vh - 100px);
    overflow-y: auto;
  }
</style>
