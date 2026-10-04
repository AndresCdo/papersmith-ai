import { describe, expect, it } from 'vitest';
import { formatHash, parseHash } from './hash';

describe('parseHash / formatHash', () => {
  it('parses a bare tab', () => {
    expect(parseHash('#health')).toEqual({ tab: 'health', el: null });
    expect(parseHash('sections')).toEqual({ tab: 'sections', el: null });
  });

  it('falls back to the default tab for empty and unknown fragments', () => {
    expect(parseHash('')).toEqual({ tab: 'pipeline', el: null });
    expect(parseHash('#')).toEqual({ tab: 'pipeline', el: null });
    expect(parseHash('#nope?el=stage%3Aa')).toEqual({ tab: 'pipeline', el: null });
  });

  it('knows the atlas tab and round-trips it', () => {
    expect(parseHash('#atlas')).toEqual({ tab: 'atlas', el: null });
    expect(parseHash(formatHash('atlas'))).toEqual({ tab: 'atlas', el: null });
    expect(parseHash('#atlases')).toEqual({ tab: 'pipeline', el: null });
  });

  it('knows the decisions tab and round-trips it', () => {
    expect(parseHash('#decisions')).toEqual({ tab: 'decisions', el: null });
    expect(parseHash(formatHash('decisions'))).toEqual({ tab: 'decisions', el: null });
    expect(parseHash('#decisionss')).toEqual({ tab: 'pipeline', el: null });
  });

  it('knows the preview tab and round-trips it', () => {
    expect(parseHash('#preview')).toEqual({ tab: 'preview', el: null });
    expect(parseHash(formatHash('preview'))).toEqual({ tab: 'preview', el: null });
    expect(parseHash('#previews')).toEqual({ tab: 'pipeline', el: null });
  });

  it('parses an encoded element id', () => {
    expect(parseHash('#pipeline?el=gate%3Awriting-readiness')).toEqual({
      tab: 'pipeline',
      el: 'gate:writing-readiness',
    });
  });

  it('drops a malformed or empty el', () => {
    expect(parseHash('#pipeline?el=%E0%A4%A')).toEqual({ tab: 'pipeline', el: null });
    expect(parseHash('#pipeline?el=')).toEqual({ tab: 'pipeline', el: null });
  });

  it('formats a bare tab and an element with encodeURIComponent', () => {
    expect(formatHash('health')).toBe('#health');
    expect(formatHash('pipeline', null)).toBe('#pipeline');
    expect(formatHash('pipeline', 'stage:drafting->gate:x')).toBe(
      '#pipeline?el=stage%3Adrafting-%3Egate%3Ax',
    );
  });

  it('round-trips ids with spaces, unicode and reserved characters', () => {
    for (const el of ['stage:drafting', 'edge:a->b', 'section:Related Work', 'section:Méthode 概要', 'section:a&b=c?d#e']) {
      expect(parseHash(formatHash('pipeline', el))).toEqual({ tab: 'pipeline', el });
    }
  });
});
