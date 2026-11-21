import { expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import * as r from "./profile_resolver.mjs";

test("five-tier lookup, defaults, missing profiles and empty markers", () => {
	const root = mkdtempSync(join(tmpdir(), "profile-resolve-")),
		project = join(root, "project"),
		home = join(root, "home");
	try {
		const dirs = r.candidate_dirs("brand", "richdocs", project, home);
		expect(dirs).toEqual([
			join(project, ".design-profiles/brand"),
			join(home, ".design-profiles/brand"),
			...[project, home].flatMap((base) =>
				[".codex", ".claude"].map((h) =>
					join(base, h, "skills/richdocs/resources/profile/brand"),
				),
			),
		]);
		expect(r.resolve_profile(null, "richdocs", project, home)).toBeNull();
		expect(() => r.resolve_profile("ghost", "richdocs", project, home)).toThrow(
			"resolves nowhere",
		);
		for (const folder of [...dirs].reverse()) {
			mkdirSync(folder, { recursive: true });
			writeFileSync(join(folder, r.TOKENS_FILE), "{}");
			expect(r.resolve_profile("brand", "richdocs", project, home)).toBe(
				join(folder, r.TOKENS_FILE),
			);
		}
		const marker = join(project, r.STORE, r.DEFAULT_FILE);
		writeFileSync(join(home, r.STORE, r.DEFAULT_FILE), "other\n");
		writeFileSync(marker, "brand\n");
		expect(r.default_profile_name(project, home)).toBe("brand");
		expect(r.resolve_profile(null, "richdocs", project, home)).toBe(
			join(dirs[0], r.TOKENS_FILE),
		);
		writeFileSync(marker, "ghost\n");
		expect(() => r.resolve_profile(null, "richdocs", project, home)).toThrow(
			"from .default-profile",
		);
		writeFileSync(marker, "\n");
		expect(() => r.default_profile_name(project, home)).toThrow("is empty");
		expect(() => r.resolve_profile("missing", "richdocs")).toThrow(
			"resolves nowhere",
		);
		expect(r.isFile(join(root, "missing", "file"))).toBe(false);
	} finally {
		rmSync(root, { recursive: true });
	}
});

const c = (hex: string, alpha = 1) => ({
	colorSpace: "srgb",
	components: [0, 0, 0],
	hex,
	alpha,
});
const doc = (tree: Record<string, unknown>) => ({
	modifiers: {
		mode: { contexts: { light: [tree], dark: [tree] }, default: "light" },
	},
});
test("DTCG merging, aliases, alpha, fonts and zero-padded numeric series", () => {
	const tree = {
		color: {
			$type: "color",
			text: {
				default: { $value: c("#111111") },
				subtle: { $value: c("#222222") },
			},
			border: { $value: c("#111111", 0.14) },
			link: { $value: "{color.text.default}" },
		},
		font: {
			$type: "fontFamily",
			body: { $value: ["Fira Sans", "sans-serif"] },
		},
		size: { gap: { $type: "number", $value: 4 } },
	};
	const d = doc(tree);
	const before = structuredClone(d);
	const flat = r.read_tokens(d);
	expect(flat).toMatchObject({
		"color.text": "#111111",
		"color.border": "#11111124",
		"color.link": "#111111",
		"font.body": "'Fira Sans', sans-serif",
		"size.gap": 4,
	});
	expect(d).toEqual(before);
	expect(r.group(flat, "color.text")).toEqual({ subtle: "#222222" });
	expect(
		r.series(
			{ "p.10": "ten", "p.01": "one", "p.02": "two", "p.note": "ignored" },
			"p",
		),
	).toEqual(["one", "two", "ten"]);
	expect(r.modes(d)).toEqual(["light", "dark"]);
	expect(r.default_mode(d)).toBe("light");
	expect(r.extension(d)).toEqual({});
	const dark: ReturnType<typeof doc> & {
		modifiers: { mode: { $extensions?: Record<string, unknown> } };
	} = doc(tree);
	dark.modifiers.mode.default = "dark";
	dark.modifiers.mode.contexts.dark.push({
		color: { text: { default: { $value: c("#eeeeee") } } },
	});
	dark.modifiers.mode.$extensions = { [r.EXT]: { profile: "demo" } };
	expect(r.read_tokens(dark)["color.text"]).toBe("#eeeeee");
	expect(r.extension(dark)).toEqual({ profile: "demo" });
	expect(() => r.read_tokens(d, "sepia")).toThrow("no mode");
	expect(() =>
		r.read_tokens(doc({ a: { $value: "{b}" }, b: { $value: "{a}" } })),
	).toThrow("alias cycle");
	expect(() => r.read_tokens(doc({ a: { $value: "{missing}" } }))).toThrow(
		"does not define",
	);
});
