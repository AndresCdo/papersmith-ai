import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import HarnessStatus from './HarnessStatus';
import type { WiringHealth } from '../../types';

const health = {
  summary: { state: 'HEALTHY', components_total: 45, components_healthy: 45, warnings: [] },
  harness_sync: { state: 'IN_SYNC', harnesses: [] },
  skills: Array.from({ length: 11 }, (_, index) => ({ id: `s${index}`, state: 'WIRED' })),
  agents: Array.from({ length: 19 }, (_, index) => ({ id: `a${index}`, state: 'WIRED' })),
  cli_entrypoints: Array.from({ length: 7 }, (_, index) => ({ id: `c${index}`, state: 'WIRED' })),
} as unknown as WiringHealth;

describe('HarnessStatus readiness rows', () => {
  it.each([
    ['skills wired', '11/11'],
    ['agents wired', '19/19'],
    ['CLI front doors', '7/7'],
  ])('separates the %s label from its %s value', (label, value) => {
    render(<HarnessStatus health={health} />);
    const row = screen.getByText(label).closest('.readiness__row') as HTMLElement;
    expect(row).not.toBeNull();
    const valueElement = within(row).getByText(value);
    expect(valueElement).toHaveClass('readiness__value');
    expect(valueElement).not.toBe(screen.getByText(label));
  });
});
