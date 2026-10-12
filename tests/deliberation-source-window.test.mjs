// The first revision's source window: how much of the declared sources v1 actually reads.
//
// `CREATE_INITIAL_REVISION` composes v1 from the idea plus every declared source's Markdown,
// pasted verbatim. The loader reads sources in declaration order, nested `<folder>/<folder>.md`
// first and flat `*.md` second within each, and stops at 4000 bytes in total. Before this fix
// that window was fixed and silent: a 10 KB data paper declared first was cut mid-sentence and
// every later source (the managed proposal, for the experiments domain) was left out entirely,
// with nothing in the result saying so.
//
// Now the result reports the window (`sourceWindow`), warns `SOURCE_WINDOW_TRUNCATED` whenever a
// document was cut or left out, and `sourceWindowBytes` widens it for one creation.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const proposalCli = path.resolve('skills/proposal-deliberation/cli.mjs');
const experimentalCli = path.resolve('skills/experimental-deliberation/cli.mjs');
const IDEA = 'A bounded tutor for proof drafts. It names the step it doubts.';
const DECLARATIONS = '**Dataset:** Synthetic-Blobs, train/test split as distributed\n\n**Validation scheme:** paired t-test, 5 seeds, 10 repetitions';

function oneShot(cli, root, request, args = []) {
	return new Promise((resolve, reject) => {
		const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root };
		delete env.DELIBERATION_DOMAIN_PROFILE;
		const child = spawn(process.execPath, [cli, ...args], { cwd: root, env, stdio: ['pipe', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', (chunk) => { out += chunk; });
		child.on('error', reject);
		child.on('close', () => {
			try { resolve(JSON.parse(out)); } catch { reject(new Error(`unparseable: ${out}`)); }
		});
		child.stdin.end(JSON.stringify(request));
	});
}

/** A sentence-shaped filler of exactly `bytes` ASCII bytes, starting with a recognizable tag. */
function filler(tag, bytes) {
	const body = `${tag} `.padEnd(bytes - 1, 'word ');
	return `${body.slice(0, bytes - 1)}\n`;
}

async function guideRoot(files) {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-source-window-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	for (const [relative, content] of Object.entries(files)) {
		await mkdir(path.dirname(path.join(root, relative)), { recursive: true });
		await writeFile(path.join(root, relative), content);
	}
	return root;
}

test('a source cut by the window, and one left out after it, are reported and warned about', async () => {
	const root = await guideRoot({
		'guidance/paper-guide/alpha/alpha.md': filler('ALPHA', 5000),
		'guidance/paper-guide/beta.md': filler('BETA', 300),
	});
	const body = await oneShot(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA }, ['--dry-run']);
	assert.equal(body.status, 'preview', JSON.stringify(body).slice(0, 500));
	assert.deepEqual(body.sourceWindow, {
		limitBytes: 4000,
		loadedBytes: 4000,
		sources: [
			{ path: 'guidance/paper-guide/alpha/alpha.md', bytes: 5000, loadedBytes: 4000, status: 'truncated' },
			{ path: 'guidance/paper-guide/beta.md', bytes: 300, loadedBytes: 0, status: 'not-loaded' },
		],
	});
	assert.deepEqual(body.warnings.map((w) => w.code), ['SOURCE_WINDOW_TRUNCATED']);
	assert.match(body.warnings[0].message, /alpha\.md/);
	assert.match(body.warnings[0].message, /beta\.md/);
	assert.match(body.warnings[0].message, /sourceWindowBytes/);
	assert.doesNotMatch(body.markdown, /BETA/);
});

test('sourceWindowBytes widens the window for one creation, and then nothing is cut', async () => {
	const root = await guideRoot({
		'guidance/paper-guide/alpha/alpha.md': filler('ALPHA', 5000),
		'guidance/paper-guide/beta.md': filler('BETA', 300),
	});
	const body = await oneShot(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA, sourceWindowBytes: 6000 }, ['--dry-run']);
	assert.equal(body.status, 'preview', JSON.stringify(body).slice(0, 500));
	assert.equal(body.sourceWindow.limitBytes, 6000);
	assert.deepEqual(body.sourceWindow.sources.map((s) => s.status), ['loaded', 'loaded']);
	assert.equal(body.warnings, undefined);
	assert.match(body.markdown, /BETA/);
});

test('sources inside the default window load whole and raise no warning', async () => {
	const root = await guideRoot({ 'guidance/paper-guide/alpha/alpha.md': 'Define notation before use.\n' });
	const body = await oneShot(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA });
	assert.equal(body.status, 'created', JSON.stringify(body).slice(0, 500));
	assert.deepEqual(body.sourceWindow.sources, [{ path: 'guidance/paper-guide/alpha/alpha.md', bytes: 28, loadedBytes: 28, status: 'loaded' }]);
	assert.equal(body.warnings, undefined);
});

for (const invalid of [0, 262_145, 12.5, 'big']) {
	test(`sourceWindowBytes ${JSON.stringify(invalid)} is refused, nothing composed`, async () => {
		const root = await guideRoot({ 'guidance/paper-guide/alpha/alpha.md': 'Define notation before use.\n' });
		const body = await oneShot(proposalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: IDEA, sourceWindowBytes: invalid });
		assert.equal(body.status, 'blocked', JSON.stringify(body).slice(0, 500));
		assert.deepEqual(body.blockers.map((b) => b.code), ['SOURCE_WINDOW_INVALID']);
		assert.equal(body.mutations, 0);
	});
}

test('sourceWindowBytes on another operation is refused rather than ignored', async () => {
	const root = await guideRoot({});
	const body = await oneShot(proposalCli, root, { operation: 'WITHDRAW_REVISION', instruction: 'Withdraw it.', sourceFilename: 'research-concept-r01.md', sourceWindowBytes: 8000 });
	assert.equal(body.status, 'blocked', JSON.stringify(body).slice(0, 500));
	assert.deepEqual(body.blockers.map((b) => b.code), ['SOURCE_WINDOW_UNSUPPORTED']);
});

test('experiments domain: the data paper is read first, so a large one leaves the proposal out -- and says so', async () => {
	const root = await guideRoot({
		'guidance/data-paper/data/data.md': filler('DATAPAPER', 4500),
		'proposals/research-concept-sample-r01.md': `The proposal claims one shared latent code.\n\n${DECLARATIONS}\n`,
	});
	const body = await oneShot(experimentalCli, root, { operation: 'CREATE_INITIAL_REVISION', instruction: `Sweep plan. It tests the shared code.\n\n${DECLARATIONS}` }, ['--dry-run']);
	assert.ok(body.sourceWindow, JSON.stringify(body).slice(0, 500));
	assert.deepEqual(body.sourceWindow.sources.map((s) => [s.path, s.status]), [
		['guidance/data-paper/data/data.md', 'truncated'],
		['proposals/research-concept-sample-r01.md', 'not-loaded'],
	]);
	assert.deepEqual(body.warnings.map((w) => w.code), ['SOURCE_WINDOW_TRUNCATED']);
});
