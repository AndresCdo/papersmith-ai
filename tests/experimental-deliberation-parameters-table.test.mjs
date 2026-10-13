// A parameters table declares settings the plan fixes; it is not a promise about a run.
//
// `report-table-fabricated-value` refuses any digit in a report-table body cell past column one,
// because a report table's cells are slots a future run fills. Before this change the only table
// exempt from it was a baselines table, so a plan could not state its own fixed settings -- a
// learning rate, a batch size, a seed list -- in a table at all: `| learning rate | 3e-4 |` was a
// "fabricated result" and blocked creation and every successor.
//
// A table whose FIRST header cell reads `Parameter`, `Parameters`, `Hyperparameter` or
// `Hyperparameters` (case-insensitively, the whole cell) is now a parameters table: a declaration,
// exempt from the rule. The guard stays fail-closed for everything else: a header merely
// containing the word, or any other first header cell, keeps today's behaviour.
import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';
import { pathToFileURL } from 'node:url';

const repoRoot = process.cwd();
const { createJiti } = await import(pathToFileURL(path.join(repoRoot, 'node_modules/jiti/lib/jiti.mjs')).href);
const jiti = createJiti(import.meta.url, { alias: {
    '@earendil-works/pi-coding-agent': path.join(repoRoot, 'dist/index.js'),
    '@earendil-works/pi-ai': path.join(repoRoot, 'node_modules/@earendil-works/pi-ai/dist/index.js'),
    typebox: path.join(repoRoot, 'node_modules/typebox/build/index.mjs'),
} });
const { extractAtoms, violations } = await jiti.import(
    path.join(repoRoot, 'skills/experimental-deliberation/preservation-experimental.ts'));

const fabricated = (source) => violations(source).filter((entry) => entry.rule === 'report-table-fabricated-value');
const tableRules = (source) => violations(source).map((entry) => entry.rule).filter((rule) => rule.startsWith('report-table') || rule.startsWith('baseline'));
const table = (header, ...rows) => {
    const cells = header.split('|').length;
    return [`| ${header} |`, `|${' --- |'.repeat(cells)}`, ...rows.map((row) => `| ${row} |`), ''].join('\n');
};

for (const header of ['Parameter | Value', 'Parameters | Value | Range', 'Hyperparameter | Value', 'hyperparameters | Value', 'PARAMETER | Value']) {
    test(`a table headed "${header.split(' | ')[0]}" declares its values and raises no fabricated-value violation`, () => {
        const source = table(header, `learning rate | 3e-4${header.includes('Range') ? ' | 1e-5 to 1e-3' : ''}`, `batch size | 128${header.includes('Range') ? ' | 32 to 512' : ''}`);
        assert.deepEqual(fabricated(source), []);
        assert.deepEqual(tableRules(source), [], 'nor any baseline rule: a parameters table is not a baselines table');
    });
}

test('a results table with a number in a body cell is still refused', () => {
    assert.deepEqual(fabricated(table('Arm | Accuracy', 'Source only | 0.71')).map((entry) => entry.rule), ['report-table-fabricated-value']);
});

test('a first header cell that merely contains the word is not a declaration (fail-closed)', () => {
    assert.equal(fabricated(table('Parameter count | Accuracy', 'Small | 0.71')).length, 1);
    assert.equal(fabricated(table('Arm | Parameter', 'Adapted | 3e-4')).length, 1, 'only the FIRST header cell declares');
});

test('a parameters table still declares a report-table atom, so dropping it is a loss to acknowledge', () => {
    const atoms = [...extractAtoms(table('Parameter | Value', 'learning rate | 3e-4')).values()];
    assert.deepEqual(atoms.map((atom) => atom.kind), ['report-table']);
});
