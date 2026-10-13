// B3: a successor locus is matched by its heading's own tokens, and an outer
// section stays reachable when a nested heading shares its words.
//
// The defects this file pins (all reproduced on 0.13.0):
//   - heading words matched as substrings, so `O1` also hit `O10` and the
//     query blocked as ambiguous;
//   - two headings carrying the same words (`Alignment loss` and
//     `Alignment loss weighting`) tied, even when one IS the query;
//   - nested matches collapsed to the innermost one, so `## Data` could not be
//     targeted at all once `### Synthetic data` existed, and a label line
//     directly under `## Data` (`**Dataset:**`) could not be edited;
//   - the ambiguity menu named neither a candidate's level nor its real
//     heading path.
// Every fixture is generic; no document here belongs to a paper.
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdir, mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const engineDir = path.resolve('skills/_core/deliberation/engine');
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const workspaceModule = await jiti.import(path.join(engineDir, 'proposal-workspace.ts'));
const v2 = await jiti.import(path.join(engineDir, 'exports.ts'));

async function seed(content) {
	const root = await mkdtemp(path.join(os.tmpdir(), 'pp-heading-target-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	await workspaceModule.createProposalWorkspaceTool(root).execute('seed', { action: 'write', resource: 'proposal', slug: 'r01', content });
	return root;
}

const FILENAME = 'research-concept-r01.md';

async function resolve(content, query) {
	const root = await seed(content);
	const state = await v2.loadDocumentState(root, FILENAME);
	const resolution = v2.resolveSuccessorTarget(state, query);
	const gate = v2.ambiguityGate(resolution.candidates);
	const text = gate.candidate ? state.documentBytes.subarray(gate.candidate.composite.startByte, gate.candidate.composite.endByte).toString('utf8') : null;
	return { resolution, gate, text, root };
}

const OBJECTIVES = [
	'# Title', '', 'Intro.', '',
	'## Objectives', '', 'Overview.', '',
	'### O1. First aim', '', 'Aim one body.', '',
	'### O10. Tenth aim', '', 'Aim ten body.', '',
].join('\n');

test('an identifier token matches its own heading only: O1 never matches O10', async () => {
	const { gate, text } = await resolve(OBJECTIVES, 'O1');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('### O1. First aim'), text);
	assert.ok(!text.includes('O10'), text);
});

test('an identifier declared inside a heading stays a whole-token handle: E1 never matches E10', async () => {
	const doc = ['# Plan', '', 'Intro.', '', '## Experiment [exp:E1] — Baseline run', '', 'A.', '', '## Experiment [exp:E10] — Ablation run', '', 'B.', ''].join('\n');
	const { gate, text } = await resolve(doc, 'E1');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Experiment [exp:E1] — Baseline run'), text);
});

test('a word matches a whole heading token, never a substring of one', async () => {
	const doc = ['# Title', '', 'Intro.', '', '## Misalignment', '', 'A.', '', '## Alignment', '', 'B.', ''].join('\n');
	const { gate, text, resolution } = await resolve(doc, 'Alignment');
	assert.equal(resolution.candidates.length, 1, JSON.stringify(resolution.candidates.map(c => c.headingPath)));
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Alignment\n'), text);
});

test('a hyphenated heading word stays reachable by each of its parts', async () => {
	const doc = ['# Title', '', 'Intro.', '', '## Cross-entropy objective', '', 'A.', '', '## Other', '', 'B.', ''].join('\n');
	const { gate, text } = await resolve(doc, 'entropy');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Cross-entropy objective'), text);
});

test('a heading that is exactly the query outranks one that merely contains its words', async () => {
	const doc = ['# Title', '', 'Intro.', '', '## Alignment loss weighting', '', 'A.', '', '## Alignment loss', '', 'B.', ''].join('\n');
	const { gate, text } = await resolve(doc, 'Alignment loss');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Alignment loss\n'), text);
	const weighting = await resolve(doc, 'Alignment loss weighting');
	assert.ok(weighting.text.startsWith('## Alignment loss weighting'), weighting.text);
});

test('an exact match ignores the section label and the heading stopwords', async () => {
	const doc = ['# Title', '', 'Intro.', '', '## 5. Normalization of the terms', '', 'A.', '', '## 6. Normalization schedule', '', 'B.', ''].join('\n');
	const { gate, text } = await resolve(doc, 'Normalization terms');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## 5. Normalization of the terms'), text);
});

const NESTED = [
	'# Title', '', 'Intro.', '',
	'## Data', '', '**Dataset:** a placeholder corpus.', '',
	'### Synthetic data', '', 'Generated samples.', '',
	'## Results', '', 'Numbers.', '',
].join('\n');

test('level marks target the outer section even when a nested heading shares its words', async () => {
	const { gate, text } = await resolve(NESTED, '## Data');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Data\n\n**Dataset:**'), text);
	assert.ok(text.includes('### Synthetic data'), 'the outer section spans its subsection');
	assert.ok(!text.includes('## Results'), text);
});

test('a plain query naming the outer heading exactly no longer collapses to the inner one', async () => {
	const { gate, text } = await resolve(NESTED, 'Data');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('## Data\n'), text);
});

