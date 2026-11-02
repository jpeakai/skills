import { readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

/** @typedef {Record<string, any>} Dict */
export const STORE = ".design-profiles";
export const DEFAULT_FILE = ".default-profile";
export const TOKENS_FILE = "design-tokens.json";
export const EXT = "ai.jpeak.design-profiles";
export const HARNESSES = [".codex", ".claude"];
export class ProfileError extends Error {}

/** @param {number} alpha */
function alpha_hex(alpha) {
	const scaled = alpha * 255,
		floor = Math.floor(scaled);
	return (scaled - floor === 0.5 ? floor + (floor % 2) : Math.round(scaled))
		.toString(16)
		.padStart(2, "0");
}

/** @param {string} path */
export function isFile(path) {
	try {
		return statSync(path).isFile();
	} catch (error) {
		if (
			["ENOENT", "ENOTDIR"].includes(
				/** @type {NodeJS.ErrnoException} */ (error).code ?? "",
			)
		)
			return false;
		throw error;
	}
}

/** @param {string} name @param {string} skill @param {string} project @param {string} home */
export function candidate_dirs(name, skill, project, home) {
	const tail = join("skills", skill, "resources", "profile", name);
	return [
		join(project, STORE, name),
		join(home, STORE, name),
		...HARNESSES.map((h) => join(project, h, tail)),
		...HARNESSES.map((h) => join(home, h, tail)),
	];
}

/** @param {string} project @param {string} home */
export function default_profile_name(project, home) {
	for (const root of [project, home]) {
		const marker = join(root, STORE, DEFAULT_FILE);
		if (!isFile(marker)) continue;
		const name = readFileSync(marker, "utf8").trim();
		if (!name)
			throw new ProfileError(
				`error: ${marker} is empty; it must name one profile`,
			);
		return name;
	}
	return null;
}

/** @param {string|null} name @param {string} skill @param {string} [project] @param {string} [home] */
export function resolve_profile(
	name,
	skill,
	project = process.cwd(),
	home = homedir(),
) {
	const source = name === null ? DEFAULT_FILE : "--profile";
	name ??= default_profile_name(project, home);
	if (name === null) return null;
	const tried = candidate_dirs(name, skill, project, home).map((dir) =>
		join(dir, TOKENS_FILE),
	);
	const found = tried.find(isFile);
	if (found) return found;
	throw new ProfileError(
		`error: design profile '${name}' (from ${source}) resolves nowhere. Tried:\n${tried.map((p) => `  ${p}`).join("\n")}`,
	);
}

/** @param {Dict} doc */
export function modes(doc) {
	return Object.keys(doc.modifiers.mode.contexts);
}
/** @param {Dict} doc */
export function default_mode(doc) {
	return String(doc.modifiers.mode.default);
}
/** @param {Dict} doc */
export function extension(doc) {
	return doc.modifiers.mode.$extensions?.[EXT] ?? {};
}

/** @param {Dict} into @param {Dict} source */
function merge(into, source) {
	for (const [key, value] of Object.entries(source)) {
		if (
			value &&
			typeof value === "object" &&
			!Array.isArray(value) &&
			into[key] &&
			typeof into[key] === "object" &&
			!("$value" in value)
		)
			merge(into[key], value);
		else into[key] = structuredClone(value);
	}
}

/** Read one DTCG mode, merging sets and resolving aliases without modifying the input.
 * @param {Dict} doc @param {string} [mode] @returns {Dict}
 */
export function read_tokens(doc, mode = default_mode(doc)) {
	const contexts = doc.modifiers.mode.contexts;
	if (!Object.hasOwn(contexts, mode))
		throw new ProfileError(
			`error: profile has no mode '${mode}'; it carries ${Object.keys(contexts).sort().join(", ")}`,
		);
	/** @type {Dict} */ const tree = {};
	for (const set of contexts[mode]) merge(tree, set);
	/** @type {Map<string, [string, any]>} */ const raw = new Map();
	/** @param {Dict} node @param {string[]} path @param {string} kind */
	function walk(node, path, kind) {
		kind = node.$type ?? kind;
		for (const [key, child] of Object.entries(node)) {
			if (
				key.startsWith("$") ||
				!child ||
				typeof child !== "object" ||
				Array.isArray(child)
			)
				continue;
			if ("$value" in child)
				raw.set([...path, key].join("."), [child.$type ?? kind, child.$value]);
			else walk(child, [...path, key], kind);
		}
	}
	walk(tree, [], "");
	/** @param {string} path @param {string[]} [seen] @returns {[string, any]} */
	function resolve(path, seen = []) {
		if (seen.includes(path))
			throw new ProfileError(
				`error: alias cycle through ${[...seen, path].join(" -> ")}`,
			);
		const entry = raw.get(path);
		if (!entry)
			throw new ProfileError(
				`error: alias to '${path}', which the profile does not define`,
			);
		const [kind, value] = entry;
		if (
			typeof value === "string" &&
			value.startsWith("{") &&
			value.endsWith("}")
		) {
			const [targetKind, target] = resolve(value.slice(1, -1), [...seen, path]);
			return [kind || targetKind, target];
		}
		return [kind, value];
	}
	/** @type {Dict} */ const flat = {};
	for (const path of raw.keys()) {
		const [kind, value] = resolve(path);
		let plain = structuredClone(value);
		if (kind === "color")
			plain =
				value.hex + ((value.alpha ?? 1) < 1 ? alpha_hex(value.alpha) : "");
		if (kind === "fontFamily" && Array.isArray(value))
			plain = value
				.map((f) => (f.includes(" ") && !f.startsWith("'") ? `'${f}'` : f))
				.join(", ");
		flat[path.replace(/\.default$/, "")] = plain;
	}
	return flat;
}

/** @param {Dict} flat @param {string} prefix @returns {Dict} */
export function group(flat, prefix) {
	const head = `${prefix}.`;
	return Object.fromEntries(
		Object.entries(flat)
			.filter(([key]) => key.startsWith(head))
			.map(([key, value]) => [key.slice(head.length), value]),
	);
}
/** @param {Dict} flat @param {string} prefix */
export function series(flat, prefix) {
	const items = group(flat, prefix);
	return Object.keys(items)
		.filter((k) => /^\d+$/.test(k))
		.sort((a, b) => Number(a) - Number(b))
		.map((key) => items[key]);
}
