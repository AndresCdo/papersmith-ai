// A successor receipt can say why the change was made and who decided it.
//
// A published successor's receipt recorded an `instructionHash` and nothing else about the
// decision behind it: the instruction itself is not kept, so a later reader of
// `<sidecarRoot>/receipts/<file>.json` could tell THAT a revision was made but not why, nor
// whether a person or an agent took the call. Two optional request fields now travel into the
// receipt as recorded: `rationale` (free text, at most 2000 characters) and `decider`
// (`"agent"` or `"human"`). Both are optional and additive: a receipt without them -- every
// receipt written before this change -- is exactly as valid as before.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readdir, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const engineDir = path.resolve('skills/_core/deliberation/engine');
const cliPath = path.resolve('skills/proposal-deliberation/cli.mjs');
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const workspaceModule = await jiti.import(path.join(engineDir, 'proposal-workspace.ts'));
const v2 = await jiti.import(path.join(engineDir, 'exports.ts'));

const R01 = 'research-concept-r01.md';
const R02 = 'research-concept-r02.md';

async function seed() {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-decision-record-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	await workspaceModule.createProposalWorkspaceTool(root).execute('seed', { action: 'write', resource: 'proposal', slug: 'r01', content: '# A generic proposal\n\n## Alpha\n\nOld alpha body.\n\n## Tail\n\nKeep suffix exactly.\n' });
	return root;
}

function serve(root, sessionId) {
	const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root, PROPOSAL_DELIBERATION_SESSION_ID: sessionId };
	const child = spawn(process.execPath, [cliPath, '--serve'], { cwd: root, env, stdio: ['pipe', 'pipe', 'pipe'] });
	const lines = [];
	let buffer = '';
	child.stdout.on('data', (chunk) => {
		buffer += chunk.toString('utf8');
		let index;
		while ((index = buffer.indexOf('\n')) !== -1) {
			const line = buffer.slice(0, index).trim();
			buffer = buffer.slice(index + 1);
			if (line) lines.push(JSON.parse(line));
		}
	});
	const send = async (request) => {
		const at = lines.length;
		child.stdin.write(`${JSON.stringify(request)}\n`);
		const deadline = Date.now() + 30000;
		while (lines.length <= at) {
			if (Date.now() > deadline) throw new Error('serve timeout');
			await new Promise((resolve) => setTimeout(resolve, 20));
		}
		return lines[at];
	};
	return { send, close: () => { child.stdin.end(); child.kill(); } };
}

async function request(root, extra) {
	const state = await v2.loadDocumentState(root, R01);
	const gate = v2.ambiguityGate(v2.resolveSuccessorTarget(state, 'Alpha').candidates);
	assert.ok(gate.candidate, gate.question);
	return { operation: 'CREATE_SUCCESSOR', sourceFilename: R01, instruction: 'Rewrite the Alpha section body.', selectedEntryId: 'Alpha', resolvedDecisions: [{ kind: 'replace', targetEntryId: gate.candidate.entryId, replacementText: '## Alpha\n\nNew alpha body.\n\n' }], ...extra };
}

async function publish(root, extra) {
	const session = serve(root, `decision-record-${Math.random().toString(36).slice(2)}`);
	try {
		const body = await request(root, extra);
		const preview = await session.send(body);
		if (preview.status !== 'awaiting_acceptance') return { preview };
		const published = await session.send({ ...body, acceptSuccessor: true, successorAcceptanceToken: preview.acceptanceToken });
		return { preview, published };
	} finally { session.close(); }
}

test('a rationale and a decider supplied with the successor are recorded in its receipt', async () => {
	const root = await seed();
	const { published } = await publish(root, { rationale: 'The old body overstated what the section shows.', decider: 'human' });
	assert.equal(published.status, 'published', JSON.stringify(published));
	const receipt = JSON.parse(await readFile(v2.receiptPath(root, R02), 'utf8'));
	assert.equal(receipt.rationale, 'The old body overstated what the section shows.');
	assert.equal(receipt.decider, 'human');
	assert.ok(receipt.instructionHash, 'the instruction hash is still recorded');
	assert.ok(await v2.loadDerivedState(root, R02, published.targetSha256, v2.PARSER_VERSION), 'a receipt carrying the fields validates on read');
});

test('a successor without them records neither key, and its receipt validates as every older receipt does', async () => {
	const root = await seed();
	const { published } = await publish(root, {});
	assert.equal(published.status, 'published', JSON.stringify(published));
	const receipt = JSON.parse(await readFile(v2.receiptPath(root, R02), 'utf8'));
	assert.equal(Object.hasOwn(receipt, 'rationale'), false);
	assert.equal(Object.hasOwn(receipt, 'decider'), false);
	assert.ok(await v2.loadDerivedState(root, R02, published.targetSha256, v2.PARSER_VERSION));
	const audit = await v2.runConsistencyAudit({ projectRoot: root });
	assert.equal(audit.status, 'PASS', JSON.stringify(audit.failures));
});

for (const [label, extra] of [
	['an unknown decider', { decider: 'committee' }],
	['an empty rationale', { rationale: '   ' }],
	['an over-long rationale', { rationale: 'x'.repeat(2001) }],
	['a non-string rationale', { rationale: 42 }],
]) {
	test(`${label} is refused at the preview, before any token or write`, async () => {
		const root = await seed();
		const { preview, published } = await publish(root, extra);
		assert.equal(published, undefined);
		assert.equal(preview.status, 'blocked', JSON.stringify(preview));
		assert.deepEqual(preview.blockers.map((b) => b.code), ['DECISION_RECORD_INVALID']);
		assert.deepEqual((await readdir(path.join(root, 'proposals'))).sort(), [R01]);
	});
}

test('the fields on an operation that writes no successor receipt are refused rather than dropped', async () => {
	const root = await seed();
	const session = serve(root, 'decision-record-other');
	try {
		const body = await session.send({ operation: 'CREATE_INITIAL_REVISION', instruction: 'A tutor. It refutes.', decider: 'agent' });
		assert.equal(body.status, 'blocked', JSON.stringify(body));
		assert.deepEqual(body.blockers.map((b) => b.code), ['DECISION_RECORD_UNSUPPORTED']);
	} finally { session.close(); }
});
