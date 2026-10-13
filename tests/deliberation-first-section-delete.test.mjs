// X1: deleting a document's FIRST section was refused as
// `successor-markdown-block-safety`. A managed revision opens with the artifact
// marker line followed by ONE newline, so the deletion left the marker and the
// next heading one line break apart, and the removal-join check (which wants a
// blank line between the bytes before and after a removed block) refused it.
// The marker is an HTML comment line, never a block a heading could fuse
// into; the same single-newline join with ordinary prose on the left is still
// refused. Every fixture is generic.
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const engineDir = path.resolve('skills/_core/deliberation/engine');
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const workspaceModule = await jiti.import(path.join(engineDir, 'proposal-workspace.ts'));
const v2 = await jiti.import(path.join(engineDir, 'exports.ts'));
const { artifact } = await jiti.import(path.join(engineDir, 'artifact-naming.ts'));

const R01 = 'research-concept-r01.md';
const R02 = 'research-concept-r02.md';
const ctx = { sessionManager: { getSessionId: () => 'first-section-delete' }, hasUI: false, ui: { confirm: async () => false } };

async function seed(content) {
	const root = await mkdtemp(path.join(os.tmpdir(), 'pp-first-section-delete-'));
	await mkdir(path.join(root, 'proposals'), { recursive: true });
	await workspaceModule.createProposalWorkspaceTool(root).execute('seed', { action: 'write', resource: 'proposal', slug: 'r01', content });
	const tools = [];
	workspaceModule.createProposalDeliberationExtension({ projectRoot: root })({ registerTool: tool => tools.push(tool), on: () => {} });
	return { root, tool: tools.find(tool => tool.name === 'proposal_deliberation_execute') };
}

async function deleteSection(content, query) {
	const { root, tool } = await seed(content);
	const state = await v2.loadDocumentState(root, R01);
	const gate = v2.ambiguityGate(v2.resolveSuccessorTarget(state, query).candidates);
	assert.ok(gate.candidate, gate.question);
	const request = {
		operation: 'CREATE_SUCCESSOR', editIntent: 'DELETE', sourceFilename: R01,
		instruction: `Elimina la sección ${query}.`, selectedEntryId: query,
		resolvedDecisions: [{ kind: 'delete', targetEntryId: gate.candidate.entryId, instructionEvidence: `Elimina la sección ${query}.`, reason: 'requested' }],
	};
	const run = async body => (await tool.execute('call', body, undefined, undefined, ctx)).details;
	return { root, state, gate, request, run };
}

/** The bare derive_successor manifest check, on the exact bytes of one section removed. */
function refusalOf(state, sectionText) {
	const source = state.documentBytes.toString('utf8');
	return workspaceModule.successorCandidateRefusal(source, state.documentSha256, [{ id: 'p1', kind: 'replace', oldText: sectionText, newText: '' }]).refusal;
}

const DOC = '# 1 Intro\n\nKeep intro.\n\n# 2 Alpha\n\nAlpha body.\n\n# 3 Tail\n\nKeep suffix exactly.\n';

test('deleting the first section of a managed revision previews and publishes', async () => {
	const { root, request, run } = await deleteSection(DOC, 'Intro');
	const preview = await run(request);
	assert.equal(preview.status, 'awaiting_acceptance', JSON.stringify(preview));
	const published = await run({ ...request, acceptSuccessor: true, successorAcceptanceToken: preview.acceptanceToken });
	assert.equal(published.status, 'published', JSON.stringify(published));
	const body = await readFile(path.join(root, 'proposals', R02), 'utf8');
	assert.equal(body, `${artifact.marker}# 2 Alpha\n\nAlpha body.\n\n# 3 Tail\n\nKeep suffix exactly.\n`);
});

test('the removal next to the marker is the only single-newline join the check admits', async () => {
	const { state } = await deleteSection(DOC, 'Intro');
	assert.equal(refusalOf(state, '# 1 Intro\n\nKeep intro.\n\n'), null, 'removing the first section is a clean join after the marker');
	// The same removal with ordinary prose on the left still fuses blocks and is refused.
	const fused = await deleteSection('# 1 Intro\n\nKeep intro.\n## 2 Alpha\n\nAlpha body.\n\n# 3 Tail\n\nKeep suffix exactly.\n', 'Alpha');
	const refusal = refusalOf(fused.state, '## 2 Alpha\n\nAlpha body.\n\n');
	assert.equal(refusal?.code, 'successor-markdown-block-safety', JSON.stringify(refusal));
	const preview = await fused.run(fused.request);
	assert.equal(preview.status, 'blocked', JSON.stringify(preview));
	assert.equal(preview.message, 'CANDIDATE_VALIDATION_FAILED');
});

test('deleting a middle section keeps working exactly as before', async () => {
	const { root, request, run } = await deleteSection(DOC, 'Alpha');
	const preview = await run(request);
	assert.equal(preview.status, 'awaiting_acceptance', JSON.stringify(preview));
	const published = await run({ ...request, acceptSuccessor: true, successorAcceptanceToken: preview.acceptanceToken });
	assert.equal(published.status, 'published', JSON.stringify(published));
	assert.equal(await readFile(path.join(root, 'proposals', R02), 'utf8'), `${artifact.marker}# 1 Intro\n\nKeep intro.\n\n# 3 Tail\n\nKeep suffix exactly.\n`);
});
