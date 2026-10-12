// B13: a successor inherits every byte outside its locus, including a line that
// links a companion artifact named after the PREVIOUS revision (a picture
// rendered from `<revision>.sky.json` into `<revision>.graph.html`, say).
// Nothing regenerated or flagged it, so the successor silently pointed at its
// predecessor's picture.
//
// The engine never regenerates an artifact outside its own scope and never
// rewrites a managed revision. It flags: the preview and the receipt name every
// reference in the successor to another revision's companion artifact, and a
// deliberate substitution inside the locus (the ordinary edit path) clears it.
// Every fixture is generic.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const engineDir = path.resolve('skills/_core/deliberation/engine');
const cliPath = path.join(engineDir, 'cli.mjs');
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const workspaceModule = await jiti.import(path.join(engineDir, 'proposal-workspace.ts'));
const v2 = await jiti.import(path.join(engineDir, 'exports.ts'));

const R01 = 'research-concept-r01.md';
const R02 = 'research-concept-r02.md';

async function seed(content) {
	const root = await mkdtemp(path.join(os.tmpdir(), 'pp-stale-companion-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	await workspaceModule.createProposalWorkspaceTool(root).execute('seed', { action: 'write', resource: 'proposal', slug: 'r01', content });
	return root;
}

function serve(root, sessionId) {
	const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root, PROPOSAL_DELIBERATION_SESSION_ID: sessionId };
	delete env.ANTHROPIC_API_KEY;
	const child = spawn(process.execPath, [cliPath, '--serve'], { cwd: engineDir, env, stdio: ['pipe', 'pipe', 'pipe'] });
	const lines = [];
	let buffer = '';
	child.stdout.on('data', chunk => {
		buffer += chunk.toString('utf8');
		let index;
		while ((index = buffer.indexOf('\n')) !== -1) {
			const line = buffer.slice(0, index).trim();
			buffer = buffer.slice(index + 1);
			if (line) lines.push(JSON.parse(line));
		}
	});
	const send = async request => {
		const at = lines.length;
		child.stdin.write(`${JSON.stringify(request)}\n`);
		const deadline = Date.now() + 20000;
		while (lines.length <= at) {
			if (Date.now() > deadline) throw new Error('serve timeout');
			await new Promise(resolve => setTimeout(resolve, 20));
		}
		return lines[at];
	};
	return { send, close: () => { child.stdin.end(); child.kill(); } };
}

const SOURCE = [
	'# A generic proposal', '',
	'Companion artifact: [constellation](research-concept-r01.graph.html), built from `research-concept-r01.sky.json`.', '',
	'## Alpha', '', 'Old alpha body.', '',
	'## Tail', '', 'Keep suffix exactly.', '',
].join('\n');

async function successor(source, query, replacement) {
	const root = await seed(source);
	const before = await readFile(path.join(root, 'proposals', R01));
	const state = await v2.loadDocumentState(root, R01);
	const gate = v2.ambiguityGate(v2.resolveSuccessorTarget(state, query).candidates);
	assert.ok(gate.candidate, gate.question);
	const request = { operation: 'CREATE_SUCCESSOR', sourceFilename: R01, instruction: `Modifica la sección ${query}.`, selectedEntryId: query, resolvedDecisions: [{ kind: 'replace', targetEntryId: gate.candidate.entryId, replacementText: replacement }] };
	const session = serve(root, `stale-companion-${query}`);
	try {
		const preview = await session.send(request);
		assert.equal(preview.status, 'awaiting_acceptance', JSON.stringify(preview));
		const published = await session.send({ ...request, acceptSuccessor: true, successorAcceptanceToken: preview.acceptanceToken });
		assert.equal(published.status, 'published', JSON.stringify(published));
		const receipt = JSON.parse(await readFile(v2.receiptPath(root, R02), 'utf8'));
		const body = await readFile(path.join(root, 'proposals', R02), 'utf8');
		assert.deepEqual(await readFile(path.join(root, 'proposals', R01)), before, 'the source revision is immutable');
		return { preview, published, receipt, body, root };
	} finally { session.close(); }
}

test('a successor that inherits a link to the previous revision\'s companion artifacts is flagged at preview, on publish and in the receipt', async () => {
	const { preview, published, receipt, body, root } = await successor(SOURCE, 'Alpha', '## Alpha\n\nNew alpha body.\n\n');
	const expected = [
		{ reference: 'research-concept-r01.graph.html', revision: R01, inherited: true },
		{ reference: 'research-concept-r01.sky.json', revision: R01, inherited: true },
	];
	assert.deepEqual(preview.staleCompanionReferences, expected);
	assert.deepEqual(published.staleCompanionReferences, expected);
	assert.deepEqual(receipt.staleCompanionReferences, expected);
	assert.ok(body.includes('research-concept-r01.graph.html'), 'the engine flags the line; it never rewrites it in silence');
	// The receipt is read back on every load of the successor; the optional key must not break that.
	const reloaded = await v2.loadDerivedState(root, R02, published.targetSha256, v2.PARSER_VERSION);
	assert.ok(reloaded, 'a receipt carrying the key validates on read');
});

test('a deliberate substitution of the link inside the locus clears the flag, and the receipt carries no key', async () => {
	const { preview, receipt, body } = await successor(SOURCE, 'A generic proposal', '# A generic proposal\n\nCompanion artifact: [constellation](research-concept-r02.graph.html), built from `research-concept-r02.sky.json`.\n\n');
	assert.equal(preview.staleCompanionReferences, undefined, JSON.stringify(preview.staleCompanionReferences));
	assert.equal(Object.hasOwn(receipt, 'staleCompanionReferences'), false);
	assert.ok(body.includes('research-concept-r02.graph.html'));
});

test('a reference written inside the locus to another revision\'s artifact is flagged as not inherited', async () => {
	const { preview } = await successor(SOURCE.replace(/Companion artifact:.*\n/u, 'No link yet.\n'), 'Alpha', '## Alpha\n\nSee research-concept-r01.graph.html for the old picture.\n\n');
	assert.deepEqual(preview.staleCompanionReferences, [{ reference: 'research-concept-r01.graph.html', revision: R01, inherited: false }]);
});

test('a citation of another revision\'s managed document is not a companion artifact', async () => {
	const { preview } = await successor(SOURCE.replace(/Companion artifact:.*\n/u, 'Supersedes research-concept-r01.md in part.\n'), 'Alpha', '## Alpha\n\nNew alpha body.\n\n');
	assert.equal(preview.staleCompanionReferences, undefined);
});
