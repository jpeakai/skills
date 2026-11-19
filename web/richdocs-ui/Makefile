.PHONY: install typecheck test build ci dev

install:
	bun install --frozen-lockfile

typecheck: install
	bunx tsc --noEmit

test: install
	bun test

build: install
	bunx --bun vite build

ci: typecheck test build

dev: install
	bunx --bun vite --host 127.0.0.1 --port 4174
