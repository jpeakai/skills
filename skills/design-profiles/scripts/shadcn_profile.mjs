import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs, isDeepStrictEqual } from "node:util";
import * as p from "./profiles.mjs";

/** @typedef {Record<string, any>} Dict */
export const GOLDEN_ANGLE = p.GOLDEN_ANGLE;
export const ROLE_VARIABLES = {
	"color.surface": "background",
	"color.surface.sunken": "muted",
	"color.surface.raised": "card",
	"color.text": "foreground",
	"color.text.subtle": "muted-foreground",
	"color.text.subtlest": "muted-foreground",
	"color.background.brand.bold": "primary",
	"color.text.inverse": "primary-foreground",
	"color.border": "border",
	"color.border.brand": "primary",
	"color.border.focused": "ring",
	"color.border.selected": "ring",
	"color.background.selected": "accent",
	"color.text.selected": "accent-foreground",
};
/** @param {string} role */
export function padded_role(role) {
	return role.replace(
		/^(color\.chart\.(?:categorical|palettes)\.)(\d+)(?=\.|$)/,
		(_, prefix, index) => prefix + String(Number(index)).padStart(2, "0"),
	);
}
/** @param {Dict} ir @returns {Dict} */
export function normalise_chart_roles(ir) {
	/** @type {Dict} */ const result = {};
	for (const [role, value] of Object.entries(ir)) {
		const node = structuredClone(value),
			ext = node.$extensions?.[p.EXT] ?? {};
		if (!role.startsWith("$")) {
			if (ext.alias) ext.alias = padded_role(ext.alias);
			if (ext.roles) ext.roles = ext.roles.map(padded_role);
		}
		const target = padded_role(role);
		if (target in result && !isDeepStrictEqual(result[target], node))
			throw new Error(`Conflicting chart roles for ${target}`);
		result[target] = node;
	}
	for (const report of Object.values(
		result.$extensions?.[p.EXT]?.chartContrast ?? {},
	)) {
		const r = /** @type {Dict} */ (report);
		if (r.sequentialAdjacent)
			r.sequentialAdjacent = Object.fromEntries(
				Object.entries(r.sequentialAdjacent).map(([i, v]) => [
					String(Number(i)).padStart(2, "0"),
					v,
				]),
			);
	}
	return result;
}
/** @param {string} value @returns {[number[],number]} */
export function colour(value) {
	const match = /^oklch\(([^()]+)\)$/.exec(value);
	if (!match) throw new Error(`Expected a registry OKLCH colour, got ${value}`);
	const [coords, ...opacity] = match[1].split("/"),
		parts = coords.trim().split(/\s+/);
	if (parts.length !== 3 || opacity.length > 1)
		throw new Error(`Invalid OKLCH colour: ${value}`);
	const L =
			Number(parts[0].replace(/%$/, "")) / (parts[0].endsWith("%") ? 100 : 1),
		C = Number(parts[1]),
		h = Number(parts[2]),
		alphaText = opacity[0]?.trim() ?? "1";
	const alpha =
		Number(alphaText.replace(/%$/, "")) / (alphaText.endsWith("%") ? 100 : 1);
	if (
		![L, C, h, alpha].every(Number.isFinite) ||
		L < 0 ||
		L > 1 ||
		C < 0 ||
		alpha < 0 ||
		alpha > 1 ||
		!alphaText
	)
		throw new Error(`Invalid OKLCH colour: ${value}`);
	return [[L, C, p.mod360(h)], alpha];
}
/** @param {string} value */
export function hex_value(value) {
	const [lch, alpha] = colour(value);
	return (
		p.hex_of(lch) +
		(alpha < 1
			? p
					.round(alpha * 255)
					.toString(16)
					.padStart(2, "0")
			: "")
	);
}
/** @param {number[]} lch */
export function fit_srgb([L, C, h]) {
	return p.fit_srgb([L, C, h]);
}
/** @param {Record<string,string>} values */
export function expanded_chart(values) {
	const template = Array.from(
			{ length: 5 },
			(_, i) => colour(values[`chart-${i + 1}`])[0],
		),
		root = template[0];
	const offsets = template.map(([L, C, h]) => [
		L - root[0],
		C - root[1],
		p.mod360(h - root[2] + 180) - 180,
	]);
	return Array.from({ length: 10 }, (_, i) =>
		offsets.map(([dL, dC, dh]) =>
			fit_srgb([
				p.round(root[0] + dL, 6),
				Math.max(0, p.round(root[1] + dC, 6)),
				p.round(p.mod360(root[2] + i * GOLDEN_ANGLE + dh), 6),
			]),
		),
	);
}
/** @param {Dict} snapshot @returns {[Dict,string[]]} */
export function font_metadata(snapshot) {
	/** @type {Dict} */ const families = {};
	/** @type {string[]} */ const urls = [];
	for (const item of snapshot.fonts) {
		const font = item.font,
			dependency = font.dependency;
		if (!/^@fontsource(?:-variable)?\/[a-z0-9-]+$/.test(dependency))
			throw new Error(`Unsupported font dependency: ${dependency}`);
		families[font.variable] = font.family;
		const url = `https://cdn.jsdelivr.net/npm/${dependency}/index.css`;
		if (!urls.includes(url)) urls.push(url);
	}
	const body =
		families["--font-sans"] ||
		families["--font-mono"] ||
		families["--font-serif"];
	if (!body) throw new Error("Preset is missing its body font metadata");
	if (
		snapshot.config.fontHeading !== "inherit" &&
		!("--font-heading" in families)
	)
		throw new Error("Preset is missing its heading font metadata");
	return [
		{
			"font.body": body,
			"font.display": families["--font-heading"] ?? body,
			"font.mono": families["--font-mono"] ?? p.SYSTEM_MONO,
		},
		urls,
	];
}

