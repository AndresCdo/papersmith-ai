// The instruction cap: 65,536 characters, stated, enforced on every path, and reported.
//
// `proposal_deliberation_execute` declared `instruction` as `maxLength: 65536` in its TypeBox
// schema, but the CLI host calls `tool.execute` directly and no validating dispatcher reads that
// schema on this path. So the cap a Pi session met never existed for `cli.mjs`, no document said
// it existed at all, and a caller had no way to see how much room an instruction (for
// `CREATE_INITIAL_REVISION`, the whole idea) had left.
//
// Now: one constant, enforced inside `tool.execute` (so both hosts refuse the same way, with
// nothing written), and an `instructionBudget` `{ limit, used, remaining }` on the successor
// preview and on the first revision's result.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, readdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const engineDir = path.resolve('skills/_core/deliberation/engine');
const cliPath = path.resolve('skills/proposal-deliberation/cli.mjs');
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const workspaceModule = await jiti.import(path.join(engineDir, 'proposal-workspace.ts'));
const v2 = await jiti.import(path.join(engineDir, 'exports.ts'));

const LIMIT = 65_536;

async function freshRoot() {
	const root = await mkdtemp(path.join(os.tmpdir(), 'deliberation-instruction-budget-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	return root;
}

function oneShot(root, request) {
	return new Promise((resolve, reject) => {
		const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root };
		const child = spawn(process.execPath, [cliPath], { cwd: root, env, stdio: ['pipe', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', (chunk) => { out += chunk; });
		child.on('error', reject);
		child.on('close', (code) => {
			try { resolve({ code, body: JSON.parse(out) }); } catch (error) { reject(new Error(`unparseable: ${out}`)); }
		});
		child.stdin.end(JSON.stringify(request));
	});
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

test('the cap is one exported constant, and the tool schema declares exactly it', () => {
	assert.equal(workspaceModule.MAX_INSTRUCTION_CHARACTERS, LIMIT);
	const tools = [];
	workspaceModule.createProposalDeliberationExtension({ projectRoot: os.tmpdir() })({ registerTool: (tool) => tools.push(tool), on: () => {} });
	const tool = tools.find((candidate) => candidate.name === 'proposal_deliberation_execute');
	assert.equal(tool.parameters.properties.instruction.maxLength, LIMIT);
});

test('through the CLI, an instruction one character over the cap is refused and nothing is written', async () => {
	const root = await freshRoot();
	const idea = `Two sentences make a v1. ${'x'.repeat(LIMIT - 'Two sentences make a v1. '.length)}.`;
	assert.equal(idea.length, LIMIT + 1);
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: idea });
	assert.equal(body.status, 'blocked', JSON.stringify(body).slice(0, 400));
	assert.equal(body.mutations, 0);
	assert.deepEqual(body.blockers.map((b) => b.code), ['INSTRUCTION_TOO_LONG']);
	assert.match(body.blockers[0].message, /65536/);
	assert.deepEqual(body.instructionBudget, { limit: LIMIT, used: LIMIT + 1, remaining: -1 });
	assert.deepEqual(await readdir(path.join(root, 'proposals')), []);
});

test('an instruction exactly at the cap is not refused for its length', async () => {
	// One sentence on purpose: the refusal that answers is the engine's own next check,
	// `INITIAL_IDEA_SINGLE_SENTENCE`, reached cheaply -- which is only possible once the
	// length check has let the instruction through.
	const root = await freshRoot();
	const idea = 'x'.repeat(LIMIT);
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: idea });
	assert.deepEqual(body.blockers?.map((b) => b.code), ['INITIAL_IDEA_SINGLE_SENTENCE'], JSON.stringify(body).slice(0, 400));
});

test('the first revision reports how much of the cap its idea used', async () => {
	const root = await freshRoot();
	const idea = 'A bounded tutor for proof drafts. It names the step it doubts.';
	const { body } = await oneShot(root, { operation: 'CREATE_INITIAL_REVISION', instruction: idea });
	assert.equal(body.status, 'created', JSON.stringify(body));
	assert.deepEqual(body.instructionBudget, { limit: LIMIT, used: idea.length, remaining: LIMIT - idea.length });
});

test('the successor preview reports the remaining instruction budget', async () => {
	const root = await freshRoot();
	await workspaceModule.createProposalWorkspaceTool(root).execute('seed', { action: 'write', resource: 'proposal', slug: 'r01', content: '# A generic proposal\n\n## Alpha\n\nOld alpha body.\n\n## Tail\n\nKeep suffix exactly.\n' });
	const state = await v2.loadDocumentState(root, 'research-concept-r01.md');
	const gate = v2.ambiguityGate(v2.resolveSuccessorTarget(state, 'Alpha').candidates);
	assert.ok(gate.candidate, gate.question);
	const instruction = 'Rewrite the Alpha section body.';
	const session = serve(root, 'instruction-budget');
	try {
		const preview = await session.send({ operation: 'CREATE_SUCCESSOR', sourceFilename: 'research-concept-r01.md', instruction, selectedEntryId: 'Alpha', resolvedDecisions: [{ kind: 'replace', targetEntryId: gate.candidate.entryId, replacementText: '## Alpha\n\nNew alpha body.\n\n' }] });
		assert.equal(preview.status, 'awaiting_acceptance', JSON.stringify(preview));
		assert.deepEqual(preview.instructionBudget, { limit: LIMIT, used: instruction.length, remaining: LIMIT - instruction.length });
	} finally { session.close(); }
});
