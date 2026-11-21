import { describe, expect, test } from "bun:test";
import { decode, main, resolvePreset, run } from "./shadcn.mjs";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

describe("public shadcn preset decoder", () => {
	test("decodes the complete sample without an in-house codec", () => {
		expect(decode("b5cR4pgAc")).toEqual({
			style: "nova",
			baseColor: "neutral",
			theme: "violet",
			chartColor: "teal",
			font: "inter",
			fontHeading: "inherit",
			iconLibrary: "lucide",
			radius: "small",
			menuAccent: "subtle",
			menuColor: "default-translucent",
		});
	});
	test("supports the upstream version-a format", () => {
		expect(decode("a0").fontHeading).toBe("inherit");
	});
	test("resolves actual theme and font registry metadata", async () => {
		const snapshot = await resolvePreset("b5cR4pgAc");
		expect(snapshot.cssVars.light?.["chart-1"]).toBe(
			"oklch(0.855 0.138 181.071)",
		);
		expect(snapshot.fonts[0]?.font?.family).toBe(
			"'Inter Variable', sans-serif",
		);
	}, 30000);
	test("generates a profile from one code without a subprocess", async () => {
		const store = await mkdtemp(join(tmpdir(), "preset-profile-"));
		try {
			await main(["b5cR4pgAc", "--store", store]);
			const css = await readFile(
				join(store, "preset-b5cR4pgAc", "theme.css"),
				"utf8",
			);
			expect(css).toContain("--palette-10-5:");
			expect(css).toContain("@fontsource-variable/inter/index.css");
			const tokens = JSON.parse(
				await readFile(
					join(store, "preset-b5cR4pgAc", "design-tokens.json"),
					"utf8",
				),
			);
			expect(tokens.modifiers.mode.contexts.dark).toBeDefined();
		} finally {
			await rm(store, { recursive: true });
		}
	}, 30000);
	test("prints command help", async () => {
		expect(await run(["--help"])).toBe(0);
	});
	test("returns a non-zero CLI status for an invalid preset", async () => {
		expect(await run(["invalid"])).toBe(1);
	});
	test("rejects malformed codes and CLI options before fetching", async () => {
		expect(() => decode("not-a-code")).toThrow("Invalid shadcn preset");
		await expect(main([])).rejects.toThrow("Supply one");
		await expect(main(["b0", "--format", "invalid"])).rejects.toThrow(
			"Invalid output",
		);
		await expect(main(["b0", "--name", "../outside"])).rejects.toThrow(
			"Invalid profile",
		);
	});
});
