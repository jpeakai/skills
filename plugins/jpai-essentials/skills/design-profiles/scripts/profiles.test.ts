import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import {
	mkdtempSync,
	mkdirSync,
	readFileSync,
	rmSync,
	unlinkSync,
	utimesSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import Ajv from "ajv";
import * as p from "./profiles.mjs";
import * as r from "./profile_resolver.mjs";

const baseline = p.read_json(
	new URL("./testdata/curation-baseline.json", import.meta.url).pathname,
);
// Expanded charts and shadcn projections are new; retain the baseline for existing roles.
const withoutCharts = (flat: Record<string, unknown>) =>
	Object.fromEntries(
		Object.entries(flat).filter(
			([key]) =>
				!/^surface\.shadcn\.|^color\.chart\.|^surface\.plotly\.(?:colorway|sequential)\.|^surface\.drawio\.stencil\.|^surface\.mermaid\.(?:cScale|pie\d|pieSectionTextColor|git\d|gitBranchLabel)/.test(
					key,
				),
		),
	);
const schema = p.read_json(
	new URL("./schemas/2025.10/resolver.json", import.meta.url).pathname,
);
const validate = new Ajv({ strict: false, validateFormats: false }).compile(
	schema,
);
const root = () => mkdtempSync(join(tmpdir(), "curation-"));
const seeded = (
	store: string,
	name = "p",
	seed: Record<string, unknown> = { "brand.hue": 200 },
) => {
	const f = join(store, name);
	mkdirSync(f, { recursive: true });
	p.write_json(join(f, "seed.json"), seed);
	return f;
};

for (const [name, fixture] of Object.entries(baseline) as [
	string,
	{
		seed: Record<string, unknown>;
		flat: Record<string, ReturnType<typeof r.read_tokens>>;
		scores: ReturnType<typeof p.score_contrast>;
	},
][]) {
	if (name === "preset") continue;
	test(`preserves non-chart baseline tokens and contrast scores: ${name}`, () => {
		const ir = new p.Curator(fixture.seed).run(),
			tokens = p.build_tokens(ir, name);
		expect(validate(tokens)).toBe(true);
		for (const mode of p.MODES)
			expect(withoutCharts(r.read_tokens(tokens, mode))).toEqual(
				withoutCharts({
					...fixture.flat[mode],
					"dimension.radius": { value: 12, unit: "px" },
				}),
			);
		expect(p.score_contrast(ir)).toEqual(fixture.scores);
	});
}
test("known colour maths, gamut boundaries, font stacks and invalid inputs", () => {
	expect(p.contrast("#000000", "#ffffff")).toBe(21);
	expect(p.contrast("#ffc000", "#ffffff")).toBeCloseTo(1.64, 2);
	expect(p.exact_oklch("#5c4295")).toEqual([0.45, 0.131, 295.044]);
	expect(p.composite("#00000080", "#ffffff")).toBe("#7f7f7f");
	expect(p.rgba("#0102037f")).toEqual([1, 2, 3, 127]);
	expect(p.best_text("#ffffff")).toBe("#000000");
	expect(p.best_text("#000000")).toBe("#ffffff");
	expect(p.max_chroma(0, 120)).toBe(0);
	expect(p.max_chroma(1, 120)).toBe(0);
	expect(p.font_families("'Fira Sans', \"A B\", serif")).toEqual([
		"Fira Sans",
		"A B",
		"serif",
	]);
	expect(p.round(2.5)).toBe(2);
	expect(p.round(3.5)).toBe(4);
	expect(() => p.rgb8("red")).toThrow("Invalid hex");
	expect(() => p.resolve_params({})).toThrow("must state");
	expect(() => p.resolve_params({ "brand.hue": 1, nope: 2 })).toThrow(
		"unknown seed",
	);
	expect(() =>
		p.resolve_params({ "brand.hue": 1, "mode.default": "sepia" }),
	).toThrow("mode.default");
	expect(p.resolve_params({ "brand.hue": 10 })["brand.hue"]).toEqual([
		10,
		"stated",
	]);
	expect(p.resolve_params({ "brand.hue": 10 })["L-dark-bg"][1]).toStartWith(
		"default (DT-REF-1",
	);
	expect(() =>
		new p.Curator({ "brand.hue": 10 }).solve(10, 0.1, 0.5, () => false, "test"),
	).toThrow("unsolvable");
});

test("every example exports a superset of the reference shadcn variables", async () => {
	const { build_css, hex_value } = await import("./shadcn_profile.mjs");
	const reference = p.read_json(
		join(import.meta.dir, "testdata/shadcn-preset.json"),
	);
	for (const [name, path] of Object.entries(p.examples())) {
		const ir = new p.Curator(p.read_json(path)).run(),
			css = build_css(ir),
			tokens = p.build_tokens(ir, name);
		for (const [mode, selector] of [
			["light", ":root"],
			["dark", ".dark"],
		]) {
			const block = css.split(`${selector} {`)[1].split("}")[0],
				entries = [...block.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [
					m[1],
					m[2],
				]);
			const vars = Object.fromEntries(entries);
			expect(entries.length).toBe(Object.keys(vars).length);
			for (const key of Object.keys(reference.cssVars.light))
				expect(vars[key]).toBeDefined();
			const flat = r.read_tokens(tokens, mode);
			expect(hex_value(vars.primary)).toBe(flat["color.background.brand.bold"]);
			expect(hex_value(vars["profile-accent"])).toBe(
				flat["color.background.brand.bold"],
			);
			expect(hex_value(vars.accent)).toBe(
				flat["color.background.selected.hovered"],
			);
			expect(hex_value(vars["accent-foreground"])).toBe(
				flat["color.text.selected"],
			);
			expect(hex_value(vars["chart-5"])).toBe(
				flat["color.chart.palettes.01.5"],
			);
			expect(p.font_families(vars["font-sans"])).toEqual(
				p.font_families(flat["font.family.body"]),
			);
			expect(flat["surface.shadcn.font-sans"]).toBe(flat["font.family.body"]);
			expect(flat["surface.shadcn.radius"]).toEqual(flat["dimension.radius"]);
			expect(
				p.contrast(
					hex_value(vars.destructive),
					hex_value(vars["destructive-foreground"]),
				),
			).toBeGreaterThanOrEqual(4.5);
		}
		const lineage = p.build_lineage(ir).sankeys[1];
		for (const source of [
			"color.background.brand.bold",
			"color.chart.sequential.1",
			"font.family.body",
			"dimension.radius",
		])
			expect(lineage.links).toContainEqual({
				source,
				target: "surface.shadcn",
			});
	}
});

test("shadcn projection edits survive rebuilds and remain traceable", async () => {
	const { build_css, hex_value } = await import("./shadcn_profile.mjs");
	const store = root();
	try {
		const folder = seeded(store);
		await p.curate_profile(folder);
		const path = join(folder, "ir.json"),
			ir = p.read_json(path);
		ir["surface.shadcn.primary"].light = "#123456";
		ir["surface.shadcn.font-sans"].light = "'Example Serif', serif";
		ir["surface.shadcn.radius"].light = { value: 0.7, unit: "rem" };
		p.write_json(path, ir);
		await p.curate_profile(folder);
		const after = p.read_json(path),
			css = build_css(after),
			doc = p.build_tokens(after, "p"),
			flat = r.read_tokens(doc, "light");
		const block = css.split(":root {")[1].split("}")[0],
			vars = Object.fromEntries(
				[...block.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2]]),
			);
		expect(hex_value(vars.primary)).toBe("#123456");
		expect(vars.radius).toBe("0.7rem");
		expect(vars["font-sans"]).toBe("'Example Serif', serif");
		expect(flat["surface.shadcn.font-sans"]).toBe("'Example Serif', serif");
		expect(flat["surface.shadcn.radius"]).toEqual({ value: 0.7, unit: "rem" });
		delete after["surface.shadcn.background"];
		expect(() => build_css(after)).toThrow("run curate first");
	} finally {
		rmSync(store, { recursive: true });
	}
});