test('the inner section stays reachable by its own heading', async () => {
	const { gate, text } = await resolve(NESTED, 'Synthetic data');
	assert.equal(gate.blocked, false, gate.question);
	assert.ok(text.startsWith('### Synthetic data'), text);
	const leveled = await resolve(NESTED, '### Synthetic data');
	assert.ok(leveled.text.startsWith('### Synthetic data'), leveled.text);
});

test('level marks restrict the match to headings of that level', async () => {
	const { resolution } = await resolve(NESTED, '#### Data');
	assert.equal(resolution.candidates.length, 0);
	assert.equal(resolution.reason, 'SUCCESSOR_TARGET_NOT_FOUND');
});

const TWIN = [
	'# Title', '', 'Intro.', '',
	'## Methods', '', 'M.', '', '### Setup', '', 'Method setup.', '',
	'## Results', '', 'R.', '', '### Setup', '', 'Result setup.', '',
].join('\n');

test('an ambiguity names every candidate with its level and real heading path', async () => {
	const { gate } = await resolve(TWIN, 'Setup');
	assert.equal(gate.blocked, true);
	assert.equal(gate.candidates.length, 2);
	assert.match(gate.question, /### Title › Methods › Setup/u);
	assert.match(gate.question, /### Title › Results › Setup/u);
	for (const candidate of gate.candidates) {
		assert.equal(candidate.headingLevel, 3);
		assert.equal(candidate.headingPath.at(-1), 'Setup');
	}
});

test('nested candidates within the margin block instead of resolving to the innermost in silence', async () => {
	const doc = ['# Title', '', 'Intro.', '', '## Loss functions', '', 'A.', '', '### Alignment loss', '', 'B.', ''].join('\n');
	const { gate } = await resolve(doc, 'loss');
	assert.equal(gate.blocked, true);
	assert.match(gate.question, /## Title › Loss functions/u);
	assert.match(gate.question, /### Title › Loss functions › Alignment loss/u);
});

test('RESOLVE_TARGET over the CLI resolves level marks and lists candidates when blocked', async () => {
	const root = await seed(NESTED);
	const env = { ...process.env, PROPOSAL_DELIBERATION_PROJECT_ROOT: root, PROPOSAL_DELIBERATION_SESSION_ID: 'heading-target' };
	delete env.ANTHROPIC_API_KEY;
	const run = async request => JSON.parse((await execFileAsync(process.execPath, [path.join(engineDir, 'cli.mjs'), JSON.stringify(request)], { cwd: engineDir, env })).stdout);
	const outer = await run({ operation: 'RESOLVE_TARGET', sourceFilename: FILENAME, query: '## Data' });
	assert.equal(outer.blocked, false, outer.question);
	assert.ok(outer.text.startsWith('## Data\n\n**Dataset:**'), outer.text);
	const twinRoot = await seed(TWIN);
	const blocked = JSON.parse((await execFileAsync(process.execPath, [path.join(engineDir, 'cli.mjs'), JSON.stringify({ operation: 'RESOLVE_TARGET', sourceFilename: FILENAME, query: 'Setup' })], { cwd: engineDir, env: { ...env, PROPOSAL_DELIBERATION_PROJECT_ROOT: twinRoot } })).stdout);
	assert.equal(blocked.blocked, true);
	assert.deepEqual(blocked.candidates.map(c => [c.headingLevel, c.headingPath.join(' › ')]), [[3, 'Title › Methods › Setup'], [3, 'Title › Results › Setup']]);
	for (const c of blocked.candidates) assert.match(c.entryId, /^composite:/u);
});
