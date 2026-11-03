import {
	mkdirSync,
	readFileSync,
	readdirSync,
	statSync,
	writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs, isDeepStrictEqual } from "node:util";
import * as resolver from "./profile_resolver.mjs";

/** @typedef {Record<string, any>} Dict */
/** @typedef {[number, number, number]} LCH */
export const EXT = resolver.EXT;
export const MODES = ["light", "dark"];
export const STEP = 0.005;
export const SCHEMA =
	"https://www.designtokens.org/schemas/2025.10/resolver.json";
export const SYSTEM_SANS =
	"system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
export const SYSTEM_MONO =
	"ui-monospace, 'SF Mono', Menlo, Consolas, monospace";
export const EXAMPLES_DIR = resolve(
	dirname(fileURLToPath(import.meta.url)),
	"../resources/examples",
);
export const LINEAGE_DIR = "tmp/design-profiles";
export const GOLDEN_ANGLE = 360 / ((1 + Math.sqrt(5)) / 2) ** 2;
// Relative L/C and signed hue offsets measured from the five-shade reference ramp.
// This is our fallback curation recipe, not a formula supplied by shadcn.
export const CHART_SHADES = [
	[1, 1, 0],
	[0.704 / 0.855, 0.14 / 0.138, 1.432],
	[0.6 / 0.855, 0.118 / 0.138, 3.633],
	[0.511 / 0.855, 0.096 / 0.138, 5.32],
	[0.437 / 0.855, 0.078 / 0.138, 7.145],
];
/** Shadcn's semantic CSS contract, mapped to the profile's curated roles.
 * Imported values take precedence over these fallback projections.
 * @type {Record<string,string>} */
/** Old `surface.css` role keys and their shadcn-aligned names. Saved profiles
 * migrate on load, so a stated edit under an old name is kept under the new one. */
export const CSS_ROLE_RENAMES = {
	page: "background",
	sunken: "muted",
	raised: "card",
	text: "foreground",
	"text-subtle": "muted-foreground",
	"text-subtlest": "faint-foreground",
	accent: "primary",
	"on-accent": "primary-foreground",
	"accent-subtlest": "primary-subtle",
	"border-bold": "border-strong",
	focus: "ring",
};
/** `surface.css` roles shadcn has no variable for. CSS exports them as is. */
export const CSS_EXTENSIONS = [
	"link",
	"faint-foreground",
	"primary-subtle",
	"border-strong",
	"selected",
];
export const SHADCN_VARIABLES = {
	background: "color.surface",
	foreground: "color.text",
	card: "color.surface.raised",
	"card-foreground": "color.text",
	popover: "color.surface.raised",
	"popover-foreground": "color.text",
	primary: "color.background.brand.bold",
	"primary-foreground": "color.text.inverse",
	secondary: "color.background.selected",
	"secondary-foreground": "color.text.selected",
	muted: "color.surface.sunken",
	"muted-foreground": "color.text.subtle",
	accent: "color.background.selected.hovered",
	"accent-foreground": "color.text.selected",
	destructive: "color.text.danger",
	input: "color.border.bold",
	ring: "color.border.focused",
	sidebar: "color.surface.sunken",
	"sidebar-foreground": "color.text",
	"sidebar-primary": "color.background.brand.bold",
	"sidebar-primary-foreground": "color.text.inverse",
	"sidebar-accent": "color.background.selected",
	"sidebar-accent-foreground": "color.text.selected",
	"sidebar-ring": "color.border.focused",
	...Object.fromEntries(
		Array.from({ length: 5 }, (_, i) => [
			`chart-${i + 1}`,
			`color.chart.sequential.${i + 1}`,
		]),
	),
};
/** @type {Record<string, [any, string]>} */
export const DEFAULTS = {
	radius: ["12px", "DT-RADIUS-1"],
	"radius.dark": [null, "DT-RADIUS-1 (defaults to radius)"],
	"brand.hue": [null, "DT-ACCENT-1 (required)"],
	"brand.chroma": [
		"cusp",
		"CURATION stage 3 (hue-only: the hue's most colourful in-gamut point)",
	],
	"brand.lightness": [
		"cusp",
		"CURATION stage 3 (hue-only; a stated value pins the light accent)",
	],
	"brand.dark.hue": [null, "DT-ACCENT-1 (defaults to brand.hue)"],
	"brand.dark.chroma": [null, "DT-ACCENT-1 (defaults to brand.chroma)"],
	"brand.dark.lightness": [
		null,
		"DT-ACCENT-1 (stated: pins the dark accent verbatim; else solved)",
	],
	"L-dark-bg": [0.15, "DT-REF-1"],
	"L-light-bg": [0.97, "DT-REF-1"],
	"offset.surface.sunken": [-0.05, "DT-REF-1"],
	"offset.surface.raised": [0.05, "DT-REF-1"],
	"offset.text": [0.9, "DT-REF-1"],
	"offset.text.subtle": [0.65, "DT-REF-1"],
	"target.text.subtlest": [
		4.5,
		"WCAG 2.2 SC 1.4.3 (AA: the lowest text tier still reads)",
	],
	"alpha.border": [0.14, "DT-BORDER-1"],
	"offset.border.bold": [0.35, "DT-BORDER-1 (search start; solved to 3:1)"],
	"target.graphic": [3.0, "WCAG 2.2 SC 1.4.11"],
	"target.text.inverse": [
		7.0,
		"DT-CONTRAST-1 (maximise: WCAG 2.2 SC 1.4.6 AAA on the brand fill)",
	],
	"target.link": [4.5, "WCAG 2.2 SC 1.4.3 (AA text)"],
	"alpha.brand.subtlest": [
		0.16,
		"CURATION stage 3 (the fill at 16% over the surface)",
	],
	"secondary.hue": [null, "DT-ACCENT-1 (defaults to brand.hue)"],
	"secondary.chromaRatio": [0.444, "DT-ACCENT-1 (M3 chroma 16/36)"],
	"offset.background.selected": [
		0.07,
		"DT-ACCENT-1 (M3 secondaryContainer sits 0.068 L from its surface)",
	],
	"walk.slots": [10, "DT-CHART-1"],
	"walk.angle": [GOLDEN_ANGLE, "DT-CHART-1"],
	"walk.lightness": ["brand", "DT-WALK-2 (each mode's accent lightness)"],
	"walk.chromaCeiling": ["seed", "DT-CHART-1"],
	"status.hue.danger": [
		25.0,
		"CURATION stage 5 (Primer danger.fg 24.6, Tailwind red-600 27.3, M3 error 28.7)",
	],
	"status.hue.warning": [
		75.0,
		"CURATION stage 5 (Primer attention.fg 75.0, a text role)",
	],
	"status.hue.success": [
		148.0,
		"CURATION stage 5 (Primer success.fg 148.0, Tailwind green-600 149.2)",
	],
	"status.chromaCap": [0.18, "CURATION stage 5 (M3 error chroma 0.178)"],
	"target.status": [4.5, "WCAG 2.2 SC 1.4.3 (AA text)"],
	"mode.default": ["light", "DT-DTCG-1 (modifiers.mode.default)"],
	"font.display": [
		"system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
		"MIGRATION M4 (system stack)",
	],
	"font.body": [
		"system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
		"MIGRATION M4 (system stack)",
	],
	"font.mono": [
		"ui-monospace, 'SF Mono', Menlo, Consolas, monospace",
		"MIGRATION M4 (system stack)",
	],
	"font.stylesheet": [null, "MIGRATION M4 (optional web-font stylesheet URL)"],
};

/** @param {number} value @param {number} [places] */
export function round(value, places = 0) {
	const factor = 10 ** places;
	const scaled = value * factor;
	const floor = Math.floor(scaled);
	// Match round-to-even when a channel or alpha lands exactly halfway.
	return (
		(scaled - floor === 0.5 ? floor + (floor % 2) : Math.round(scaled)) / factor
	);
}
/** @param {number} value */
export const mod360 = (value) =>
	value < 0 ? ((value % 360) + 360) % 360 : value % 360;
