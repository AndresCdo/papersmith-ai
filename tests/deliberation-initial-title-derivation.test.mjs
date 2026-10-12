// How v1's title and section heading are derived from the idea text.
//
// `CREATE_INITIAL_REVISION` takes the document title from the idea's first sentence and the
// section heading from its second, then writes the idea itself, verbatim, as the section body.
// The sentence splitter keeps each sentence's terminal punctuation, so before this fix a
// two-sentence idea produced `# A tutor that refutes weak proofs.` -- a heading ending in a
// full stop, which no heading in a managed document is meant to carry and which every later
// `RESOLVE_TARGET` query had to work around (the resolver truncates a query at its first `.`).
//
// What stays deliberate, and is held here so a later "cleanup" cannot silently undo it:
//   - the section heading comes from the SECOND sentence (the single-sentence refusal relies on
//     it: one sentence would collapse `#` and `##` into identical bytes);
//   - the idea is repeated verbatim as the body, because the headings are derived labels capped
//     at 200 characters and the body is the only place the author's whole text survives.
import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const { createJiti } = await import('jiti');
const jiti = createJiti(import.meta.url);
const v2 = await jiti.import(path.join(root, 'skills/_core/deliberation/engine/exports.ts'));

test('the title and section heading drop the terminal punctuation of their sentence', () => {
	const renderer = new v2.InitialRevisionRenderer();
	const composed = renderer.renderFromIdea({ idea: 'Does a shared code transfer across sites? It is measured on two held-out sites!' });
	assert.deepEqual(composed.canonicalMetadata, {
		schemaVersion: 1,
		title: 'Does a shared code transfer across sites',
		sectionHeading: 'It is measured on two held-out sites',
	});
	assert.ok(composed.markdown.startsWith('# Does a shared code transfer across sites\n\n## It is measured on two held-out sites\n\n'));
});

test('the idea body stays verbatim, punctuation included, under the derived headings', () => {
	const renderer = new v2.InitialRevisionRenderer();
	const idea = 'A tutor that refutes weak proofs. It should also cite prior work.';
	const composed = renderer.renderFromIdea({ idea });
	assert.equal(composed.markdown, `# A tutor that refutes weak proofs\n\n## It should also cite prior work\n\n${idea}\n`);
});

test('the slug is unchanged by the stripped punctuation', () => {
	const renderer = new v2.InitialRevisionRenderer();
	assert.equal(renderer.renderFromIdea({ idea: 'A tutor that refutes weak proofs. It cites prior work.' }).slug, 'a-tutor-that-refutes-weak-proofs');
});

test('punctuation inside a sentence is kept; only the terminal run is stripped', () => {
	const renderer = new v2.InitialRevisionRenderer();
	const composed = renderer.renderFromIdea({ idea: 'Version 2.1 of the sampler, revisited... Why does it drift?!' });
	assert.equal(composed.canonicalMetadata.title, 'Version 2.1 of the sampler, revisited');
	assert.equal(composed.canonicalMetadata.sectionHeading, 'Why does it drift');
});

test('two sentences that differ only in their terminal punctuation still count as one heading, and are refused', async () => {
	const published = [];
	const service = new v2.InitialRevisionCreationService(
		{ hasManagedProposal: async () => false },
		{ async publish(candidate) { published.push(candidate); return { filename: candidate.filename, revision: candidate.revision, documentSha256: 'x', bytesWritten: 0 }; } },
	);
	const result = await service.execute({ idea: 'Shared latent code! Shared latent code?' });
	assert.equal(result.status, 'blocked');
	assert.equal(result.code, 'INITIAL_IDEA_SINGLE_SENTENCE');
	assert.equal(published.length, 0);
});
