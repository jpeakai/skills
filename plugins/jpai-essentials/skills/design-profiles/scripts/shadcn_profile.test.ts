import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import Ajv from "ajv";
import * as p from "./profiles.mjs";
import * as r from "./profile_resolver.mjs";
import * as s from "./shadcn_profile.mjs";
const snapshot = () =>
	p.read_json(join(import.meta.dir, "testdata/shadcn-preset.json"));

test("preset exports preserve registry values, fonts, radius and lineage", () => {
	const ir = new s.PresetCurator(snapshot()).run(),
		doc = p.build_tokens(ir, "demo");
	const schema = p.read_json(
		join(import.meta.dir, "schemas/2025.10/resolver.json"),
	);
	expect(
		new Ajv({ strict: false, validateFormats: false }).validate(schema, doc),
	).toBe(true);
	const lineage = p.build_lineage(ir);
	expect(lineage.sankeys[0].nodes).toContainEqual(
		expect.objectContaining({
			id: "param:preset",
			label: "preset = b5cR4pgAc",
		}),
	);
	expect(lineage.sankeys[0].links).toContainEqual({
		source: "param:preset",
		target: "color.chart.palettes.01.1",
	});
	expect(lineage.sankeys[1].links).toContainEqual({
		source: "color.shadcn.primary",
		target: "surface.shadcn",
	});
	const css = s.build_css(ir);
	for (const [mode, selector] of [
		["light", ":root"],
		["dark", ".dark"],
	]) {
		const block = css.split(`${selector} {`)[1].split("}")[0];
		const vars = Object.fromEntries(
			[...block.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2]]),
		);
		for (const [key, value] of Object.entries(snapshot().cssVars[mode]))
			expect(vars[key]).toBe(String(value));
	}
	expect(css).toContain("--font-sans: 'Inter Variable', sans-serif;");
	expect(css).toContain("@fontsource-variable/inter/index.css");
	expect(css).toContain("--chart-5: var(--palette-10-5)");
	expect(r.read_tokens(doc)["dimension.radius"]).toEqual({
		value: 0.45,
		unit: "rem",
	});
	expect(
		doc.modifiers.mode.contexts.light[0].color.background.brand.bold.$value
			.components,
	).toEqual([0.491, 0.27, 292.581]);
	expect(
		r.extension(doc).chartContrast.light.sequentialAdjacent["01"].length,
	).toBe(4);
});
test("golden walk preserves ramp offsets and chroma-only gamut mapping", () => {
	const ramps = s.expanded_chart(snapshot().cssVars.light);
	expect(ramps.length).toBe(10);
	expect(ramps.map((r) => p.hex_of(r[0]))).toEqual([
		"#46ecd5",
		"#efb8ff",
		"#eacf5a",
		"#96d9ff",
		"#ffbac2",
		"#8ce89c",
		"#cbc9ff",
		"#ffc188",
		"#30eaf4",
		"#ffb4e8",
	]);
	expect(ramps[0][0]).toEqual([0.855, 0.138, 181.071]);
	expect(ramps[7].map((v) => v[0])).toEqual([0.855, 0.704, 0.6, 0.511, 0.437]);
	expect(ramps[1][1][2]).toBeCloseTo(320.010764, 6);
	expect(new Set(ramps.flat().map(p.hex_of)).size).toBe(50);
	expect(
		ramps
			.flat()
			.flatMap(p.lin_rgb)
			.every((c) => c >= -1e-9 && c <= 1 + 1e-9),
	).toBe(true);
});
test("body/heading fonts, different dark charts and validation errors", () => {
	const snap = snapshot();
	snap.config.fontHeading = "playfair-display";
	expect(() => new s.PresetCurator(snap)).toThrow("heading font");
	snap.fonts.push({
		font: {
			family: "'Playfair Display Variable', serif",
			variable: "--font-heading",
			dependency: "@fontsource-variable/playfair-display",
		},
	});
	snap.cssVars.dark["chart-1"] = "oklch(0.8 0.1 300)";
	const ir = new s.PresetCurator(snap).run();
	expect(ir["font.family.display"].light).toBe(
		"'Playfair Display Variable', serif",
	);
	expect(s.build_css(ir)).toContain("playfair-display/index.css");
	expect(ir["color.chart.palettes.01.1"].dark).not.toBe(
		ir["color.chart.palettes.01.1"].light,
	);
	for (const value of [
		"red",
		"oklch(0.5 0.1)",
		"oklch(2 0.1 40)",
		"oklch(nan 0.1 40)",
		"oklch(.5 .1 40 / 1 / 1)",
		"oklch(.5 .1 40 / )",
	])
		expect(() => s.colour(value)).toThrow();
	expect(s.colour("oklch(50% 0.1 360 / 10%)")).toEqual([[0.5, 0.1, 0], 0.1]);
	expect(s.css_colour({ light: "#ffffff" }, "light")).toBe("#ffffff");
	const bad = snapshot();
	bad.fonts[0].font.dependency = "invalid";
	expect(() => new s.PresetCurator(bad)).toThrow("Unsupported font");
	bad.fonts = [];
	expect(() => new s.PresetCurator(bad)).toThrow("body font");
	bad.fonts = snapshot().fonts;
	bad.cssVars.light.radius = "auto";
	expect(() => new s.PresetCurator(bad).run()).toThrow("Unsupported radius");
});
test("offline rebuild preserves edits and normalises old numbered aliases", async () => {
	const store = mkdtempSync(join(tmpdir(), "preset-edits-"));
	try {
		await s.savePreset(snapshot(), { name: "demo", store });
		const folder = join(store, "demo"),
			path = join(folder, "ir.json"),
			first = readFileSync(path, "utf8");
		await p.curate_profile(folder);
		expect(readFileSync(path, "utf8")).toBe(first);
		const ir = p.read_json(path);
		ir["color.background.brand.bold"].light = "#123456";
		ir["color.shadcn.chart-1"].dark = "#abcdef";
		ir["color.chart.palettes.1.2"] = ir["color.chart.palettes.01.2"];
		delete ir["color.chart.palettes.01.2"];
		ir["color.chart.palettes.1.2"].light = "#654321";
		ir["color.chart.categorical.1"] = ir["color.chart.categorical.01"];
		delete ir["color.chart.categorical.01"];
		const ext = ir["color.chart.sequential.2"].$extensions[p.EXT];
		ext.alias = "color.chart.palettes.1.2";
		ext.roles = [ext.alias];
		p.write_json(path, ir);
		await p.build_profile(folder);
		await p.curate_profile(folder);
		await p.build_profile(folder);
		const css = readFileSync(join(folder, "theme.css"), "utf8");
		const primary = /--primary: ([^;]+);/.exec(css)?.[1];
		const darkChart = /--chart-1: ([^;]+);/.exec(css.split(".dark {")[1])?.[1];
		expect(s.hex_value(primary ?? "")).toBe("#123456");
		expect(s.hex_value(darkChart ?? "")).toBe("#abcdef");
		expect(
			r.read_tokens(p.read_json(join(folder, "design-tokens.json")))[
				"color.chart.palettes.01.2"
			],
		).toBe("#654321");
		expect(() =>
			s.normalise_chart_roles({
				"color.chart.categorical.1": { light: "#123456" },
				"color.chart.categorical.01": { light: "#abcdef" },
			}),
		).toThrow("Conflicting chart roles");
		const other = snapshot();
		other.code = "another";
		await expect(s.savePreset(other, { name: "demo", store })).rejects.toThrow(
			"another seed",
		);
		await expect(
			s.savePreset(snapshot(), { name: "../bad", store }),
		).rejects.toThrow("Invalid profile");
		await expect(
			s.savePreset(snapshot(), { name: "bad", store, format: "bad" }),
		).rejects.toThrow("Invalid output");
		expect(existsSync(join(store, "bad"))).toBe(false);
	} finally {
		rmSync(store, { recursive: true });
	}
});
test("offline snapshot CLI and format selection run under Node and Bun with no Python", () => {
	const store = mkdtempSync(join(tmpdir(), "preset-runtimes-"));
	try {
		for (const runtime of ["node", "bun"])
			for (const format of ["css", "tokens", "both"]) {
				const name = `${runtime}-${format}`,
					binary = execFileSync("which", [runtime], {
						encoding: "utf8",
					}).trim();
				const script = resolve(import.meta.dir, "shadcn_profile.mjs"),
					env = { ...process.env, PATH: "/nonexistent" };
				execFileSync(
					binary,
					[script, "--name", name, "--store", store, "--format", format],
					{ env, input: JSON.stringify(snapshot()) },
				);
				expect(existsSync(join(store, name, "theme.css"))).toBe(
					format !== "tokens",
				);
				expect(existsSync(join(store, name, "design-tokens.json"))).toBe(
					format !== "css",
				);
				expect(
					execFileSync(binary, [script, "--help"], { env, encoding: "utf8" }),
				).toContain("snapshot.json");
				expect(() =>
					execFileSync(binary, [script], { env, input: "{}", stdio: "pipe" }),
				).toThrow();
			}
	} finally {
		rmSync(store, { recursive: true });
	}
});