/** @param {number} value */
const clamp = (value) => Math.min(1, Math.max(0, value));
/** @param {number} value */
const byte = (value) => round(value).toString(16).padStart(2, "0");
/** @param {number[][]} matrix @param {number[]} vector @returns {LCH} */
const mul = (matrix, vector) =>
	/** @type {LCH} */ (
		matrix.map(
			(row) => row[0] * vector[0] + row[1] * vector[1] + row[2] * vector[2],
		)
	);
/** @param {number} c */
export const to_lin = (c) =>
	c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
/** @param {number} c */
const to_srgb = (c) =>
	clamp(c) <= 0.0031308
		? clamp(c) * 12.92
		: 1.055 * clamp(c) ** (1 / 2.4) - 0.055;
/** @param {number[]} lch @returns {LCH} */
export function lin_rgb([L, C, h]) {
	const rad = (h * Math.PI) / 180;
	const lms = mul(
		[
			[1, 0.3963377774, 0.2158037573],
			[1, -0.1055613458, -0.0638541728],
			[1, -0.0894841775, -1.291485548],
		],
		[L, C * Math.cos(rad), C * Math.sin(rad)],
	);
	return mul(
		[
			[4.0767416621, -3.3077115913, 0.2309699292],
			[-1.2684380046, 2.6097574011, -0.3413193965],
			[-0.0041960863, -0.7034186147, 1.707614701],
		],
		lms.map((x) => x ** 3),
	);
}
/** @param {number} L @param {number} h */
export function max_chroma(L, h) {
	if (L <= 0 || L >= 1) return 0;
	let lo = 0,
		hi = 0.4;
	for (let i = 0; i < 26; i++) {
		const mid = (lo + hi) / 2;
		if (lin_rgb([L, mid, h]).every((c) => c >= -1e-4 && c <= 1 + 1e-4))
			lo = mid;
		else hi = mid;
	}
	return lo;
}
/** Reduce chroma only, retaining the requested lightness and hue.
 * @param {number[]} lch */
export function fit_srgb([L, C, h]) {
	if (!lin_rgb([L, C, h]).every((c) => c >= 0 && c <= 1)) {
		let lo = 0,
			hi = C;
		for (let i = 0; i < 50; i++) {
			const mid = (lo + hi) / 2;
			if (lin_rgb([L, mid, h]).every((c) => c >= 0 && c <= 1)) lo = mid;
			else hi = mid;
		}
		C = Math.floor(lo * 1e6) / 1e6;
	}
	return [L, C, h];
}
/** @param {number[]} lch */
export const hex_of = (lch) =>
	`#${lin_rgb(lch)
		.map((c) => byte(to_srgb(c) * 255))
		.join("")}`;
