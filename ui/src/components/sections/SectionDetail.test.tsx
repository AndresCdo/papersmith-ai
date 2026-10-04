import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import SectionDetail from './SectionDetail';
import { draftingSection } from './fixtures';

describe('SectionDetail', () => {
  it('shows the contract fields of the section', () => {
    render(<SectionDetail section={draftingSection} />);
    expect(screen.getByText('paper/sections/related.md')).toBeInTheDocument();
    expect(screen.getByText('300–600 words')).toBeInTheDocument();
    expect(screen.getByText('1/2 written')).toBeInTheDocument();
    expect(screen.getByText('smith2020')).toBeInTheDocument();
  });

  it('lists blocks with their written state and the fact contract', () => {
    render(<SectionDetail section={draftingSection} />);
    expect(screen.getByText('WRITTEN')).toBeInTheDocument();
    expect(screen.getByText('PENDING')).toBeInTheDocument();
    expect(screen.getByText('OPTIONAL')).toBeInTheDocument();
    const produces = screen.getByRole('heading', { name: 'Produces' }).parentElement as HTMLElement;
    expect(within(produces).getByText('f1')).toBeInTheDocument();
  });

  it('says so when no citation key is unresolved', () => {
    render(<SectionDetail section={{ ...draftingSection, citations: { verified: 1, placeholders: 0 } }} />);
    expect(screen.getByText('No unresolved citation keys.')).toBeInTheDocument();
  });
});
