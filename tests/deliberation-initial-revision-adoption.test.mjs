// ADOPT_INITIAL_REVISION: an existing document becomes v1 with the same state, receipt and
// validation CREATE_INITIAL_REVISION gives a composed one.
//
// Both deliberation skills offered "adopt it as v1 directly" as a decision-tree branch, and the
// only way to do it was by hand: prepend the artifact marker and rename the file. That v1 had no
// committed derived state and no receipt (`runConsistencyAudit` -> `MISSING_MANIFEST`), and it
// never met the canonical-form gate or the pre-publish validation every other first revision
// runs, so a document breaking this domain's rules entered the lineage unexamined.
//
// Two modes, chosen by what `sourceFilename` names:
//   rename  an unmanaged Markdown file in the managed directory becomes `<stem>-<slug>-<first>.md`
//           through the creation port itself (lock, exclusive write, state, receipt); the source
//           is left in place, byte-identical, for the agent to move to a backup.
//   record  a managed first revision that already carries the marker but has no receipt -- an
//           old hand adoption -- gets its state and receipt written, bytes untouched. The explicit
//           repair path: nothing is ever rewritten in silence, an existing receipt is never
//           replaced, and an unrecorded v1 keeps reading exactly as before.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readdir, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const proposalCli = path.resolve('skills/proposal-deliberation/cli.mjs');
const experimentalCli = path.resolve('skills/experimental-deliberation/cli.mjs');
const engineDir = path.resolve('skills/_core/deliberation/engine');
const MARKER = '<!-- proposal-workspace:artifact:v1 -->\n';
const RICH = '# Calibrated sampling under drift\n\n## Setting\n\nWe study a sampler $x_t$ whose step obeys\n\n$$\nx_{t+1} = A x_t \\tag{1}\n$$\n\n## Claim\n\nThe drift is bounded by (Ec. 1).\n';
const BROKEN = '# Calibrated sampling under drift\n\n## Setting\n\nWe study a sampler \\(x_t\\) with unbounded drift.\n';

