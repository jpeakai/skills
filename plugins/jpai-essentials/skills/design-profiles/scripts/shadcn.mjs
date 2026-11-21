import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { decodePreset, isPresetCode } from "shadcn/preset";
import { getRegistryItems } from "shadcn/registry";
import { savePreset } from "./shadcn_profile.mjs";

/** Decode with the upstream public API; codes do not encode CSS or font files.
 * @param {string} code
 */
export function decode(code) {
	const config = isPresetCode(code) && decodePreset(code);
	if (!config) throw new Error(`Invalid shadcn preset code: ${code}`);
	return config;
}

/** Resolve design data without installing components into a project.
 * @param {string} code
 */
export async function resolvePreset(code) {
	const config = decode(code);
	const url = new URL("https://ui.shadcn.com/init");
	url.searchParams.set("preset", code);
	url.searchParams.set("base", "base");
	url.searchParams.set("only", "theme,font");
	const [registry] = await getRegistryItems([url.href]);
	if (!registry?.cssVars?.light || !registry.cssVars.dark) {
		throw new Error("Preset registry must supply light and dark CSS variables");
	}
	const names = [`font-${config.font}`];
	if (config.fontHeading !== "inherit") {
		names.push(`font-heading-${config.fontHeading}`);
	}
	const items = await getRegistryItems(names);
	const fonts = items.filter((item) => item.type === "registry:font");
	if (fonts.length !== names.length || fonts.some((font) => !font.font)) {
		throw new Error("Preset registry returned incomplete font metadata");
	}
	return { code, config, cssVars: registry.cssVars, fonts };
}

/** @param {string[]} argv */
export async function main(argv) {
	const { positionals, values } = parseArgs({
		args: argv,
		allowPositionals: true,
		options: {
			name: { type: "string" },
			store: { type: "string", default: ".design-profiles" },
			format: { type: "string", default: "both" },
			help: { type: "boolean" },
		},
	});
	if (values.help) {
		console.log(
			"preset CODE [--name NAME] [--store DIR] [--format css|tokens|both]",
		);
		return;
	}
	const [code] = positionals;
	if (!code || positionals.length !== 1)
		throw new Error("Supply one shadcn preset code");
	if (!["css", "tokens", "both"].includes(values.format))
		throw new Error("Invalid output format");
	const name = values.name ?? `preset-${code}`;
	if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(name))
		throw new Error("Invalid profile name");
	const snapshot = await resolvePreset(code);
	await savePreset(snapshot, {
		name,
		store: resolve(values.store),
		format: values.format,
	});
}

/** Translate adapter failures into a CLI exit status.
 * @param {string[]} argv
 */
export async function run(argv) {
	try {
		await main(argv);
		return 0;
	} catch (error) {
		console.error(error instanceof Error ? error.message : String(error));
		return 1;
	}
}

if (
	process.argv[1] &&
	resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
	process.exitCode = await run(process.argv.slice(2));
}
