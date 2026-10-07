import { siteConfig } from "../config";
import type I18nKey from "./i18nKey";
import { en } from "./languages/en";
import { zh_CN } from "./languages/zh_CN";

export type Translation = {
	[K in I18nKey]: string;
};

/**
 * 站点语言固定为 zh_CN（见 src/config.ts）。
 *
 * 这里原先静态 import 了 10 种语言包，Vite 会把它们全部纳入首屏依赖图 ——
 * 实测首屏因此白白多下载一个语言 chunk（zh_TW 那个 7.3KB 就是这么来的）。
 * 现在只保留实际会用到的两种：en 作为兜底，zh_CN 是站点语言。
 *
 * 将来要恢复多语言：把对应语言文件加回 import 与 map 即可，
 * src/i18n/languages/*.ts 都还在，一个都没删。
 */
const defaultTranslation = en;

const map: { [key: string]: Translation } = {
	en: en,
	en_us: en,
	en_gb: en,
	en_au: en,
	zh_cn: zh_CN,
	zh_tw: zh_CN, // 需要真正的繁体时改回 zh_TW 并加回 import
};

export function getTranslation(lang: string): Translation {
	return map[lang.toLowerCase()] || defaultTranslation;
}

export function i18n(key: I18nKey): string {
	const lang = siteConfig.lang || "en";
	return getTranslation(lang)[key];
}
