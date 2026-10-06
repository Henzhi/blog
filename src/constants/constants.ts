export const PAGE_SIZE = 8;

export const LIGHT_MODE = "light",
	DARK_MODE = "dark",
	AUTO_MODE = "auto";
export const DEFAULT_THEME = AUTO_MODE;

// Banner height unit: vh
export const BANNER_HEIGHT = 35;
export const BANNER_HEIGHT_EXTEND = 30;
export const BANNER_HEIGHT_HOME = BANNER_HEIGHT + BANNER_HEIGHT_EXTEND;

// The height the main panel overlaps the banner, unit: rem
export const MAIN_PANEL_OVERLAPS_BANNER_HEIGHT = 3.5;

// Page width: rem
// 1200px = px-4(16×2) + 左侧目录列 12.5rem + gap 3rem + 正文 42rem + gap 3rem + 右侧栏 12.5rem
// 这个值必须让「正文在三栏里正好 42rem」，否则行长上限形同虚设。改栅格/间距时同步重算。
export const PAGE_WIDTH = 75;
