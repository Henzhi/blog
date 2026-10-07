#!/usr/bin/env node
/**
 * 生成本地图标映射 src/constants/local-icons.ts
 *
 * 为什么需要它：
 *   @iconify/svelte 的 <Icon icon="material-symbols:search"> 传字符串名时，
 *   会在**运行时**向 api.iconify.design 请求图标集 JSON。国内访问不稳定，
 *   请求失败或超时按钮就变成空白，而且给 CSP 引入一个第三方域名。
 *   改传图标对象则走 @iconify/svelte 的离线路径，零网络请求。
 *
 *   本地 @iconify-json/* 包只提供全量 icons.json（几 MB），不能整体 import，
 *   所以这里在构建前把**实际用到的那几个**图标提取成一个小文件。
 *
 * 用法：
 *   node scripts/gen-local-icons.mjs
 *
 * 新增图标时：把 "图标集:图标名" 加到下面的 WANTED 里再跑一次，
 * 然后把组件里的 icon="xxx" 改成 icon={localIcons["xxx"]}。
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/** 图标集 -> 该集合里用到的图标名 */
const WANTED = {
	"material-symbols": [
		"search",
		"wb-sunny-outline-rounded",
		"dark-mode-outline-rounded",
		"radio-button-partial-outline",
	],
	"fa6-solid": ["chevron-right", "arrow-rotate-left"],
};

const OUT = path.join(ROOT, "src/constants/local-icons.ts");

/** 这些键不是图标定义，提取时要跳过 */
const META_KEYS = new Set(["body", "width", "height", "left", "top"]);

function extract() {
	const out = {};
	for (const [prefix, names] of Object.entries(WANTED)) {
		const file = path.join(
			ROOT,
			"node_modules",
			"@iconify-json",
			prefix,
			"icons.json",
		);
		const data = JSON.parse(fs.readFileSync(file, "utf8"));
		const icons = data.icons ?? {};
		const aliases = data.aliases ?? {};

		for (const name of names) {
			let node = icons[name];
			if (!node && aliases[name]?.parent) {
				node = icons[aliases[name].parent];
			}
			if (!node) {
				throw new Error(`图标缺失：${prefix}:${name}`);
			}

			const entry = {
				body: node.body,
				width: node.width ?? data.width,
				height: node.height ?? data.height,
			};
			for (const key of Object.keys(node)) {
				if (!META_KEYS.has(key) && !(key in entry)) {
					entry[key] = node[key];
				}
			}
			out[`${prefix}:${name}`] = entry;
		}
	}
	return out;
}

function render(icons) {
	const lines = [
		"// 本文件由 scripts/gen-local-icons.mjs 生成，请勿手改。",
		"// 图标取自本地 @iconify-json 数据包并在构建期内联 —— 目的是让 @iconify/svelte",
		"// 走离线路径，不再于运行时向 api.iconify.design 拉取图标集。",
		"",
		"export interface LocalIcon {",
		"\tbody: string;",
		"\twidth?: number;",
		"\theight?: number;",
		"\tleft?: number;",
		"\ttop?: number;",
		"\thFlip?: boolean;",
		"\tvFlip?: boolean;",
		"\trotate?: number;",
		"}",
		"",
		"export const localIcons = {",
	];
	for (const [key, value] of Object.entries(icons)) {
		lines.push(`\t${JSON.stringify(key)}: ${JSON.stringify(value)},`);
	}
	lines.push("} as const satisfies Record<string, LocalIcon>;");
	lines.push("");
	lines.push("export type LocalIconName = keyof typeof localIcons;");
	lines.push("");
	return lines.join("\n");
}

const icons = extract();
fs.writeFileSync(OUT, render(icons), "utf8");
console.log(
	`已生成 ${path.relative(ROOT, OUT)}（${Object.keys(icons).length} 个图标）`,
);
