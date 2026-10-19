// Issue #76: the engine CLI must turn its own file URL into a filesystem path with
// `fileURLToPath`, never `URL.pathname` -- the pathname keeps percent-encoding
// (`%20`, `%C3%B1`) and, on Windows, a leading `/C:` that is not a path.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const forge = path.resolve('.');
// Wherever this checkout resolves its dependencies from (a worktree has none of its own).
const nodeModules = path.resolve(path.dirname(createRequire(path.join(forge, 'package.json')).resolve('jiti/package.json')), '..');
const cliPath = path.join(forge, 'skills/_core/deliberation/engine/cli.mjs');

test('cli.mjs derives its directory with fileURLToPath, not URL.pathname', () => {
	const source = readFileSync(cliPath, 'utf8');
	assert.doesNotMatch(source, /import\.meta\.url\)\.pathname/);
	assert.match(source, /fileURLToPath\(import\.meta\.url\)/);
});

test('the CLI starts from a clone whose path holds a space and a non-ASCII character', () => {
	const base = mkdtempSync(path.join(os.tmpdir(), 'papersmith-url-'));
	try {
		const root = path.join(base, 'clone with space ñ');
		cpSync(path.join(forge, 'skills'), path.join(root, 'skills'), { recursive: true });
		cpSync(path.join(forge, 'package.json'), path.join(root, 'package.json'));
		symlinkSync(nodeModules, path.join(root, 'node_modules'), 'dir');

		const proc = spawnSync(process.execPath, [path.join(root, 'skills/proposal-deliberation/cli.mjs'), '{}'], {
			cwd: root,
			encoding: 'utf8',
			env: { ...process.env, DELIBERATION_DOMAIN_PROFILE: path.join(root, 'skills/proposal-deliberation/profile.ts') },
			timeout: 60_000,
		});

		assert.doesNotMatch(proc.stderr, /Cannot find module|ENOENT|ERR_MODULE_NOT_FOUND/, proc.stderr);
		assert.doesNotThrow(() => JSON.parse(proc.stdout), `stdout was not JSON:\n${proc.stdout}\n${proc.stderr}`);
	} finally {
		rmSync(base, { recursive: true, force: true });
	}
});