function cli(script, root, request, args = []) {
	return new Promise((resolve, reject) => {
		const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root };
		delete env.DELIBERATION_DOMAIN_PROFILE;
		const child = spawn(process.execPath, [script, ...args], { cwd: root, env, stdio: ['pipe', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', (chunk) => { out += chunk; });
		child.on('error', reject);
		child.on('close', () => {
			try { resolve(JSON.parse(out)); } catch { reject(new Error(`unparseable: ${out}`)); }
		});
		child.stdin.end(JSON.stringify(request));
	});
}

async function audit(root) {
	const script = `const { createJiti } = await import('jiti'); const jiti = createJiti(${JSON.stringify(path.join(engineDir, 'x.mjs'))});
const v2 = await jiti.import(${JSON.stringify(path.join(engineDir, 'exports.ts'))});
process.stdout.write(JSON.stringify(await v2.runConsistencyAudit({ projectRoot: ${JSON.stringify(root)} })));`;
	return new Promise((resolve, reject) => {
		const env = { ...process.env, DELIBERATION_DOMAIN_PROFILE: path.resolve('skills/proposal-deliberation/profile.ts') };
		const child = spawn(process.execPath, ['--input-type=module', '-e', script], { cwd: path.resolve('.'), env, stdio: ['ignore', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', (chunk) => { out += chunk; });
		child.on('close', () => { try { resolve(JSON.parse(out)); } catch { reject(new Error(out)); } });
	});
}

async function project(files) {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-adoption-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	for (const [name, content] of Object.entries(files)) await writeFile(path.join(root, 'proposals', name), content);
	return root;
}

const adopt = (sourceFilename, extra = {}) => ({ operation: 'ADOPT_INITIAL_REVISION', instruction: 'Adopt the existing draft as the first revision.', sourceFilename, ...extra });
const sidecar = (root, kind, filename) => path.join(root, '.proposal-deliberation', kind, `${filename}.json`);

test('rename: an unmanaged draft becomes v1 with the same state and receipt a created v1 gets, and the draft is left in place', async () => {
	const root = await project({ 'my-draft.md': RICH });
	const body = await cli(proposalCli, root, adopt('my-draft.md'));
	assert.equal(body.status, 'adopted', JSON.stringify(body));
	assert.equal(body.mode, 'rename');
	assert.equal(body.targetFilename, 'research-concept-calibrated-sampling-under-drift-r01.md');
	assert.equal(body.mutations, 1);
	assert.equal(body.manifestStatus, 'COMMITTED');
	assert.equal(body.auditStatus, 'PASS');
	assert.equal(body.nextAction, 'move_adopted_source_to_backup');
	assert.equal(await readFile(path.join(root, 'proposals', body.targetFilename), 'utf8'), `${MARKER}${RICH}`, 'the document is adopted byte for byte');
	assert.equal(await readFile(path.join(root, 'proposals', 'my-draft.md'), 'utf8'), RICH, 'the source is never moved or rewritten by the engine');

	const state = JSON.parse(await readFile(sidecar(root, 'state', body.targetFilename), 'utf8'));
	const receipt = JSON.parse(await readFile(sidecar(root, 'receipts', body.targetFilename), 'utf8'));
	assert.equal(state.manifest.status, 'COMMITTED');
	assert.equal(state.manifest.documentSha256, body.targetSha256);
	assert.equal(receipt.operation, 'CREATE_INITIAL_REVISION', 'the same receipt every reader of a first revision already understands');
	assert.equal(receipt.documentShaAfter, body.targetSha256);
	assert.equal(receipt.adoptedFrom, 'my-draft.md');

	// The same shape a composed v1 gets, key for key, plus the one additive field.
	const created = await project({});
	const made = await cli(proposalCli, created, { operation: 'CREATE_INITIAL_REVISION', instruction: 'Calibrated sampling under drift. It bounds the drift.' });
	const madeReceipt = JSON.parse(await readFile(sidecar(created, 'receipts', made.targetFilename), 'utf8'));
	const madeState = JSON.parse(await readFile(sidecar(created, 'state', made.targetFilename), 'utf8'));
	assert.deepEqual(Object.keys(receipt).sort(), [...Object.keys(madeReceipt), 'adoptedFrom'].sort());
	assert.deepEqual(Object.keys(state.manifest).sort(), Object.keys(madeState.manifest).sort());
	assert.ok(existsSync(path.join(root, '.proposal-deliberation', 'locks', 'initial-revision.lock')), 'the same single-winner lock a creation takes');
});

test('rename: the draft meets the same canonical-form gate a created v1 meets, and nothing is written when it fails', async () => {
	const root = await project({ 'my-draft.md': BROKEN });
	const body = await cli(proposalCli, root, adopt('my-draft.md'));
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['INITIAL_REVISION_CANONICAL_FORM_VIOLATION']);
	assert.deepEqual(await readdir(path.join(root, 'proposals')), ['my-draft.md']);
	assert.equal(existsSync(path.join(root, '.proposal-deliberation')), false);
});

test('rename: refused while a managed revision already exists', async () => {
	const root = await project({ 'my-draft.md': RICH });
	await cli(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: 'A first idea. It is already managed.' });
	const body = await cli(proposalCli, root, adopt('my-draft.md'));
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['MANAGED_PROPOSAL_ALREADY_EXISTS']);
});

test('rename: a dry run reports the would-be v1 and writes nothing', async () => {
	const root = await project({ 'my-draft.md': RICH });
	const body = await cli(proposalCli, root, adopt('my-draft.md'), ['--dry-run']);
	assert.equal(body.status, 'preview', JSON.stringify(body));
	assert.equal(body.mode, 'rename');
	assert.equal(body.targetFilename, 'research-concept-calibrated-sampling-under-drift-r01.md');
	assert.equal(body.mutations, 0);
	assert.deepEqual(await readdir(path.join(root, 'proposals')), ['my-draft.md']);
	assert.equal(existsSync(path.join(root, '.proposal-deliberation')), false);
});

const HAND = 'research-concept-hand-adopted-r01.md';

test('record: an old hand-adopted v1 gets its state and receipt, its bytes untouched, and the audit turns from MISSING_MANIFEST to PASS', async () => {
	const root = await project({ [HAND]: `${MARKER}${RICH}` });
	assert.deepEqual((await audit(root)).failures, [`MISSING_MANIFEST:${HAND}`]);
	const body = await cli(proposalCli, root, adopt(HAND));
	assert.equal(body.status, 'adopted', JSON.stringify(body));
	assert.equal(body.mode, 'record');
	assert.equal(body.targetFilename, HAND);
	assert.equal(body.auditStatus, 'PASS');
	assert.equal(body.nextAction, null);
	assert.equal(await readFile(path.join(root, 'proposals', HAND), 'utf8'), `${MARKER}${RICH}`);
	const receipt = JSON.parse(await readFile(sidecar(root, 'receipts', HAND), 'utf8'));
	assert.equal(receipt.operation, 'CREATE_INITIAL_REVISION');
	assert.equal(receipt.adoptedFrom, HAND);
	assert.equal((await audit(root)).status, 'PASS');
	assert.equal(existsSync(path.join(root, '.proposal-deliberation', 'locks', 'initial-revision.lock')), false, 'recording takes no creation lock');
});

test('record: a revision that already has a receipt is never re-recorded', async () => {
	const root = await project({});
	const made = await cli(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: 'A first idea. It is already managed.' });
	const before = await readFile(sidecar(root, 'receipts', made.targetFilename), 'utf8');
	const body = await cli(proposalCli, root, adopt(made.targetFilename));
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['ADOPTION_ALREADY_RECORDED']);
	assert.equal(await readFile(sidecar(root, 'receipts', made.targetFilename), 'utf8'), before);
});