test("CSS keeps OKLCH for the three previously rounded-to-hex colours", async () => {
	const { build_css } = await import("./shadcn_profile.mjs");
	const curator = new p.Curator({ "brand.hue": 295.044 });
	curator.run();
	curator.put(
		"color.chart.categorical.08",
		{ light: "#106355", dark: "#6fd3bd" },
		"precision regression",
		[],
		{
			light: [0.45, 0.07793085575103761, 177.544],
			dark: [0.801, 0.09992572665214539, 177.544],
		},
	);
	curator.put(
		"color.chart.categorical.10",
		{ light: "#64541a", dark: "#d5bd70" },
		"precision regression",
		[],
		{
			light: [0.45, 0.07793085575103761, 92.544],
			dark: [0.801, 0.09992572665214539, 92.544],
		},
	);
	const css = build_css({
		$extensions: { [p.EXT]: { params: {} } },
		...curator.ir,
	});
	for (const [mode, selector] of [
		["light", ":root"],
		["dark", ".dark"],
	]) {
		const block = css.split(`${selector} {`)[1].split("}")[0];
		for (const index of ["08", "10"]) {
			const value = new RegExp(
				`--categorical-${index}: oklch\\(([^)]+)\\);`,
			).exec(block)?.[1];
			expect(value).toBeDefined();
			expect(p.hex_of((value ?? "").split(" ").map(Number))).toBe(
				curator.val(`color.chart.categorical.${index}`, mode),
			);
		}
	}
});