/** @param {string} hex @returns {[number[], number]} */
export function rgb8(hex) {
	if (!/^#[\da-f]{6}([\da-f]{2})?$/i.test(hex))
		throw new Error(`Invalid hex colour: ${hex}`);
	return [
		[1, 3, 5].map((i) => Number.parseInt(hex.slice(i, i + 2), 16)),
		hex.length === 9 ? Number.parseInt(hex.slice(7), 16) / 255 : 1,
	];
}
/** @param {string} hex @returns {LCH} */
export function oklch_of(hex) {
	const lin = rgb8(hex)[0].map((c) => to_lin(c / 255));
	const lms = mul(
		[
			[0.4122214708, 0.5363325363, 0.0514459929],
			[0.2119034982, 0.6806995451, 0.1073969566],
			[0.0883024619, 0.2817188376, 0.6299787005],
		],
		lin,
	);
	const [L, a, b] = mul(
		[
			[0.2104542553, 0.793617785, -0.0040720468],
			[1.9779984951, -2.428592205, 0.4505937099],
			[0.0259040371, 0.7827717662, -0.808675766],
		],
		lms.map(Math.cbrt),
	);
	return [L, Math.hypot(a, b), mod360((Math.atan2(b, a) * 180) / Math.PI)];
}
/** @param {string} fg @param {string} bg */
export function composite(fg, bg) {
	const [f, alpha] = rgb8(fg),
		[b] = rgb8(bg);
	return `#${f.map((x, i) => byte(x * alpha + b[i] * (1 - alpha))).join("")}`;
}
/** @param {string} a @param {string} b */
export function contrast(a, b) {
	/** @param {string} hex */
	const lum = (hex) => {
		const [r, g, b] = rgb8(hex)[0].map((c) => to_lin(c / 255));
		return 0.2126 * r + 0.7152 * g + 0.0722 * b;
	};
	const x = lum(a),
		y = lum(b);
	return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
/** @param {string} fill */
export const best_text = (fill) =>
	contrast(fill, "#000000") >= contrast(fill, "#ffffff")
		? "#000000"
		: "#ffffff";
/** @param {string} hex */
export function rgba(hex) {
	const [rgb, alpha] = rgb8(hex);
	return [...rgb, round(alpha * 255)];
}
/** @param {number} L @returns {LCH} */
export const grey = (L) => [clamp(L), 0, 0];
/** @param {string} hex @returns {LCH} */
export function exact_oklch(hex) {
	const exact = oklch_of(hex);
	for (let places = 3; places <= 8; places++) {
		const lch = /** @type {LCH} */ (exact.map((x) => round(x, places)));
		if (hex_of(lch) === hex.toLowerCase()) return lch;
	}
	throw new Error(`error: ${hex} does not round-trip through OKLCH`);
}
/** @param {Dict} seed @param {typeof DEFAULTS} [defaults] */
export function resolve_params(seed, defaults = DEFAULTS) {
	const unknown = Object.keys(seed).filter((k) => !(k in defaults));
	if (unknown.length)
		throw new Error(
			`error: unknown seed parameter(s): ${unknown.sort().join(", ")}`,
		);
	if (!("brand.hue" in seed))
		throw new Error("error: a seed must state brand.hue");
	parse_radius(seed.radius ?? defaults.radius[0]);
	if (seed["radius.dark"] != null) parse_radius(seed["radius.dark"]);
	if (!MODES.includes(seed["mode.default"] ?? "light"))
		throw new Error(`error: mode.default must be one of ${MODES}`);
	return Object.fromEntries(
		Object.entries(defaults).map(([k, [v, source]]) => [
			k,
			k in seed ? [seed[k], "stated"] : [v, `default (${source})`],
		]),
	);
}

/** Parse the same nonnegative px/rem radius accepted from preset CSS variables.
 * @param {string} value */
export function parse_radius(value) {
	const match = /^(\d+(?:\.\d+)?|\.\d+)(rem|px)?$/.exec(String(value));
	if (!match || !Number.isFinite(Number(match[1])))
		throw new Error(`Unsupported radius: ${value}`);
	return { value: Number(match[1]), unit: match[2] ?? "px" };
}
/** @param {(mode: string) => any} fn @returns {Dict} */
const both = (fn) => Object.fromEntries(MODES.map((m) => [m, fn(m)]));
/** @param {number} anchor @param {number} step */
const nearest = (anchor, step) =>
	[...new Set([anchor + step * STEP, anchor - step * STEP])].sort(
		(a, b) => a - b,
	);

export class Curator {
	/** @param {Dict} seed @param {Dict} [stated] @param {typeof DEFAULTS} [defaults] */
	constructor(seed, stated = {}, defaults = DEFAULTS) {
		this.p = resolve_params(seed, defaults);
		this.stated = stated;
		/** @type {Dict} */ this.ir = {};
		/** @type {Dict} */ this.resolved = {};
		/** @type {Dict} */ this.accent = {};
		this.brand_hue = 0;
		this.brand_c = 0;
		this.brand_l = 0;
	}
	/** @param {string} key */
	v(key) {
		return this.p[key][0];
	}
	/** @param {string[]} keys */
	cite(...keys) {
		return keys.map((k) => `${k}=${this.p[k][0]} [${this.p[k][1]}]`);
	}
	/** @param {string} role @param {Dict} values @param {string} rule @param {string[]} inputs @param {Dict|null} [lch] @param {string|null} [alias] @param {string[]|null} [roles] */
	put(role, values, rule, inputs, lch = null, alias = null, roles = null) {
		const pinned = this.stated[role] ?? {};
		/** @type {Dict} */ const ext = {
			origin: Object.fromEntries(
				Object.keys(values).map((m) => [m, m in pinned ? "stated" : "imputed"]),
			),
			derived: structuredClone(values),
			rule,
			inputs,
		};
		if (roles || alias) ext.roles = roles ?? [alias];
		// Keep full coordinates. Four-decimal rounding can change an 8-bit channel.
		const coordinates = { ...lch };
		for (const [m, value] of Object.entries(values))
			if (
				!coordinates[m] &&
				typeof value === "string" &&
				/^#[\da-f]{6}$/i.test(value)
			)
				coordinates[m] = oklch_of(value);
		if (Object.keys(coordinates).length) {
			ext.oklch = Object.fromEntries(
				Object.entries(coordinates).map(([m, coords]) => [m, [...coords]]),
			);
			for (const [m, value] of Object.entries(pinned))
				if (typeof value === "string" && value.length === 7)
					ext.oklch[m] = oklch_of(value);
		}
		if (alias) ext.alias = alias;
		this.ir[role] = { ...values, ...pinned, $extensions: { [EXT]: ext } };
	}
	/** @param {string} role @param {string} mode */
	val(role, mode) {
		return this.ir[role][mode];
	}
	/** @param {string} key @param {string} role */
	same(key, role) {
		this.put(
			key,
			both((m) => this.val(role, m)),
			`alias of ${role}`,
			[],
			this.ir[role].$extensions?.[EXT]?.oklch ?? null,
			role,
		);
		const kind =
			this.ir[role].$extensions?.[EXT]?.type ?? TYPES[role.split(".")[0]];
		if (kind && kind !== "color") this.ir[key].$extensions[EXT].type = kind;
	}
	/** @param {string} key @param {string} fg @param {string} bg */
	over(key, fg, bg) {
		this.put(
			key,
			both((m) => composite(this.val(fg, m), this.val(bg, m))),
			`${fg} flattened onto ${bg}`,
			[],
			null,
			null,
			[fg, bg],
		);
	}
	/** @param {string} key @param {string} fill */
	text_on(key, fill) {
		this.put(
			key,
			both((m) => best_text(this.val(fill, m))),
			`black or white, whichever reads better on ${fill}`,
			[],
			null,
			null,
			[fill],
		);
	}
	/** @param {string} mode */
	grounds(mode) {
		return [
			"color.surface.sunken",
			"color.surface",
			"color.surface.raised",
		].map((r) => this.val(r, mode));
	}
	/** @param {string} mode */
	sign(mode) {
		return mode === "dark" ? 1 : -1;
	}
	/** @param {string} mode */
	bg(mode) {
		return Number(this.v(mode === "dark" ? "L-dark-bg" : "L-light-bg"));
	}
	/** @param {number} hue @param {number} cap @param {number} anchor @param {(colour:string)=>boolean} test @param {string} what @returns {LCH} */
	solve(hue, cap, anchor, test, what) {
		for (let step = 0; step <= 1 / STEP; step++)
			for (const L of nearest(anchor, step)) {
				if (L < 0 || L > 1) continue;
				const lch = /** @type {LCH} */ ([
					L,
					Math.min(max_chroma(L, hue), cap),
					hue,
				]);
				if (test(hex_of(lch))) return lch;
			}
		throw new Error(`error: unsolvable: ${what} at hue ${hue.toFixed(1)}`);
	}
	/** @param {string} mode @param {number} target */
	on_all_grounds(mode, target) {
		return (/** @type {string} */ colour) =>
			Math.min(...this.grounds(mode).map((g) => contrast(colour, g))) >= target;
	}
	neutrals() {
		for (const [
			role,
			key,
			absolute,
		] of /** @type {[string,string|null,boolean][]} */ ([
			["color.surface.sunken", "offset.surface.sunken", true],
			["color.surface", null, true],
			["color.surface.raised", "offset.surface.raised", true],
			["color.text", "offset.text", false],
			["color.text.subtle", "offset.text.subtle", false],
		])) {
			const lch = both((m) =>
				grey(
					this.bg(m) +
						(key ? Number(this.v(key)) : 0) * (absolute ? 1 : this.sign(m)),
				),
			);
			this.put(
				role,
				both((m) => hex_of(lch[m])),
				key === null
					? "mode reference"
					: absolute
						? "reference + absolute offset"
						: "reference + offset toward text",
				this.cite("L-light-bg", "L-dark-bg", ...(key ? [key] : [])),
				lch,
			);
		}
		const bold = both((m) =>
			this.solve(
				0,
				0,
				this.bg(m) + this.sign(m) * Number(this.v("offset.border.bold")),
				this.on_all_grounds(m, Number(this.v("target.graphic"))),
				"border bold",
			),
		);
		this.put(
			"color.border.bold",
			both((m) => hex_of(bold[m])),
			"grey nearest reference + offset toward text reaching the target on every ground",
			this.cite(
				"L-light-bg",
				"L-dark-bg",
				"offset.border.bold",
				"target.graphic",
			),
			bold,
		);
		const subtle = both((m) => {
			for (let step = 1; step < 1 / STEP; step++) {
				const lch = grey(this.bg(m) + this.sign(m) * step * STEP);
				if (
					this.on_all_grounds(
						m,
						Number(this.v("target.text.subtlest")),
					)(hex_of(lch))
				)
					return lch;
			}
			throw new Error("error: unsolvable subtlest text");
		});
		this.put(
			"color.text.subtlest",
			both((m) => hex_of(subtle[m])),
			"nearest the ground reaching the target on every ground",
			this.cite("target.text.subtlest"),
			subtle,
		);
		this.put(
			"color.border",
			both(
				(m) =>
					this.val("color.text", m) +
					byte(Number(this.v("alpha.border")) * 255),
			),
			"color.text at alpha",
			this.cite("alpha.border"),
			null,
			null,
			["color.text"],
		);
	}
	/** @param {string} mode */
	fill_test(mode) {
		const grounds = this.on_all_grounds(mode, Number(this.v("target.graphic"))),
			target = Number(this.v("target.text.inverse"));
		return (/** @type {string} */ col) =>
			contrast(col, best_text(col)) >= target && grounds(col);
	}
	brand() {
		const hue = Number(this.v("brand.hue"));
		let cuspL = STEP;
		for (let i = 1; i < 1 / STEP; i++)
			if (max_chroma(i * STEP, hue) > max_chroma(cuspL, hue)) cuspL = i * STEP;
		const cuspC = max_chroma(cuspL, hue);
		this.brand_hue = hue;
		this.brand_c =
			this.v("brand.chroma") === "cusp"
				? cuspC
				: Number(this.v("brand.chroma"));
		this.brand_l =
			this.v("brand.lightness") === "cusp"
				? cuspL
				: Number(this.v("brand.lightness"));
		const dark = Object.fromEntries(
			["hue", "chroma", "lightness"].map((k) => [k, this.v(`brand.dark.${k}`)]),
		);
		this.accent = {
			light: [this.brand_l, this.brand_c, hue],
			dark: [
				dark.lightness ?? this.brand_l,
				dark.chroma ?? this.brand_c,
				dark.hue ?? hue,
			],
		};
		const pinned = {
			light: this.v("brand.lightness") !== "cusp",
			dark: dark.lightness !== null,
		};
		Object.assign(this.resolved, {
			"brand.lightness": this.brand_l,
			"brand.chroma": this.brand_c,
			...Object.fromEntries(
				["lightness", "chroma", "hue"].map((k, i) => [
					`brand.dark.${k}`,
					this.accent.dark[i],
				]),
			),
		});
		const base = [
			...this.cite(
				"brand.hue",
				"brand.chroma",
				"brand.lightness",
				...Object.keys(dark)
					.filter((k) => dark[k] !== null)
					.map((k) => `brand.dark.${k}`),
			),
			`cusp L=${cuspL.toFixed(3)} C=${cuspC.toFixed(4)} (derived)`,
		];
		const lch = both((m) =>
			pinned[/** @type {"light"|"dark"} */ (m)]
				? this.accent[m]
				: this.solve(
						this.accent[m][2],
						this.accent[m][1],
						this.accent[m][0],
						this.fill_test(m),
						"brand fill",
					),
		);
		const rule = MODES.map(
			(m) =>
				`${m}: ${pinned[/** @type {"light"|"dark"} */ (m)] ? "the stated accent, verbatim" : "lightness solved: inverse text reaches target, and 3:1 on every ground"}`,
		).join("; ");
		this.put(
			"color.background.brand.bold",
			both((m) => hex_of(lch[m])),
			rule,
			[...base, ...this.cite("target.text.inverse", "target.graphic")],
			lch,
		);
		this.text_on("color.text.inverse", "color.background.brand.bold");
		this.put(
			"color.background.brand.subtlest",
			both((m) =>
				composite(
					this.val("color.background.brand.bold", m) +
						byte(Number(this.v("alpha.brand.subtlest")) * 255),
					this.val("color.surface", m),
				),
			),
			"brand fill at alpha over color.surface",
			this.cite("alpha.brand.subtlest"),
			null,
			null,
			["color.background.brand.bold", "color.surface"],
		);
		for (const [role, key] of [
			["color.border.brand", "target.graphic"],
			["color.link", "target.link"],
		]) {
			const coords = both((m) =>
				this.solve(
					this.accent[m][2],
					this.accent[m][1],
					this.accent[m][0],
					this.on_all_grounds(m, Number(this.v(key))),
					role,
				),
			);
			this.put(
				role,
				both((m) => hex_of(coords[m])),
				"the mode's accent, lightness solved to reach the target on every ground",
				[...base, ...this.cite(key)],
				coords,
			);
		}
	}
	secondary() {
		const hue = Number(this.v("secondary.hue") ?? this.brand_hue),
			chroma = this.brand_c * Number(this.v("secondary.chromaRatio"));
		const inputs = this.cite(
			"secondary.hue",
			"secondary.chromaRatio",
			"brand.hue",
			"brand.chroma",
		);
		for (const [role, extra] of /** @type {[string,number][]} */ ([
			["color.background.selected", 0],
			["color.background.selected.hovered", STEP * 10],
		])) {
			const lch = both((m) => {
				const L =
					this.bg(m) +
					this.sign(m) * (Number(this.v("offset.background.selected")) + extra);
				return [L, Math.min(max_chroma(L, hue), chroma), hue];
			});
			this.put(
				role,
				both((m) => hex_of(lch[m])),
				"secondary at reduced chroma, offset from the ground toward text",
				[...inputs, ...this.cite("offset.background.selected")],
				lch,
			);
		}
		const lch = both((m) =>
			this.solve(
				hue,
				this.brand_c,
				this.brand_l,
				this.on_all_grounds(m, Number(this.v("target.graphic"))),
				"selected",
			),
		);
		this.put(
			"color.border.selected",
			both((m) => hex_of(lch[m])),
			"secondary hue reaching 3:1 on every ground",
			[...inputs, ...this.cite("target.graphic")],
			lch,
		);
		this.same("color.border.focused", "color.border.selected");
		this.same("color.text.selected", "color.text");
	}
	status() {
		for (const name of ["danger", "warning", "success"]) {
			const key = `status.hue.${name}`;
			const lch = both((m) =>
				this.solve(
					Number(this.v(key)),
					Number(this.v("status.chromaCap")),
					0.6,
					this.on_all_grounds(m, Number(this.v("target.status"))),
					name,
				),
			);
			this.put(
				`color.text.${name}`,
				both((m) => hex_of(lch[m])),
				"conventional hue reaching the target on every ground",
				this.cite(key, "status.chromaCap", "target.status"),
				lch,
			);
		}
	}
	/** @param {number} index */
	categorical_role(index) {
		return `color.chart.categorical.${String(index).padStart(2, "0")}`;
	}
	walk() {
		const n = Number(this.v("walk.slots")),
			angle = Number(this.v("walk.angle")),
			ceiling = this.v("walk.chromaCeiling"),
			follow = this.v("walk.lightness") === "brand";
		if (!Number.isInteger(n) || n < 1 || n > 99 || !Number.isFinite(angle))
			throw new Error("Invalid categorical walk configuration");
		const inputs = this.cite(
			"brand.hue",
			"walk.slots",
			"walk.angle",
			"walk.lightness",
			"walk.chromaCeiling",
			"target.graphic",
			...(ceiling === "seed" ? ["brand.chroma"] : []),
			...(follow ? ["brand.lightness"] : []),
			...(follow && this.v("brand.dark.lightness") !== null
				? ["brand.dark.lightness"]
				: []),
		);
		const perMode = both((m) => {
			const source =
				this.ir["color.background.brand.bold"].$extensions[EXT].oklch[m];
			const anchor = follow ? source[0] : Number(this.v("walk.lightness"));
			if (!Number.isFinite(anchor) || anchor < 0 || anchor > 1)
				throw new Error("Invalid chart lightness");
			const hues = Array.from({ length: n }, (_, i) =>
				mod360(source[2] + i * angle),
			);
			let cap =
				ceiling === "seed" || ceiling === "floor" ? source[1] : Number(ceiling);
			if (!Number.isFinite(cap) || cap < 0)
				throw new Error("Invalid chart chroma ceiling");
			if (ceiling === "floor")
				cap = Math.min(cap, ...hues.map((h) => fit_srgb([anchor, cap, h])[1]));
			this.resolved["walk.lightness"] ??= {};
			this.resolved["walk.lightness"][m] = anchor;
			return hues.map((h) => fit_srgb([anchor, cap, h]));
		});
		for (let i = 0; i < n; i++) {
			const lch = both((m) => perMode[m][i]);
			this.put(
				this.categorical_role(i + 1),
				both((m) => hex_of(lch[m])),
				`golden walk slot ${i + 1}: hue +${i}x${angle} deg, root lightness preserved, chroma-only sRGB mapping`,
				inputs,
				lch,
			);
		}
	}
	palettes() {
		for (let i = 1; i <= Number(this.v("walk.slots")); i++) {
			const index = String(i).padStart(2, "0"),
				role = this.categorical_role(i);
			this.same(`color.chart.palettes.${index}.1`, role);
			for (let j = 1; j < 5; j++) {
				const [scaleL, scaleC, dh] = CHART_SHADES[j];
				const lch = both((m) => {
					const root = this.ir[role].$extensions[EXT].oklch[m];
					return fit_srgb([
						root[0] * scaleL,
						root[1] * scaleC,
						mod360(root[2] + dh),
					]);
				});
				this.put(
					`color.chart.palettes.${index}.${j + 1}`,
					both((m) => hex_of(lch[m])),
					"relative five-shade reference recipe, scaled to this categorical root",
					[],
					lch,
					null,
					[role],
				);
			}
		}
		for (let j = 1; j <= 5; j++)
			this.same(`color.chart.sequential.${j}`, `color.chart.palettes.01.${j}`);
	}
	chart_contrast() {
		const n = Number(this.v("walk.slots"));
		return both((mode) => ({
			categoricalAdjacent: Array.from({ length: n - 1 }, (_, i) =>
				round(
					contrast(
						this.val(this.categorical_role(i + 1), mode),
						this.val(this.categorical_role(i + 2), mode),
					),
					4,
				),
			),
			sequentialAdjacent: Object.fromEntries(
				Array.from({ length: n }, (_, i) => {
					const index = String(i + 1).padStart(2, "0");
					return [
						index,
						Array.from({ length: 4 }, (_, j) =>
							round(
								contrast(
									this.val(`color.chart.palettes.${index}.${j + 1}`, mode),
									this.val(`color.chart.palettes.${index}.${j + 2}`, mode),
								),
								4,
							),
						),
					];
				}),
			),
		}));
	}
	ramps() {
		const danger = Number(this.v("status.hue.danger")),
			success = Number(this.v("status.hue.success")),
			cap = Number(this.v("status.chromaCap"));
		for (const [
			name,
			hue,
			chroma,
			count,
			keys,
		] of /** @type {[string,number,number,number,string[]][]} */ ([
			[
				"sequential",
				this.brand_hue,
				this.brand_c,
				5,
				["brand.hue", "brand.chroma"],
			],
			[
				"diverging.positive",
				this.brand_hue,
				this.brand_c,
				3,
				["brand.hue", "brand.chroma"],
			],
			[
				"diverging.negative",
				danger,
				cap,
				3,
				["status.hue.danger", "status.chromaCap"],
			],
			[
				"diverging.alt-positive",
				success,
				cap,
				3,
				["status.hue.success", "status.chromaCap"],
			],
		]))
			for (let i = 0; i < count; i++) {
				const lch = both((m) => {
					const [lo, hi] = m === "light" ? [0.88, 0.42] : [0.3, 0.82];
					const L = lo + (hi - lo) * (i / (count - 1));
					return [L, Math.min(max_chroma(L, hue), chroma), hue];
				});
				this.put(
					`color.chart.${name}.${i + 1}`,
					both((m) => hex_of(lch[m])),
					"evenly spaced lightness at a fixed hue, chroma capped",
					this.cite(...keys),
					lch,
				);
			}
		for (let i = 0; i < 4; i++) {
			const lch = both((m) => {
				const a =
						this.bg(m) + this.sign(m) * Number(this.v("offset.border.bold")),
					b = this.bg(m) + this.sign(m) * Number(this.v("offset.text.subtle"));
				return grey(a + ((b - a) * i) / 3);
			});
			this.put(
				`color.chart.muted.${i + 1}`,
				both((m) => hex_of(lch[m])),
				"greys from border.bold to text.subtle",
				this.cite(
					"L-light-bg",
					"L-dark-bg",
					"offset.border.bold",
					"offset.text.subtle",
				),
				lch,
			);
		}
	}
	fonts() {
		for (const name of ["display", "body", "mono"])
			this.put(
				`font.family.${name}`,
				both(() => this.v(`font.${name}`)),
				"the seed's font stack",
				this.cite(`font.${name}`),
			);
	}
	surfaces() {
		const slots = Array.from({ length: Number(this.v("walk.slots")) }, (_, i) =>
			this.categorical_role(i + 1),
		);
		const mappings = {
			// shadcn names wherever shadcn has the role; the rest are named
			// extensions (CSS_EXTENSIONS). See CSS_ROLE_RENAMES for the old names.
			css: {
				background: "color.surface",
				muted: "color.surface.sunken",
				card: "color.surface.raised",
				foreground: "color.text",
				"muted-foreground": "color.text.subtle",
				"faint-foreground": "color.text.subtlest",
				primary: "color.background.brand.bold",
				"primary-foreground": "color.text.inverse",
				"primary-subtle": "color.background.brand.subtlest",
				link: "color.link",
				"border-strong": "color.border.bold",
				ring: "color.border.focused",
				selected: "color.background.selected",
			},
			cytoscape: {
				"node.background-color": "color.background.brand.subtlest",
				"node.border-color": "color.border.brand",
				"node.color": "color.text",
				"node-alt.background-color": "color.background.selected",
				"edge.line-color": "color.border.bold",
				"edge.color": "color.text.subtle",
				"edge.text-background-color": "color.surface",
				"compound.background-color": "color.surface.sunken",
				"selected.border-color": "color.border.selected",
			},
			plotly: {
				paper_bgcolor: "color.surface.raised",
				plot_bgcolor: "color.surface",
				font_color: "color.text",
				"diverging.zero": "color.surface.sunken",
			},
			drawio: {
				"container.fillColor": "color.surface.sunken",
				"container.fontColor": "color.text",
				"edge.strokeColor": "color.border.bold",
				"edge.fontColor": "color.text.subtle",
			},
		};
		for (const [surface, values] of Object.entries(mappings))
			for (const [key, role] of Object.entries(values))
				this.same(`surface.${surface}.${key}`, role);
		for (const [key, bg] of [
			["css.border", "color.surface"],
			["cytoscape.compound.border-color", "color.surface.sunken"],
			["plotly.gridcolor", "color.surface"],
			["drawio.container.strokeColor", "color.surface.sunken"],
		])
			this.over(`surface.${key}`, "color.border", bg);
		slots.forEach((slot, i) => {
			this.same(`surface.plotly.colorway.${i + 1}`, slot);
			this.same(`surface.drawio.stencil.${i + 1}.fillColor`, slot);
			this.same(
				`surface.drawio.stencil.${i + 1}.strokeColor`,
				"color.border.bold",
			);
			this.text_on(`surface.drawio.stencil.${i + 1}.fontColor`, slot);
		});
		for (const [ramp, count] of /** @type {[string,number][]} */ ([
			["sequential", 5],
			["muted", 4],
			["diverging.positive", 3],
			["diverging.negative", 3],
			["diverging.alt-positive", 3],
		]))
			for (let i = 1; i <= count; i++)
				this.same(`surface.plotly.${ramp}.${i}`, `color.chart.${ramp}.${i}`);
		for (const [key, role] of Object.entries({
			background: "color.surface",
			ink: "color.text.subtle",
			text: "color.text",
			warn: "color.text.warning",
		}))
			this.put(
				`surface.deckgl.${key}`,
				both((m) => rgba(this.val(role, m))),
				`${role} as RGBA`,
				[],
				null,
				null,
				[role],
			);
		this.mermaid(slots);
		this.shadcn();
	}
	shadcn() {
		for (const [name, role] of Object.entries(SHADCN_VARIABLES)) {
			const source = `color.shadcn.${name}`;
			this.same(`surface.shadcn.${name}`, source in this.ir ? source : role);
		}
		for (const [name, ground] of [
			["border", "color.surface"],
			["sidebar-border", "color.surface.sunken"],
		]) {
			const source = `color.shadcn.${name}`;
			if (source in this.ir) this.same(`surface.shadcn.${name}`, source);
			else this.over(`surface.shadcn.${name}`, "color.border", ground);
		}
		const foreground = "color.shadcn.destructive-foreground";
		if (foreground in this.ir)
			this.same("surface.shadcn.destructive-foreground", foreground);
		else
			this.text_on(
				"surface.shadcn.destructive-foreground",
				"color.shadcn.destructive" in this.ir
					? "color.shadcn.destructive"
					: "color.text.danger",
			);
		this.same("surface.shadcn.radius", "dimension.radius");
		for (const [name, role] of [
			["font-sans", "body"],
			["font-heading", "display"],
			["font-mono", "mono"],
		])
			this.same(`surface.shadcn.${name}`, `font.family.${role}`);
	}
	/** @param {string[]} slots */
	mermaid(slots) {
		const mappings = {
			background: "color.surface",
			mainBkg: "color.background.brand.subtlest",
			primaryColor: "color.background.brand.subtlest",
			primaryTextColor: "color.text",
			primaryBorderColor: "color.border.brand",
			secondaryColor: "color.background.selected",
			secondaryTextColor: "color.text.selected",
			secondaryBorderColor: "color.border.selected",
			tertiaryColor: "color.surface.sunken",
			tertiaryTextColor: "color.text",
			tertiaryBorderColor: "color.border.bold",
			nodeBorder: "color.border.brand",
			nodeTextColor: "color.text",
			textColor: "color.text",
			titleColor: "color.text",
			lineColor: "color.border.bold",
			defaultLinkColor: "color.border.bold",
			edgeLabelBackground: "color.surface",
			clusterBkg: "color.surface.sunken",
			clusterBorder: "color.border.bold",
			noteBkgColor: "color.surface.raised",
			noteTextColor: "color.text",
			noteBorderColor: "color.border.bold",
			actorBkg: "color.background.brand.subtlest",
			actorBorder: "color.border.brand",
			actorTextColor: "color.text",
			actorLineColor: "color.border.bold",
			signalColor: "color.text",
			signalTextColor: "color.text",
			labelBoxBkgColor: "color.surface.raised",
			labelBoxBorderColor: "color.border.bold",
			labelTextColor: "color.text",
			loopTextColor: "color.text",
			activationBkgColor: "color.background.selected",
			activationBorderColor: "color.border.selected",
			sequenceNumberColor: "color.text.inverse",
			errorBkgColor: "color.surface.raised",
			errorTextColor: "color.text.danger",
			pieTitleTextColor: "color.text",
			pieLegendTextColor: "color.text",
			pieStrokeColor: "color.surface",
			pieOuterStrokeColor: "color.border.bold",
		};
		for (const [key, role] of Object.entries(mappings))
			this.same(`surface.mermaid.${key}`, role);
		slots.forEach((slot, i) => {
			this.same(`surface.mermaid.cScale${i}`, slot);
			this.text_on(`surface.mermaid.cScaleLabel${i}`, slot);
			this.same(`surface.mermaid.pie${i + 1}`, slot);
			if (i < 8) {
				this.same(`surface.mermaid.git${i}`, slot);
				this.text_on(`surface.mermaid.gitBranchLabel${i}`, slot);
			}
		});
		this.put(
			"surface.mermaid.pieSectionTextColor",
			both((m) => {
				const worst = (/** @type {string} */ text) =>
					Math.min(...slots.map((s) => contrast(text, this.val(s, m))));
				return worst("#000000") >= worst("#ffffff") ? "#000000" : "#ffffff";
			}),
			"black or white, whichever has the best worst case across the categorical slots",
			[],
			null,
			null,
			slots,
		);
	}
	dimensions() {
		this.put(
			"dimension.radius",
			Object.fromEntries(
				MODES.map((mode) => [
					mode,
					parse_radius(
						mode === "dark"
							? (this.v("radius.dark") ?? this.v("radius"))
							: this.v("radius"),
					),
				]),
			),
			"the seed's corner radius",
			this.cite("radius", "radius.dark"),
		);
	}
	/** @returns {Dict} */
	run() {
		this.neutrals();
		this.brand();
		this.secondary();
		this.status();
		this.walk();
		this.ramps();
		this.palettes();
		this.dimensions();
		this.fonts();
		this.surfaces();
		const params = Object.fromEntries(
			Object.entries(this.p).map(([k, [value, source]]) => [
				k,
				{ value, source },
			]),
		);
		return {
			$extensions: { [EXT]: { params, chartContrast: this.chart_contrast() } },
			...this.ir,
		};
	}
}

/** @param {Dict} ir @returns {Dict} */
export function stated_values(ir) {
	/** @type {Dict} */ const stated = {};
	for (const [role, node] of Object.entries(ir)) {
		if (role.startsWith("$")) continue;
		const ext = node.$extensions?.[EXT] ?? {};
		for (const m of MODES)
			if (
				m in node &&
				(ext.origin?.[m] === "stated" ||
					!isDeepStrictEqual(node[m], ext.derived?.[m]))
			) {
				stated[role] ??= {};
				stated[role][m] = node[m];
			}
	}
	return stated;
}
export const AA_TEXT = 4.5;
const GROUNDS = [
	"color.surface.sunken",
	"color.surface",
	"color.surface.raised",
];
/** @type {[string,string[]][]} */
export const TEXT_CHECKS = [
	["color.text", GROUNDS],
	["color.text.subtle", GROUNDS],
	["color.text.subtlest", GROUNDS],
	["color.link", GROUNDS],
	["color.text.danger", ["color.surface"]],
	["color.text.warning", ["color.surface"]],
	["color.text.success", ["color.surface"]],
	["color.text.inverse", ["color.background.brand.bold"]],
	["color.text", ["color.background.brand.subtlest"]],
	[
		"color.text.selected",
		["color.background.selected", "color.background.selected.hovered"],
	],
];
/** @param {Dict} ir */
export function score_contrast(ir) {
	/** @param {string} role @param {string} mode */
	const stated = (role, mode) => {
		const ext = ir[role].$extensions[EXT];
		return (
			ext.origin[mode] === "stated" ||
			ext.inputs.some(
				(/** @type {string} */ c) =>
					c.endsWith("[stated]") && !c.startsWith("brand.hue="),
			)
		);
	};
	return TEXT_CHECKS.flatMap(([text, grounds]) =>
		grounds.flatMap((on) =>
			MODES.map((mode) => {
				const ratio = contrast(ir[text][mode], ir[on][mode]);
				return {
					text,
					on,
					mode,
					ratio: round(ratio, 2),
					target: AA_TEXT,
					verdict:
						ratio >= AA_TEXT
							? "pass"
							: stated(text, mode) || stated(on, mode)
								? "choice"
								: "defect",
				};
			}),
		),
	);
}
/** @param {string} path @returns {Dict} */
export const read_json = (path) => JSON.parse(readFileSync(path, "utf8"));
/** @param {string} path @param {any} value */
export const write_json = (path, value) =>
	writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
/** @param {string} folder */
export function seed_of(folder) {
	if (resolver.isFile(join(folder, "seed.json")))
		return read_json(join(folder, "seed.json"));
	if (resolver.isFile(join(folder, "ir.json"))) {
		const params =
			read_json(join(folder, "ir.json")).$extensions?.[EXT]?.params ?? {};
		const recorded = Object.fromEntries(
			Object.entries(params)
				.filter(([, p]) => /** @type {Dict} */ (p).source === "stated")
				.map(([k, p]) => [k, /** @type {Dict} */ (p).value]),
		);
		if (Object.keys(recorded).length) return recorded;
	}
	throw new Error(
		`error: ${folder} has no seed.json and its ir.json records no stated parameters to curate from`,
	);
}
/** Only retire slots owned by the previous chart expansion; stated values stay held.
 * @param {string} role @param {number} count */
function retired_chart_role(role, count) {
	const oneBased =
		/^(?:color\.chart\.(?:categorical|palettes)|surface\.plotly\.colorway|surface\.drawio\.stencil)\.(\d+)(?:\.|$)/.exec(
			role,
		) ?? /^surface\.mermaid\.pie(\d+)$/.exec(role);
	const zeroBased =
		/^surface\.mermaid\.(?:cScale|cScaleLabel|git|gitBranchLabel)(\d+)$/.exec(
			role,
		);
	return oneBased
		? Number(oneBased[1]) > count
		: zeroBased
			? Number(zeroBased[1]) >= count
			: false;
}
/** @param {string} folder @param {typeof DEFAULTS} [defaults] */
export async function curate_profile(folder, defaults = DEFAULTS) {
	const seed = seed_of(folder),
		path = join(folder, "ir.json");
	let old = resolver.isFile(path) ? read_json(path) : {};
	old = (await import("./shadcn_profile.mjs")).normalise_chart_roles(old);
	const stated = stated_values(old);
	const ir = seed.preset
		? new (await import("./shadcn_profile.mjs")).PresetCurator(
				seed.preset,
				stated,
			).run()
		: new Curator(seed, stated, defaults).run();
	const report = [];
	const unknown = Object.keys(old).filter(
		(k) =>
			!k.startsWith("$") &&
			!(k in ir) &&
			(!retired_chart_role(
				k,
				Number(ir.$extensions[EXT].params["walk.slots"].value),
			) ||
				k in stated),
	);
	for (const role of unknown) {
		ir[role] = old[role];
		report.push(`held    ${role} (not a curated role; kept as stated)`);
	}
	for (const role of Object.keys(ir).filter(
		(k) => !k.startsWith("$") && !unknown.includes(k),
	))
		for (const m of MODES) {
			const before = old[role]?.[m],
				after = ir[role][m];
			if (stated[role] && m in stated[role]) {
				const derived = ir[role].$extensions[EXT].derived?.[m];
				report.push(
					`held    ${role} ${m} ${after} stated${derived == null || isDeepStrictEqual(derived, after) ? "" : ` (rule would give ${derived})`}`,
				);
			} else if (before === undefined)
				report.push(`new     ${role} ${m} ${after}`);
			else if (!isDeepStrictEqual(before, after))
				report.push(`updated ${role} ${m} ${before} -> ${after}`);
		}
	const scores = score_contrast(ir);
	ir.$extensions[EXT].contrast = scores;
	for (const s of scores)
		if (s.verdict !== "pass")
			report.push(
				`${s.verdict.padEnd(7)} ${s.text} on ${s.on} ${s.mode} ${s.ratio}:1 (AA ${s.target}:1)`,
			);
	mkdirSync(folder, { recursive: true });
	write_json(path, ir);
	return report;
}
/** @type {Record<string,string>} */
export const TYPES = {
	color: "color",
	surface: "color",
	font: "fontFamily",
	dimension: "dimension",
};
/** @param {string|number[]} value @param {number[]|null} lch */
export function dtcg_colour(value, lch) {
	const hex =
		typeof value === "string" ? value : `#${value.map(byte).join("")}`;
	const [rgb, alpha] = rgb8(hex);
	if (lch && alpha === 1)
		return { colorSpace: "oklch", components: lch, hex: hex.slice(0, 7) };
	return {
		colorSpace: "srgb",
		components: rgb.map((c) => round(c / 255, 4)),
		hex: hex.slice(0, 7),
		...(alpha !== 1 ? { alpha: round(alpha, 4) } : {}),
	};
}
/** @param {string} stack */
export const font_families = (stack) =>
	stack
		.split(",")
		.map((f) => f.trim().replace(/^['"]|['"]$/g, ""))
		.filter(Boolean);
/** @param {string} role @param {Set<string>} roles */
export const dtcg_path = (role, roles) => [
	...role.split("."),
	...([...roles].some((r) => r.startsWith(`${role}.`)) ? ["default"] : []),
];
/** @param {Dict} ir @param {string} name @returns {Dict} */
export function build_tokens(ir, name) {
	const roles = new Set(Object.keys(ir).filter((k) => !k.startsWith("$"))),
		metaIR = ir.$extensions?.[EXT] ?? {},
		params = metaIR.params ?? {};
	for (const role of [...roles].sort()) {
		const missing = MODES.filter((m) => !(m in ir[role]));
		if (missing.length)
			throw new Error(
				`error: ${role} has no ${missing.join("/")} value; a profile carries every permutation`,
			);
		if (!(role.split(".")[0] in TYPES))
			throw new Error(
				`error: ${role} is outside the color, surface, font and dimension groups`,
			);
	}
	const contexts = both((m) => {
		/** @type {Dict} */ const tree = Object.fromEntries(
			Object.entries(TYPES).map(([group, kind]) => [group, { $type: kind }]),
		);
		for (const role of [...roles].sort()) {
			const node = ir[role],
				ext = node.$extensions?.[EXT] ?? {},
				parts = dtcg_path(role, roles),
				leaf = /** @type {string} */ (parts.pop());
			let branch = tree;
			for (const part of parts) branch = branch[part] ??= {};
			const kind = ext.type ?? TYPES[role.split(".")[0]];
			let value;
			if (
				ext.alias &&
				MODES.every((mode) =>
					isDeepStrictEqual(node[mode], ext.derived?.[mode]),
				)
			)
				value = `{${dtcg_path(ext.alias, roles).join(".")}}`;
			else if (kind === "fontFamily") value = font_families(node[m]);
			else if (kind === "dimension") value = node[m];
			else if (node[m] === ext.cssDerived?.[m]) value = ext.dtcgValue[m];
			else {
				const lch = ext.oklch?.[m];
				value = dtcg_colour(
					node[m],
					lch && hex_of(lch) === node[m] ? lch : null,
				);
			}
			branch[leaf] = { $value: value };
			if (kind !== TYPES[role.split(".")[0]]) branch[leaf].$type = kind;
		}
		return [
			Object.fromEntries(
				Object.entries(tree).filter(([, v]) => Object.keys(v).length > 1),
			),
		];
	});
	/** @type {Dict} */ const meta = { profile: name };
	if (params["font.stylesheet"]?.value)
		meta.fontStylesheet = params["font.stylesheet"].value;
	for (const key of ["preset", "fontStylesheets", "chartContrast"])
		if (key in metaIR) meta[key] = metaIR[key];
	return {
		$schema: SCHEMA,
		version: "2025.10",
		name,
		modifiers: {
			mode: {
				contexts,
				default: params["mode.default"]?.value ?? "light",
				$extensions: { [EXT]: meta },
			},
		},
		resolutionOrder: [{ $ref: "#/modifiers/mode" }],
	};
}
/** @param {string} folder @param {string} [format] */
export async function build_profile(folder, format = "both") {
	if (!["css", "tokens", "both"].includes(format))
		throw new Error("Invalid output format");
	const path = join(folder, "ir.json");
	if (!resolver.isFile(path))
		throw new Error(
			`error: ${path} not found; run curate first, or hand-author an ir.json`,
		);
	const { normalise_chart_roles, build_css } = await import(
		"./shadcn_profile.mjs"
	);
	let ir = read_json(path);
	ir = normalise_chart_roles(ir);
	const out = join(folder, resolver.TOKENS_FILE),
		tokens = build_tokens(ir, basename(folder));
	const css = format !== "tokens" ? build_css(ir) : null;
	if (format !== "css") write_json(out, tokens);
	if (css !== null) writeFileSync(join(folder, "theme.css"), css);
	return format === "css" ? join(folder, "theme.css") : out;
}
/** @param {Dict} ir */
export function build_lineage(ir) {
	const params = ir.$extensions[EXT].params,
		keys = Object.keys(ir).filter((k) => !k.startsWith("$")),
		roles = keys.filter((k) => !k.startsWith("surface.")),
		neutral = { light: "#8a8a8a", dark: "#8a8a8a" };
	const colour = (/** @type {string} */ role) => {
		const values = both((m) => ir[role][m]);
		return Object.values(values).every(
			(v) => typeof v === "string" && v.startsWith("#"),
		)
			? both((m) => values[m].slice(0, 7))
			: neutral;
	};
	/** @type {{source:string,target:string}[]} */ const links = [];
	const used = new Set();
	for (const role of roles) {
		const ext = ir[role].$extensions[EXT];
		for (const cite of ext.inputs) {
			const key = cite.split("=", 1)[0];
			if (key in params) {
				links.push({ source: `param:${key}`, target: role });
				used.add(key);
			}
		}
		for (const dep of ext.roles ?? [])
			links.push({ source: dep, target: role });
	}
	const brand = colour("color.background.brand.bold");
	const nodes = Object.keys(params)
		.filter((k) => used.has(k))
		.map((k) => ({
			id: `param:${k}`,
			label: `${k} = ${params[k].value?.code ?? params[k].value}`,
			group: params[k].source === "stated" ? "stated" : "default",
			colour: params[k].source === "stated" ? brand : neutral,
		}));
	nodes.push(
		...roles.map((r) => ({
			id: r,
			label: r,
			group: "IR role",
			colour: colour(r),
		})),
	);
	/** @type {Dict} */ const groups = {};
	/** @type {{source:string,target:string}[]} */ const surfaceLinks = [];
	for (const key of keys.filter((k) => k.startsWith("surface."))) {
		const target = key.split(".").slice(0, 2).join(".");
		groups[target] = {
			id: target,
			label: target,
			group: "surface",
			colour: neutral,
		};
		for (const dep of ir[key].$extensions[EXT].roles ?? [])
			surfaceLinks.push({ source: dep, target });
	}
	const sources = [...new Set(surfaceLinks.map((l) => l.source))].sort(
		(a, b) => roles.indexOf(a) - roles.indexOf(b),
	);
	return {
		sankeys: [
			{
				title: "Seed → IR",
				caption:
					"Every parameter on the left is stated in the seed (brand colour) or a default (grey). Each band is one recorded input of an IR role; roles that read other roles chain right.",
				nodes,
				links,
			},
			{
				title: "IR → surfaces",
				caption:
					"Each IR role on the left feeds the surfaces the DTCG carries. One role often feeds several.",
				nodes: [
					...sources.map((r) => ({
						id: r,
						label: r,
						group: "IR role",
						colour: colour(r),
					})),
					...Object.values(groups),
				],
				links: surfaceLinks,
			},
		],
	};
}
/** Pure live generator: seed and stated edits in, resolved profiles and lineage out.
 * @param {Dict} seed @param {Dict} [context] */
export function generate(seed, context = {}) {
	const curator = new Curator(seed, context.stated),
		ir = curator.run();
	return {
		ir,
		tokens: build_tokens(ir, String(context.name ?? "live")),
		lineage: build_lineage(ir),
		resolved: curator.resolved,
	};
}
/** @param {Dict} args */
export const store_dir = (args) =>
	args.store ?? join(args.user ? homedir() : process.cwd(), resolver.STORE);
/** @param {string} store */
const folders = (store) => {
	try {
		return readdirSync(store, { withFileTypes: true })
			.filter((p) => p.isDirectory())
			.map((p) => p.name)
			.sort();
	} catch (error) {
		if (/** @type {NodeJS.ErrnoException} */ (error).code === "ENOENT")
			return [];
		throw error;
	}
};
/** @param {Dict} args */
export function profile_names(args) {
	const store = store_dir(args),
		names = args.name?.length
			? args.name
			: folders(store).filter((/** @type {string} */ p) =>
					["seed.json", "ir.json"].some((f) =>
						resolver.isFile(join(store, p, f)),
					),
				);
	if (!names.length)
		throw new Error(`error: no profiles under ${store}; create one with init`);
	return /** @type {string[]} */ (names);
}
export const examples = () =>
	Object.fromEntries(
		folders(EXAMPLES_DIR)
			.filter((p) => resolver.isFile(join(EXAMPLES_DIR, p, "seed.json")))
			.map((p) => [p, join(EXAMPLES_DIR, p, "seed.json")]),
	);
/** @param {string[]} argv */
export async function main(argv = process.argv.slice(2)) {
	const [cmd, ...rest] = argv;
	const { values, positionals } = parseArgs({
		args: rest,
		allowPositionals: true,
		options: {
			store: { type: "string" },
			user: { type: "boolean" },
			hue: { type: "string" },
			radius: { type: "string" },
			"radius-dark": { type: "string" },
			primary: { type: "string" },
			// Deprecated alias of --primary (DT-NAMES-1): `accent` is a hover tint in shadcn.
			accent: { type: "string" },
			example: { type: "string" },
			force: { type: "boolean" },
			help: { type: "boolean" },
			format: { type: "string", default: "both" },
		},
	});
	if (!cmd || cmd === "--help" || values.help) {
		console.log(
			"profiles.mjs init|curate|build|all|lineage|status|set-default [NAME...] [--store DIR|--user] [--format css|tokens|both]\ninit NAME --hue DEGREES|--primary HEX|--example NAME [--radius VALUE] [--radius-dark VALUE] [--force]",
		);
		return;
	}
	if (values.store && values.user) throw new Error("Choose --store or --user");
	if (!["css", "tokens", "both"].includes(values.format))
		throw new Error("Invalid output format");
	if (positionals.some((name) => !/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(name)))
		throw new Error("Invalid profile name");
	const args = { ...values, name: positionals },
		store = store_dir(args);
	if (cmd === "init" || cmd === "set-default") {
		if (positionals.length !== 1)
			throw new Error(`${cmd} requires one profile name`);
		const folder = join(store, positionals[0]);
		if (cmd === "set-default") {
			if (!resolver.isFile(join(folder, resolver.TOKENS_FILE)))
				throw new Error(
					`error: ${folder} has no ${resolver.TOKENS_FILE}; run build first`,
				);
			writeFileSync(join(store, resolver.DEFAULT_FILE), `${positionals[0]}\n`);
			return;
		}
		const path = join(folder, "seed.json");
		if (resolver.isFile(path) && !values.force)
			throw new Error(`error: ${path} exists; pass --force to replace it`);
		const primary = values.primary ?? values.accent;
		if (values.primary !== undefined && values.accent !== undefined)
			throw new Error("error: --accent is the old name of --primary; pass one");
		if (
			[values.hue, primary, values.example].filter((v) => v !== undefined)
				.length !== 1
		)
			throw new Error(
				"error: init needs --hue, --primary or --example (choose one)",
			);
		/** @type {Dict} */ let seed;
		if (values.example) {
			const known = examples();
			if (!(values.example in known))
				throw new Error(
					`error: unknown example '${values.example}'. Available: ${Object.keys(known).join(", ")}`,
				);
			seed = read_json(known[values.example]);
		} else if (values.hue !== undefined) {
			if (!Number.isFinite(Number(values.hue))) throw new Error("Invalid hue");
			seed = { "brand.hue": Number(values.hue) };
		} else {
			const [L, C, h] = exact_oklch(/** @type {string} */ (primary));
			seed = { "brand.hue": h, "brand.chroma": C, "brand.lightness": L };
		}
		if (values.radius !== undefined) seed.radius = values.radius;
		if (values["radius-dark"] !== undefined)
			seed["radius.dark"] = values["radius-dark"];
		resolve_params(seed);
		mkdirSync(folder, { recursive: true });
		write_json(path, seed);
		return;
	}
	if (cmd === "status") {
		console.log(
			`store    ${resolve(store)}\ndefault  ${resolver.default_profile_name(process.cwd(), homedir()) ?? "(none: consumers use their built-in themes)"}\nexamples ${Object.keys(examples()).join(", ")}`,
		);
		for (const name of folders(store).filter(
			(p) => !positionals.length || positionals.includes(p),
		)) {
			const files = ["seed.json", "ir.json", resolver.TOKENS_FILE].filter((f) =>
				resolver.isFile(join(store, name, f)),
			);
			const stale =
				files.includes("ir.json") &&
				files.includes(resolver.TOKENS_FILE) &&
				statSync(join(store, name, "ir.json")).mtimeMs >
					statSync(join(store, name, resolver.TOKENS_FILE)).mtimeMs;
			const scores = files.includes("ir.json")
				? (read_json(join(store, name, "ir.json")).$extensions?.[EXT]
						?.contrast ?? [])
				: [];
			console.log(
				`profile  ${name} ${files.join(", ") || "(empty)"}; contrast: ${scores.filter((/** @type {Dict} */ s) => s.verdict === "defect").length} defect, ${scores.filter((/** @type {Dict} */ s) => s.verdict === "choice").length} choice${stale ? " (ir.json is newer: rebuild)" : ""}`,
			);
		}
		return;
	}
	if (!["curate", "build", "all", "lineage"].includes(cmd))
		throw new Error(`Unknown command: ${cmd}`);
	const names = profile_names(args);
	if (cmd === "curate" || cmd === "all") {
		let defects = 0;
		for (const name of names) {
			const report = await curate_profile(join(store, name));
			console.log(`curated  ${name}`);
			for (const line of report.filter((l) => !l.startsWith("new")))
				console.log(`  ${line}`);
			defects += report.filter((l) => l.startsWith("defect")).length;
		}
		if (defects)
			throw new Error(
				`error: curation failed: ${defects} text pairing(s) below AA from defaults alone`,
			);
	}
	if (cmd === "build" || cmd === "all")
		for (const name of names)
			console.log(
				`built    ${name} ${await build_profile(join(store, name), values.format)}`,
			);
	if (cmd === "lineage")
		for (const name of names) {
			const path = join(store, name, "ir.json");
			if (!resolver.isFile(path))
				throw new Error(`error: ${path} not found; run curate first`);
			const folder = join(LINEAGE_DIR, name);
			mkdirSync(folder, { recursive: true });
			write_json(join(folder, "lineage.json"), build_lineage(read_json(path)));
			console.log(`lineage  ${name} ${join(folder, "lineage.json")}`);
		}
}
if (
	process.argv[1] &&
	resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
	main().catch((error) => {
		console.error(error instanceof Error ? error.message : String(error));
		process.exitCode = 1;
	});
}