test('record: a hand-adopted v1 that fails the gate gets no record, and keeps reading exactly as before', async () => {
	const root = await project({ [HAND]: `${MARKER}${BROKEN}` });
	const body = await cli(proposalCli, root, adopt(HAND));
	assert.equal(body.status, 'blocked', JSON.stringify(body));
	assert.deepEqual(body.blockers.map((b) => b.code), ['INITIAL_REVISION_CANONICAL_FORM_VIOLATION']);
	assert.equal(existsSync(path.join(root, '.proposal-deliberation')), false);
	const status = await cli(proposalCli, root, { operation: 'STATUS' });
	assert.equal(status.latest?.filename ?? status.latest, HAND, JSON.stringify(status.latest));
});

for (const [label, name, code] of [
	['a path outside the managed directory', '../escape.md', 'ADOPTION_SOURCE_INVALID'],
	['a missing file', 'missing.md', 'ADOPTION_SOURCE_INVALID'],
	['a file that is not Markdown', 'notes.txt', 'ADOPTION_SOURCE_INVALID'],
	['a managed revision that is not a first revision', 'research-concept-hand-adopted-r02.md', 'ADOPTION_SOURCE_NOT_INITIAL'],
]) {
	test(`${label} is refused before anything is read into the lineage`, async () => {
		const root = await project({ 'notes.txt': 'x', 'research-concept-hand-adopted-r02.md': `${MARKER}${RICH}` });
		const body = await cli(proposalCli, root, adopt(name));
		assert.equal(body.status, 'blocked', JSON.stringify(body));
		assert.deepEqual(body.blockers.map((b) => b.code), [code]);
		assert.equal(existsSync(path.join(root, '.proposal-deliberation')), false);
	});
}

test('experiments domain: an unmanaged plan becomes experiments-<slug>-v01.md under the same gate', async () => {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-adoption-exp-'));
	await mkdir(path.join(root, 'experiments'), { recursive: true });
	const plan = '# Sweep plan\n\n## Design\n\n**Dataset:** Synthetic-Blobs, train/test split as distributed\n\n**Validation scheme:** paired t-test, 5 seeds, 10 repetitions\n';
	await writeFile(path.join(root, 'experiments', 'plan.md'), plan);
	const body = await cli(experimentalCli, root, adopt('plan.md'));
	assert.equal(body.status, 'adopted', JSON.stringify(body));
	assert.equal(body.targetFilename, 'experiments-sweep-plan-v01.md');
	assert.equal(body.targetRevision, 'v01');
	assert.ok((await readFile(path.join(root, 'experiments', body.targetFilename), 'utf8')).endsWith(plan));

	const second = await mkdtemp(path.join(os.tmpdir(), 'deliberation-adoption-exp-'));
	await mkdir(path.join(second, 'experiments'), { recursive: true });
	await writeFile(path.join(second, 'experiments', 'filled.md'), '# Filled\n\n| Arm | Accuracy |\n| --- | --- |\n| Source only | 0.71 |\n');
	const refused = await cli(experimentalCli, second, adopt('filled.md'));
	assert.equal(refused.status, 'blocked', JSON.stringify(refused));
	assert.deepEqual(refused.blockers.map((b) => b.code), ['INITIAL_REVISION_CANONICAL_FORM_VIOLATION']);
});