test("all examples have ten categorical roots and five shades per root in each mode", async () => {
	const { build_css } = await import("./shadcn_profile.mjs");
	for (const [name, path] of Object.entries(p.examples())) {
		const ir = new p.Curator(p.read_json(path)).run(),
			doc = p.build_tokens(ir, name),
			css = build_css(ir);
		for (const mode of p.MODES) {
			const flat = r.read_tokens(doc, mode);
			expect(r.series(flat, "color.chart.categorical").length).toBe(10);
			expect(Object.keys(r.group(flat, "color.chart.palettes")).length).toBe(
				50,
			);
			for (let i = 1; i <= 10; i++) {
				const index = String(i).padStart(2, "0");
				expect(flat[`color.chart.palettes.${index}.1`]).toBe(
					flat[`color.chart.categorical.${index}`],
				);
				const coords = Array.from(
					{ length: 5 },
					(_, j) =>
						ir[`color.chart.palettes.${index}.${j + 1}`].$extensions[p.EXT]
							.oklch[mode],
				);
				expect(coords.every((v, j) => j === 0 || v[0] < coords[j - 1][0])).toBe(
					true,
				);
				expect(
					coords.every((v) =>
						p.lin_rgb(v).every((c) => c >= -1e-9 && c <= 1 + 1e-9),
					),
				).toBe(true);
			}
			const report = r.extension(doc).chartContrast[mode];
			expect(report.categoricalAdjacent.length).toBe(9);
			expect(Object.keys(report.sequentialAdjacent).length).toBe(10);
		}
		expect([
			...css.matchAll(/--(?:categorical|palette)-[^:]+: #[\da-f]+;/g),
		]).toEqual([]);
		expect(css).toContain('[data-chart-palette="10"]');
		if (name === "v2ai")
			expect(r.read_tokens(doc)["color.chart.categorical.01"]).toBe("#ffc000");
	}
});

test("fallback shade recipe reproduces the reference ramp at its root", () => {
	const ir = new p.Curator({
		"brand.hue": 181.071,
		"brand.lightness": 0.855,
		"brand.chroma": 0.138,
	}).run();
	const expectedL = [0.855, 0.704, 0.6, 0.511, 0.437],
		expectedH = [181.071, 182.503, 184.704, 186.391, 188.216];
	for (let i = 1; i <= 5; i++) {
		const [L, , h] =
			ir[`color.chart.palettes.01.${i}`].$extensions[p.EXT].oklch.light;
		expect(L).toBeCloseTo(expectedL[i - 1], 12);
		expect(h).toBeCloseTo(expectedH[i - 1], 10);
	}
	for (const bad of [
		{ "walk.slots": 0 },
		{ "walk.slots": 1.5 },
		{ "walk.lightness": 2 },
		{ "walk.chromaCeiling": -1 },
	])
		expect(() => new p.Curator({ "brand.hue": 10, ...bad }).run()).toThrow(
			"Invalid",
		);
	expect(
		r.series(
			r.read_tokens(
				p.generate({ "brand.hue": 10, "walk.chromaCeiling": "floor" }).tokens,
			),
			"color.chart.categorical",
		).length,
	).toBe(10);
});

test("older twelve-slot profiles migrate without losing stated roots or shades", async () => {
	const store = root();
	try {
		const folder = seeded(store, "p", { "brand.hue": 200, "walk.slots": 12 });
		await p.curate_profile(folder);
		const ir = p.read_json(join(folder, "ir.json"));
		ir["color.chart.categorical.8"] = ir["color.chart.categorical.08"];
		delete ir["color.chart.categorical.08"];
		ir["color.chart.categorical.8"].light = "#123456";
		ir["color.chart.palettes.08.2"].dark = "#abcdef";
		p.write_json(join(folder, "ir.json"), ir);
		p.write_json(join(folder, "seed.json"), { "brand.hue": 200 });
		await p.curate_profile(folder);
		await p.build_profile(folder);
		const after = p.read_json(join(folder, "ir.json")),
			flat = r.read_tokens(p.read_json(join(folder, "design-tokens.json")));
		expect(flat["color.chart.categorical.08"]).toBe("#123456");
		expect(flat["color.chart.palettes.08.1"]).toBe("#123456");
		expect(after["color.chart.palettes.08.2"].dark).toBe("#abcdef");
		expect(
			Object.keys(after).filter((k) => k.startsWith("color.chart.categorical."))
				.length,
		).toBe(10);
		expect(after["surface.plotly.colorway.11"]).toBeUndefined();
		const first = readFileSync(join(folder, "ir.json"), "utf8");
		await p.curate_profile(folder);
		expect(readFileSync(join(folder, "ir.json"), "utf8")).toBe(first);
	} finally {
		rmSync(store, { recursive: true });
	}
});

test("example seeds explicitly preserve their theme corner radii", async () => {
	const expected = {
		fernline: 4,
		freshgreens: 8,
		gandalf: 8,
		locomotif: 16,
		osakanights: 12,
		v2ai: 0,
	};
	for (const [name, value] of Object.entries(expected)) {
		const seed = p.read_json(p.examples()[name]);
		expect(Object.hasOwn(seed, "radius")).toBe(true);
		const ir = new p.Curator(seed).run(),
			tokens = p.build_tokens(ir, name);
		for (const mode of p.MODES)
			expect(r.read_tokens(tokens, mode)["dimension.radius"]).toEqual({
				value,
				unit: "px",
			});
		expect((await import("./shadcn_profile.mjs")).build_css(ir)).toContain(
			`--radius: ${value}px;`,
		);
	}
});
test("radius units, mode overrides and stated edits survive rebuilds", async () => {
	const store = root();
	try {
		await p.main([
			"init",
			"radius",
			"--hue",
			"200",
			"--radius",
			"0.45rem",
			"--radius-dark",
			"0",
			"--store",
			store,
		]);
		const folder = join(store, "radius");
		await p.curate_profile(folder);
		let doc = p.read_json(await p.build_profile(folder));
		expect(r.read_tokens(doc, "light")["dimension.radius"]).toEqual({
			value: 0.45,
			unit: "rem",
		});
		expect(r.read_tokens(doc, "dark")["dimension.radius"]).toEqual({
			value: 0,
			unit: "px",
		});
		const ir = p.read_json(join(folder, "ir.json"));
		// Changing object-key order alone is not a stated edit.
		ir["dimension.radius"].light = { unit: "rem", value: 0.45 };
		expect(p.stated_values(ir)["dimension.radius"]).toBeUndefined();
		ir["dimension.radius"].light = { value: 2, unit: "px" };
		p.write_json(join(folder, "ir.json"), ir);
		await p.curate_profile(folder);
		doc = p.read_json(await p.build_profile(folder));
		expect(r.read_tokens(doc, "light")["dimension.radius"]).toEqual({
			value: 2,
			unit: "px",
		});
		for (const invalid of ["auto", "-1px", "1em", "1..2px", "NaN"])
			expect(() => new p.Curator({ "brand.hue": 1, radius: invalid })).toThrow(
				"Unsupported radius",
			);
	} finally {
		rmSync(store, { recursive: true });
	}
});
for (const hue of [0, 60, 120, 180, 240, 300])
	test(`hue-only curation has no default contrast defects: ${hue}`, () => {
		const result = p.generate({ "brand.hue": hue }, { name: "live" });
		expect(
			p.score_contrast(result.ir).filter((s) => s.verdict === "defect"),
		).toEqual([]);
		expect(result.tokens.name).toBe("live");
		expect(result.lineage.sankeys[0].links).toContainEqual({
			source: "param:brand.hue",
			target: "color.background.brand.bold",
		});
		expect(result.lineage.sankeys[1].nodes.map((n) => n.id)).toContain(
			"surface.mermaid",
		);
		expect(result.resolved["brand.lightness"]).toBeGreaterThan(0);
	});
test("stated edits survive offline rebuilds, unknown roles, releases and seed recovery", async () => {
	const store = root();
	try {
		const f = seeded(store);
		await p.curate_profile(f);
		const first = readFileSync(join(f, "ir.json"), "utf8");
		await p.curate_profile(f);
		expect(readFileSync(join(f, "ir.json"), "utf8")).toBe(first);
		const ir = JSON.parse(first);
		ir["color.surface"].light = "#ffffff";
		ir["color.text.brand"] = { light: "#123456", dark: "#abcdef" };
		ir["surface.mermaid.primaryColor"].light = "#abcdef";
		ir["color.link"].dark = "#abcdef80";
		p.write_json(join(f, "ir.json"), ir);
		const report = await p.curate_profile(f),
			after = p.read_json(join(f, "ir.json"));
		expect(
			report.some((l) =>
				l.startsWith(
					"held    color.surface light #ffffff stated (rule would give",
				),
			),
		).toBe(true);
		expect(after["surface.css.page"].light).toBe("#ffffff");
		expect(after["color.text.brand"]).toEqual(ir["color.text.brand"]);
		const tokens = p.read_json(await p.build_profile(f));
		expect(r.read_tokens(tokens, "light")["surface.mermaid.primaryColor"]).toBe(
			"#abcdef",
		);
		expect(r.read_tokens(tokens, "dark")["color.link"]).toBe("#abcdef80");
		delete after["color.surface"].light;
		p.write_json(join(f, "ir.json"), after);
		await p.curate_profile(f);
		expect(p.read_json(join(f, "ir.json"))["color.surface"].light).not.toBe(
			"#ffffff",
		);
		unlinkSync(join(f, "seed.json"));
		expect(p.seed_of(f)).toEqual({ "brand.hue": 200 });
		await p.curate_profile(f);
		expect(() => p.seed_of(join(store, "missing"))).toThrow("no seed.json");
		const empty = join(store, "empty");
		mkdirSync(empty);
		p.write_json(join(empty, "ir.json"), {});
		expect(() => p.seed_of(empty)).toThrow("no stated parameters");
	} finally {
		rmSync(store, { recursive: true });
	}
});
test("stated contrast choices and faulty default defects remain separate", async () => {
	const store = root();
	try {
		const choice = await p.curate_profile(
			seeded(store, "choice", { "brand.hue": 200, "offset.text.subtle": 0.05 }),
		);
		expect(choice.some((l) => l.startsWith("choice  color.text.subtle"))).toBe(
			true,
		);
		expect(choice.some((l) => l.startsWith("defect"))).toBe(false);
		const defect = await p.curate_profile(seeded(store, "defect"), {
			...p.DEFAULTS,
			"offset.text.subtle": [0.05, "bad default"],
		});
		expect(defect.some((l) => l.startsWith("defect  color.text.subtle"))).toBe(
			true,
		);
		await expect(p.build_profile(seeded(store, "missing"))).rejects.toThrow(
			"run curate first",
		);
		await expect(p.build_profile(store, "bad")).rejects.toThrow(
			"Invalid output",
		);
	} finally {
		rmSync(store, { recursive: true });
	}
});
test("build rejects incomplete and unsupported roles; schema rejects invalid output", () => {
	const ir = new p.Curator({ "brand.hue": 10 }).run();
	const incomplete = structuredClone(ir);
	delete incomplete["color.text"].dark;
	expect(() => p.build_tokens(incomplete, "x")).toThrow("has no dark");
	expect(() =>
		p.build_tokens({ ...ir, "size.gap": { light: 1, dark: 1 } }, "x"),
	).toThrow("outside the color");
	const broken = p.build_tokens(ir, "x");
	delete broken.resolutionOrder;
	expect(validate(broken)).toBe(false);
	expect(p.dtcg_colour([1, 2, 3, 127], null).alpha).toBeCloseTo(127 / 255, 4);
	expect(Object.keys(p.examples()).length).toBe(6);
	const special = new p.Curator({
		"brand.hue": 295,
		"brand.dark.lightness": 0.8,
		"walk.lightness": 0.6,
		"walk.chromaCeiling": "seed",
	}).run();
	expect(Object.keys(special)).toContain("surface.mermaid.pie10");
	expect(
		p.generate({ "brand.hue": 30, "walk.chromaCeiling": 0.08 }).tokens.name,
	).toBe("live");
});
test("CLI command API, output formats and validation", async () => {
	const store = root();
	const where = ["--store", store];
	try {
		await p.main([]);
		await p.main(["init", "p", "--hue", "100", ...where]);
		await p.main(["init", "a", "--accent", "#5c4295", ...where]);
		await p.main(["init", "e", "--example", "osakanights", ...where]);
		await p.main(["all", ...where]);
		await p.main(["set-default", "p", ...where]);
		await p.main(["status", "p", ...where]);
		utimesSync(
			join(store, "p/ir.json"),
			new Date(Date.now() + 10000),
			new Date(Date.now() + 10000),
		);
		await p.main(["status", ...where]);
		await p.main(["build", "p", "--format", "tokens", ...where]);
		await p.main(["init", "p", "--hue", "1", "--force", ...where]);
		for (const args of [
			["init", "p", "--hue", "1"],
			["init", "q"],
			["init", "q", "--example", "nope"],
			["init", "q", "--hue", "NaN"],
			["set-default", "q"],
			["lineage", "q"],
			["init"],
			["bogus", "q"],
			["build", "--format", "bad"],
			["build", "../bad"],
			["status", "--user"],
		])
			await expect(p.main([...args, ...where])).rejects.toThrow();
		await expect(
			p.main(["curate", "--store", join(store, "missing")]),
		).rejects.toThrow("no profiles");
		expect(p.store_dir({ user: true })).toEndWith(".design-profiles");
		const ir = p.read_json(join(store, "a/ir.json"));
		expect(
			p.generate(
				{ "brand.hue": 10 },
				{ stated: { "color.text": { light: "#123456" } } },
			).ir["color.text"].light,
		).toBe("#123456");
		ir["color.text.subtle"].light = "#ffffff";
		const ext = ir["color.text.subtle"].$extensions[p.EXT];
		ext.origin.light = "imputed";
		ext.derived.light = "#ffffff";
		expect(p.score_contrast(ir).some((s) => s.verdict === "defect")).toBe(true);
	} finally {
		rmSync(store, { recursive: true });
	}
});

test("CLI lifecycle and failures on Node and Bun without Python on PATH", () => {
	const store = root(),
		script = resolve(import.meta.dir, "profiles.mjs");
	try {
		for (const runtime of ["node", "bun"]) {
			const runtimePath = execFileSync("which", [runtime], {
				encoding: "utf8",
			}).trim();
			const command = (...args: string[]) =>
				execFileSync(runtimePath, [script, ...args], {
					cwd: store,
					env: { ...process.env, PATH: "/nonexistent" },
					encoding: "utf8",
				});
			const where = join(store, runtime);
			command("init", "hue", "--hue", "200", "--store", where);
			command("init", "acc", "--accent", "#5c4295", "--store", where);
			command("init", "ex", "--example", "osakanights", "--store", where);
			command("all", "--store", where);
			command("build", "hue", "--store", where, "--format", "css");
			command("lineage", "hue", "--store", where);
			command("set-default", "ex", "--store", where);
			expect(command("status", "hue", "--store", where)).toContain(
				"profile  hue",
			);
			utimesSync(
				join(where, "hue/ir.json"),
				new Date(Date.now() + 10000),
				new Date(Date.now() + 10000),
			);
			expect(command("status", "--store", where)).toContain("newer: rebuild");
			expect(command("--help")).toContain("profiles.mjs");
			for (const args of [
				["init", "hue", "--hue", "1", "--store", where],
				["init", "p"],
				["init", "p", "--example", "nope"],
				["init", "p", "--hue", "NaN"],
				["set-default", "missing"],
				["lineage", "missing"],
				["curate", "--store", join(store, "none")],
				["build", "--format", "bad"],
				["build", "../bad"],
				["init"],
				["bogus"],
				["status", "--store", where, "--user"],
			])
				expect(() => command(...args)).toThrow();
			command("init", "hue", "--hue", "1", "--store", where, "--force");
		}
	} finally {
		rmSync(store, { recursive: true });
	}
});