export class PresetCurator extends p.Curator {
	/** @param {Dict} snapshot @param {Dict} [stated] */
	constructor(snapshot, stated = {}) {
		const variables = snapshot.cssVars;
		const chartRamps = Object.fromEntries(
			p.MODES.map((mode) => [mode, expanded_chart(variables[mode])]),
		);
		const [fontParams, stylesheets] = font_metadata(snapshot);
		/** @type {Dict} */ const imported = {};
		for (const mode of p.MODES) {
			for (const [name, value] of Object.entries(variables[mode]))
				if (name !== "radius") {
					imported[`color.shadcn.${name}`] ??= {};
					imported[`color.shadcn.${name}`][mode] = value;
				}
			for (const [role, name] of Object.entries(ROLE_VARIABLES)) {
				imported[role] ??= {};
				imported[role][mode] = variables[mode][name];
			}
		}
		/** @type {Dict} */ const pinned = Object.fromEntries(
			Object.entries(imported).map(([role, modes]) => [
				role,
				Object.fromEntries(
					Object.entries(modes).map(([m, v]) => [
						m,
						hex_value(/** @type {string} */ (v)),
					]),
				),
			]),
		);
		for (const [role, modes] of Object.entries(stated)) {
			pinned[role] ??= {};
			Object.assign(pinned[role], modes);
		}
		const [light] = colour(variables.light.primary),
			[dark] = colour(variables.dark.primary);
		super(
			{
				"brand.lightness": light[0],
				"brand.chroma": light[1],
				"brand.hue": light[2],
				"brand.dark.lightness": dark[0],
				"brand.dark.chroma": dark[1],
				"brand.dark.hue": dark[2],
				"L-light-bg": colour(variables.light.background)[0][0],
				"L-dark-bg": colour(variables.dark.background)[0][0],
				"walk.slots": 10,
				"walk.angle": GOLDEN_ANGLE,
				...fontParams,
			},
			pinned,
		);
		this.snapshot = snapshot;
		this.variables = variables;
		this.hand_edits = stated;
		this.chart_ramps = chartRamps;
		this.stylesheets = stylesheets;
		this.imported = imported;
	}
	/** @param {number} index */
	categorical_role(index) {
		return `color.chart.categorical.${String(index).padStart(2, "0")}`;
	}
	walk() {
		for (let i = 0; i < 10; i++) {
			for (let j = 0; j < 5; j++) {
				const lch = Object.fromEntries(
					p.MODES.map((m) => [m, this.chart_ramps[m][i][j]]),
				);
				this.put(
					`color.chart.palettes.${String(i + 1).padStart(2, "0")}.${j + 1}`,
					Object.fromEntries(p.MODES.map((m) => [m, p.hex_of(lch[m])])),
					"chart-1 golden-angle root plus the preset ramp's L/C/h offsets; chroma-only sRGB mapping",
					[`preset=${this.snapshot.code} [stated]`],
					lch,
				);
			}
			this.same(
				this.categorical_role(i + 1),
				`color.chart.palettes.${String(i + 1).padStart(2, "0")}.1`,
			);
		}
	}
	ramps() {
		super.ramps();
		for (let i = 1; i <= 5; i++)
			this.same(`color.chart.sequential.${i}`, `color.chart.palettes.01.${i}`);
	}
	// The imported ramp was already expanded in walk(); retain its exact offsets.
	palettes() {}
	fonts() {
		super.fonts();
		/** @type {Dict} */ const reverse = {};
		for (const [role, variable] of Object.entries(ROLE_VARIABLES))
			reverse[variable] ??= role;
		for (const name of Object.keys(this.variables.light)) {
			if (name === "radius") continue;
			const role = `color.shadcn.${name}`;
			if (name in reverse) {
				if (!(role in this.hand_edits)) delete this.stated[role];
				this.same(role, reverse[name]);
			} else
				this.put(
					role,
					Object.fromEntries(
						p.MODES.map((m) => [m, hex_value(this.variables[m][name])]),
					),
					"registry colour",
					[`preset=${this.snapshot.code} [stated]`],
				);
		}
	}
	dimensions() {
		const radius = Object.fromEntries(
			p.MODES.map((mode) => {
				const text =
						this.variables[mode].radius ?? this.variables.light.radius ?? "0",
					parsed = p.parse_radius(text);
				return [mode, parsed];
			}),
		);
		this.put("dimension.radius", radius, "registry radius", [
			`preset=${this.snapshot.code} [stated]`,
		]);
	}
	run() {
		const ir = super.run();
		for (const [role, modes] of Object.entries(this.imported))
			for (const [mode, raw] of Object.entries(modes)) {
				const text = /** @type {string} */ (raw);
				if (ir[role][mode] !== hex_value(text)) continue;
				const [lch, alpha] = colour(text),
					ext = ir[role].$extensions[p.EXT];
				ext.cssValue ??= {};
				ext.cssDerived ??= {};
				ext.dtcgValue ??= {};
				ext.cssValue[mode] = text;
				ext.cssDerived[mode] = ir[role][mode];
				ext.dtcgValue[mode] = {
					colorSpace: "oklch",
					components: lch,
					hex: p.hex_of(lch),
					alpha,
				};
			}
		for (const [role, node] of Object.entries(ir))
			if (role.startsWith("color.chart.palettes.")) {
				const [i, j] = role
					.split(".")
					.slice(-2)
					.map((x) => Number(x) - 1);
				for (const mode of p.MODES) {
					const lch = this.chart_ramps[mode][i][j];
					if (node[mode] === p.hex_of(lch)) {
						node.$extensions[p.EXT].oklch ??= {};
						node.$extensions[p.EXT].oklch[mode] = lch;
					}
				}
			}
		const meta = ir.$extensions[p.EXT];
		meta.params.preset = { value: this.snapshot, source: "stated" };
		meta.preset = { code: this.snapshot.code, config: this.snapshot.config };
		meta.fontStylesheets = this.stylesheets;
		meta.chartContrast = Object.fromEntries(
			p.MODES.map((mode) => [
				mode,
				{
					categoricalAdjacent: Array.from({ length: 9 }, (_, i) =>
						p.round(
							p.contrast(
								ir[this.categorical_role(i + 1)][mode],
								ir[this.categorical_role(i + 2)][mode],
							),
							4,
						),
					),
					sequentialAdjacent: Object.fromEntries(
						Array.from({ length: 10 }, (_, i) => {
							const index = String(i + 1).padStart(2, "0");
							return [
								index,
								Array.from({ length: 4 }, (_, j) =>
									p.round(
										p.contrast(
											ir[`color.chart.palettes.${index}.${j + 1}`][mode],
											ir[`color.chart.palettes.${index}.${j + 2}`][mode],
										),
										4,
									),
								),
							];
						}),
					),
				},
			]),
		);
		return ir;
	}
}
/** @param {Dict} node @param {string} mode @param {Dict} [ir] */
export function css_colour(node, mode, ir = {}) {
	const seen = new Set();
	while (true) {
		const ext = node.$extensions?.[p.EXT] ?? {},
			source = ir[ext.alias];
		if (
			!source ||
			seen.has(ext.alias) ||
			node[mode] !== ext.derived?.[mode] ||
			node[mode] !== source[mode]
		)
			break;
		seen.add(ext.alias);
		node = source;
	}
	const ext = node.$extensions?.[p.EXT] ?? {};
	if (node[mode] === ext.cssDerived?.[mode]) return String(ext.cssValue[mode]);
	const lch = ext.oklch?.[mode];
	if (lch && p.hex_of(lch) === node[mode]) return `oklch(${lch.join(" ")})`;
	return String(node[mode]);
}
/** @param {Dict} ir */
export function build_css(ir) {
	const meta = ir.$extensions[p.EXT],
		stylesheet = meta.params?.["font.stylesheet"]?.value;
	const urls = meta.fontStylesheets ?? (stylesheet ? [stylesheet] : []);
	const blocks = urls.map(
		(/** @type {string} */ url) => `@import url(${JSON.stringify(url)});`,
	);
	for (const [mode, selector] of [
		["light", ":root"],
		["dark", ".dark"],
	]) {
		/** @type {Dict} */ const variables = Object.fromEntries(
			Object.entries(ir)
				.filter(([r]) => r.startsWith("color.shadcn."))
				.map(([r, node]) => [
					r.slice("color.shadcn.".length),
					css_colour(node, mode),
				]),
		);
		for (const [role, node] of Object.entries(ir))
			if (role.startsWith("surface.shadcn.")) {
				const key = role.slice("surface.shadcn.".length);
				variables[key] =
					key === "radius"
						? `${node[mode].value}${node[mode].unit}`
						: css_colour(node, mode, ir);
			}
		if (!("radius" in variables) && ir["dimension.radius"]) {
			const r = ir["dimension.radius"][mode];
			variables.radius = `${r.value}${r.unit}`;
		}
		for (const [variable, role] of [
			["font-sans", "body"],
			["font-heading", "display"],
			["font-mono", "mono"],
		])
			if (!(variable in variables))
				variables[variable] = ir[`font.family.${role}`][mode];
		for (const name of [
			...Object.keys(p.SHADCN_VARIABLES),
			"border",
			"sidebar-border",
			"radius",
			"font-sans",
			"font-heading",
			"font-mono",
		])
			if (!(name in variables))
				throw new Error(
					`Profile lacks shadcn variable --${name}; run curate first`,
				);
		for (const [role, node] of Object.entries(ir)) {
			if (role.startsWith("surface.css.")) {
				const key = role.slice("surface.css.".length);
				variables[key in variables ? `profile-${key}` : key] = css_colour(
					node,
					mode,
				);
			}
			if (role.startsWith("color.chart.categorical."))
				variables[`categorical-${role.split(".").at(-1)}`] = css_colour(
					node,
					mode,
				);
			if (role.startsWith("color.chart.palettes."))
				variables[`palette-${role.split(".").slice(-2).join("-")}`] =
					css_colour(node, mode);
		}
		blocks.push(
			`${selector} {\n${Object.entries(variables)
				.map(([k, v]) => `  --${k}: ${v};`)
				.join("\n")}\n}`,
		);
	}
	if (ir["color.chart.palettes.01.1"])
		for (
			let i = 1;
			i <= Number(meta.params?.["walk.slots"]?.value ?? 10);
			i++
		) {
			const index = String(i).padStart(2, "0");
			blocks.push(
				`[data-chart-palette="${index}"] {\n${Array.from({ length: 5 }, (_, j) => `  --chart-${j + 1}: var(--palette-${index}-${j + 1});`).join("\n")}\n}`,
			);
		}
	blocks.push(
		"body { font-family: var(--font-sans); }",
		"h1, h2, h3, h4, h5, h6 { font-family: var(--font-heading); }",
	);
	return `${blocks.join("\n\n")}\n`;
}
/** @param {Dict} snapshot @param {{name:string,store?:string,format?:string}} options */
export async function savePreset(
	snapshot,
	{ name, store = ".design-profiles", format = "both" },
) {
	if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(name))
		throw new Error("Invalid profile name");
	if (!["css", "tokens", "both"].includes(format))
		throw new Error("Invalid output format");
	new PresetCurator(snapshot).run();
	const folder = join(store, name),
		seed = { preset: snapshot },
		path = join(folder, "seed.json");
	if (
		existsSync(folder) &&
		(!existsSync(path) || !isDeepStrictEqual(p.read_json(path), seed))
	)
		throw new Error("Profile exists with another seed; choose another name");
	mkdirSync(folder, { recursive: true });
	p.write_json(path, seed);
	const report = await p.curate_profile(folder),
		defects = report.filter((line) => line.startsWith("defect"));
	if (defects.length) throw new Error(defects.join("\n"));
	const out = await p.build_profile(folder, format);
	console.log(`Built ${name}: ${folder} (${format}; 10 hues, 5 shades each)`);
	return out;
}
/** @param {string[]} [argv] @param {Dict} [snapshot] */
export async function main(argv = process.argv.slice(2), snapshot) {
	const { values } = parseArgs({
		args: argv,
		options: {
			name: { type: "string" },
			store: { type: "string", default: ".design-profiles" },
			format: { type: "string", default: "both" },
			help: { type: "boolean" },
		},
	});
	if (values.help) {
		console.log(
			"shadcn_profile.mjs --name NAME [--store DIR] [--format css|tokens|both] < snapshot.json",
		);
		return;
	}
	if (!values.name) throw new Error("Supply --name");
	const input = snapshot ?? JSON.parse(readFileSync(0, "utf8"));
	await savePreset(input, {
		name: values.name,
		store: values.store,
		format: values.format,
	});
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
