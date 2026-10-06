import type {
	ExpressiveCodeConfig,
	LicenseConfig,
	NavBarConfig,
	ProfileConfig,
	SiteConfig,
} from "./types/config";
import { LinkPreset } from "./types/config";

export const siteConfig: SiteConfig = {
	title: "Henzhi 的博客",
	subtitle: "生活记录、学习笔记与教程笔记",
	lang: "zh_CN", // Language code, e.g. 'en', 'zh_CN', 'ja', etc.
	themeColor: {
		hue: 250, // 强调色固定为蓝（hue 250），仅用于链接与导航当前态
		fixed: true, // 锁定主题色，不向访客提供换色入口
	},
	banner: {
		enable: false,
		src: "", // 不启用 banner；头像与 banner 素材均已移除
		position: "center", // Equivalent to object-position, only supports 'top', 'center', 'bottom'. 'center' by default
		credit: {
			enable: false, // Display the credit text of the banner image
			text: "", // Credit text to be displayed
			url: "", // (Optional) URL link to the original artwork or artist's page
		},
	},
	toc: {
		enable: true, // 在文章页左侧显示可折叠目录（≥100em 为固定竖栏，以下为抽屉）
		depth: 3, // 目录最多展示几级标题（正文最小标题级为第 1 级），1~3
	},
	favicon: [
		// Leave this array empty to use the default favicon
	],
};

export const navBarConfig: NavBarConfig = {
	links: [
		LinkPreset.Home,
		{
			name: "分类",
			url: "/categories/", // Internal links should not include the base path, as it is automatically added
		},
		LinkPreset.Archive,
		LinkPreset.About,
		{
			name: "GitHub",
			url: "https://github.com/Henzhi",
			external: true, // Show an external link icon and will open in a new tab
		},
	],
};

export const profileConfig: ProfileConfig = {
	avatar: "https://github.com/Henzhi.png?size=128", // GitHub 头像外链，Hero 里渲染
	name: "Henzhi",
	bio: "个人记录型博客：写日常生活，整理学习笔记，也把折腾过的东西写成能照着做的教程。",
	links: [
		{
			name: "GitHub",
			icon: "fa6-brands:github", // Visit https://icones.js.org/ for icon codes
			url: "https://github.com/Henzhi",
		},
	],
};

export const licenseConfig: LicenseConfig = {
	enable: true,
	name: "CC BY-NC-SA 4.0",
	url: "https://creativecommons.org/licenses/by-nc-sa/4.0/",
};

export const expressiveCodeConfig: ExpressiveCodeConfig = {
	// Note: Some styles (such as background color) are being overridden, see the astro.config.mjs file.
	// Please select a dark theme, as this blog theme currently only supports dark background color
	theme: "github-dark",
};
