// Build the plausibility atlas viewer: one minified IIFE that
// skills/plausibility/scripts/render_atlas.py inlines into atlas.html.
//
//   npm run build:atlas-viewer
//
// The output is versioned so rendering stays Python stdlib-only and offline.
// Same inputs, same bytes: no timestamps, no source maps, pinned three/esbuild.
import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const assets = resolve(root, 'skills/plausibility/assets');
const outfile = resolve(assets, 'atlas3d.bundle.js');
const threeVersion = JSON.parse(
  readFileSync(resolve(root, 'node_modules/three/package.json'), 'utf8'),
).version;

const result = await build({
  entryPoints: [resolve(assets, 'atlas3d/viewer.js')],
  bundle: true,
  minify: true,
  format: 'iife',
  target: 'es2020',
  legalComments: 'none',
  sourcemap: false,
  write: false,
  banner: {
    js: `/*! atlas3d viewer for papersmith-ai plausibility. Bundles three.js ${threeVersion} `
      + '(https://threejs.org) Copyright 2010-2026 three.js authors, MIT License; '
      + 'see skills/plausibility/assets/THIRD_PARTY_NOTICES.md. Built by '
      + 'scripts/build-atlas-viewer.mjs from assets/atlas3d/viewer.js. */',
  },
});

const code = result.outputFiles[0].text;
if (/<\/script/i.test(code)) {
  console.error('ATLAS_VIEWER_UNSAFE: the bundle contains "</script" and cannot be inlined');
  process.exit(1);
}
writeFileSync(outfile, code);
const sha = createHash('sha256').update(code).digest('hex');
console.log(`ATLAS_VIEWER_BUILT: ${outfile} ${code.length} bytes sha256=${sha}`);
