// An official dry run for the first revision: every check, no lock, no write.
//
// `CREATE_INITIAL_REVISION` is the one publication path with no preview turn, and a successful
// call leaves `<sidecarRoot>/locks/initial-revision.lock` in place permanently (the slug-independent
// single-winner guard). So the only way to see what v1 would be -- its filename, its derived
// headings, whether the composed document passes the canonical form -- was to create it, after
// which a second attempt is refused for good. `--dry-run` (or `dryRun: true` in the request) runs
// the identical checks and composition and stops before the lock and the write.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readdir, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const cliPath = path.resolve('skills/proposal-deliberation/cli.mjs');
const MARKER = '<!-- proposal-workspace:artifact:v1 -->\n';
const IDEA = 'A bounded tutor for proof drafts. It names the step it doubts.';

async function freshRoot() {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-dry-run-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	return root;
}

function oneShot(root, request, args = []) {
	return new Promise((resolve, reject) => {
		const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root };
		const child = spawn(process.execPath, [cliPath, ...args], { cwd: root, env, stdio: ['pipe', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', (chunk) => { out += chunk; });
		child.on('error', reject);
		child.on('close', (code) => {
			try { resolve({ code, body: JSON.parse(out) }); } catch { reject(new Error(`unparseable: ${out}`)); }
		});
		child.stdin.end(JSON.stringify(request));
	});
}

async function nothingWritten(root) {
	assert.deepEqual(await readdir(path.join(root, 'proposals')), [], 'no managed file');
	assert.equal(existsSync(path.join(root, '.proposal-deliberation')), false, 'no sidecar root, so no lock, state or receipt');
}

test('--dry-run composes v1 and reports it, and writes nothing -- not even the lock', async () => {
	const root = await freshRoot();
	const { code, body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA }, ['--dry-run']);
	assert.equal(code, 0);
	assert.equal(body.status, 'preview', JSON.stringify(body));
	assert.equal(body.dryRun, true);
	assert.equal(body.mutations, 0);
	assert.equal(body.receiptId, null);
	assert.match(body.targetFilename, /^research-concept-a-bounded-tutor-for-proof-drafts-r01\.md$/);
	assert.deepEqual(body.canonicalMetadata, { schemaVersion: 1, title: 'A bounded tutor for proof drafts', sectionHeading: 'It names the step it doubts' });
	await nothingWritten(root);

	// The dry run is exactly what the real call then writes, and it left nothing in the way.
	const real = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA });
	assert.equal(real.body.status, 'created', JSON.stringify(real.body));
	assert.equal(real.body.targetFilename, body.targetFilename);
	const written = await readFile(path.join(root, 'proposals', real.body.targetFilename), 'utf8');
	assert.equal(written, `${MARKER}${body.markdown}`);
});

test('dryRun: true in the request is the same dry run', async () => {
	const root = await freshRoot();
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA, dryRun: true });
	assert.equal(body.status, 'preview', JSON.stringify(body));
	await nothingWritten(root);
});

test('a dry run runs the same refusals as the real call', async () => {
	const root = await freshRoot();
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: 'Only one sentence here.' }, ['--dry-run']);
	assert.equal(body.status, 'blocked');
	assert.deepEqual(body.blockers.map((b) => b.code), ['INITIAL_IDEA_SINGLE_SENTENCE']);
	await nothingWritten(root);
});

test('a dry run predicts the refusal a leftover creation lock would cause, and never touches the lock', async () => {
	const root = await freshRoot();
	const lock = path.join(root, '.proposal-deliberation', 'locks', 'initial-revision.lock');
	await mkdir(path.dirname(lock), { recursive: true });
	await writeFile(lock, '{"createdAt":"2026-01-01T00:00:00.000Z"}');
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA }, ['--dry-run']);
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['MANAGED_PROPOSAL_ALREADY_EXISTS']);
	assert.match(body.blockers[0].message, /initial-revision\.lock/);
	assert.equal(await readFile(lock, 'utf8'), '{"createdAt":"2026-01-01T00:00:00.000Z"}');
	assert.deepEqual(await readdir(path.join(root, 'proposals')), []);
});

test('a dry run is refused on an operation it does not cover, instead of mutating', async () => {
	const root = await freshRoot();
	const { body } = await oneShot(root, { operation: 'WITHDRAW_REVISION', instruction: 'Withdraw it.', sourceFilename: 'research-concept-r01.md', dryRun: true });
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['DRY_RUN_UNSUPPORTED']);
	assert.equal(body.mutations, 0);
});

test('--dry-run leaves the read-only STATUS answering as usual', async () => {
	const root = await freshRoot();
	const { body } = await oneShot(root, { operation: 'STATUS' }, ['--dry-run']);
	assert.equal(body.status, 'ok', JSON.stringify(body));
});
