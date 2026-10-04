/// <reference types="node" />
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { composite, contrastRatio, parseColor, type Rgba } from './test/color';

const css = readFileSync(join(process.cwd(), 'src', 'styles.css'), 'utf8');

/** The text of the first `:root { ... }` block and everything outside it. */
function splitRoot(source: string): { root: string; rest: string } {
  const start = source.indexOf(':root');
  const open = source.indexOf('{', start);
  const close = source.indexOf('}', open);
  return { root: source.slice(open + 1, close), rest: source.slice(0, start) + source.slice(close + 1) };
}

const stripped = css.replace(/\/\*[\s\S]*?\*\//g, '');
const { root, rest } = splitRoot(stripped);

const tokens = new Map<string, string>();
for (const match of root.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
  tokens.set(match[1], match[2].trim());
}

function token(name: string): string {
  const value = tokens.get(name);
  if (value === undefined) throw new Error(`missing token ${name}`);
  return value;
}

/** Resolve a token to an opaque colour, compositing translucent values over `backdrop`. */
function resolve(name: string, backdrop = '--bg-panel'): Rgba {
  const color = parseColor(token(name));
  return color.a < 1 ? composite(color, resolve(backdrop)) : color;
}

const NAMED_COLORS = new Set(
  (
    'aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood ' +
    'cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod ' +
    'darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon ' +
    'darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray ' +
    'dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green ' +
    'greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon ' +
    'lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon ' +
    'lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen ' +
    'magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue ' +
    'mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy ' +
    'oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred ' +
    'papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon ' +
    'sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue ' +
    'tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen'
  ).split(' '),
);

/** Every declaration value outside `:root`, with var(...) references and strings removed. */
function declarationValues(source: string): string[] {
  const values: string[] = [];
  for (const match of source.matchAll(/(?:^|[;{\s])([a-z-]+)\s*:\s*([^;{}]+)(?=[;}])/g)) {
    values.push(match[2].replace(/var\([^)]*\)/g, '').replace(/(["']).*?\1/g, ''));
  }
  return values;
}

describe('light theme stylesheet', () => {
  it('declares every colour only as a token inside :root', () => {
    const offenders: string[] = [];
    for (const value of declarationValues(rest)) {
      if (/#[0-9a-f]{3,8}\b/i.test(value)) offenders.push(value.trim());
      if (/\b(?:rgb|rgba|hsl|hsla)\(/i.test(value)) offenders.push(value.trim());
      for (const word of value.match(/[a-z]+/gi) ?? []) {
        if (NAMED_COLORS.has(word.toLowerCase())) offenders.push(value.trim());
      }
    }
    expect(offenders).toEqual([]);
  });

  it('defines the extra theme tokens', () => {
    for (const name of [
      '--graph-bg',
      '--node-bg',
      '--edge',
      '--edge-label-bg',
      '--overlay',
      '--shadow',
      '--terminal-bg',
      '--terminal-text',
      '--ok-border',
      '--warn-border',
      '--bad-border',
      '--accent-border',
      '--sealed-border',
    ]) {
      expect(tokens.has(name), name).toBe(true);
    }
  });
});

describe('contrast (WCAG AA)', () => {
  const ratio = (fg: string, bg: string, backdrop?: string) =>
    contrastRatio(resolve(fg, backdrop), resolve(bg, backdrop));

  it.each(['--bg', '--bg-panel', '--bg-elevated', '--bg-input'])('text on %s reaches 4.5:1', (bg) => {
    expect(ratio('--text', bg)).toBeGreaterThanOrEqual(4.5);
  });

  it('muted text on the panel reaches 4.5:1', () => {
    expect(ratio('--text-muted', '--bg-panel')).toBeGreaterThanOrEqual(4.5);
  });

  it('dim text on the panel reaches 3:1', () => {
    expect(ratio('--text-dim', '--bg-panel')).toBeGreaterThanOrEqual(3);
  });

  it.each([
    ['--ok', '--ok-soft'],
    ['--warn', '--warn-soft'],
    ['--bad', '--bad-soft'],
    ['--sealed', '--sealed-soft'],
    ['--accent', '--accent-soft'],
  ])('badge text %s on its composited %s fill reaches 4.5:1', (fg, soft) => {
    expect(ratio(fg, soft)).toBeGreaterThanOrEqual(4.5);
  });

  it('the strong border against the panel reaches 3:1', () => {
    expect(ratio('--border-strong', '--bg-panel')).toBeGreaterThanOrEqual(3);
  });

  it('node text on the node background reaches 4.5:1', () => {
    expect(ratio('--text', '--node-bg')).toBeGreaterThanOrEqual(4.5);
    expect(ratio('--text-muted', '--node-bg')).toBeGreaterThanOrEqual(4.5);
  });

  it('edge label text on the label background reaches 4.5:1', () => {
    expect(ratio('--text-muted', '--edge-label-bg', '--graph-bg')).toBeGreaterThanOrEqual(4.5);
  });

  it('terminal text on the terminal background reaches 4.5:1', () => {
    expect(ratio('--terminal-text', '--terminal-bg')).toBeGreaterThanOrEqual(4.5);
  });
});

describe('mutating cue', () => {
  const rule = /\.dag-node\.is-mutating\s*\{([^}]*)\}/.exec(stripped);
  const focus = /\.react-flow__node:focus-visible \.dag-node\s*\{([^}]*)\}/.exec(stripped);

  it('draws a dashed token-based outline so it reads on the light theme', () => {
    expect(rule).not.toBeNull();
    expect(rule?.[1]).toMatch(/outline:\s*\d+px dashed var\(--accent\)/);
  });

  it('differs from the solid keyboard focus outline', () => {
    expect(focus).not.toBeNull();
    expect(focus?.[1]).toMatch(/outline:\s*2px solid var\(--accent\)/);
    expect(focus?.[1]).toMatch(/outline-offset:\s*2px/);
    const outline = (body: string) => /outline:\s*([^;]+);/.exec(body)?.[1];
    const offset = (body: string) => /outline-offset:\s*([^;]+);/.exec(body)?.[1];
    expect(outline(rule?.[1] ?? '')).not.toBe(outline(focus?.[1] ?? ''));
    expect(offset(rule?.[1] ?? '')).not.toBe(offset(focus?.[1] ?? ''));
  });
});

describe('element panel on narrow viewports', () => {
  const sheet = /@media \(max-width: 899px\)\s*\{\s*\.element-panel\s*\{([^}]*)\}/.exec(stripped);

  it('becomes a full-width bottom sheet capped at 60vh and scrollable under 900px', () => {
    expect(sheet).not.toBeNull();
    const body = sheet?.[1] ?? '';
    expect(body).toMatch(/top:\s*auto/);
    expect(body).toMatch(/left:\s*0/);
    expect(body).toMatch(/width:\s*auto/);
    expect(body).toMatch(/max-height:\s*60vh/);
    expect(body).toMatch(/overflow-y:\s*auto/);
  });

  it('swaps the drawer left border for a top border using tokens only', () => {
    const body = sheet?.[1] ?? '';
    expect(body).toMatch(/border-top:\s*1px solid var\(--border-strong\)/);
    expect(body).toMatch(/border-left:\s*none/);
  });
});
