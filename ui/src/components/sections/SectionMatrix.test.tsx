import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import SectionMatrix from './SectionMatrix';
import { draftingSection } from './fixtures';

describe('SectionMatrix drawer', () => {
  it('opens the section detail from the Detail button', async () => {
    render(<SectionMatrix sections={[draftingSection]} />);
    expect(screen.queryByLabelText('Section detail: Related Work')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Detail' }));
    const drawer = screen.getByLabelText('Section detail: Related Work');
    expect(drawer).toHaveTextContent('paper/sections/related.md');
    expect(drawer).toHaveTextContent('smith2020');
  });

  it('closes on Escape and on the Close button', async () => {
    render(<SectionMatrix sections={[draftingSection]} />);
    await userEvent.click(screen.getByRole('button', { name: 'Detail' }));
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByLabelText('Section detail: Related Work')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Detail' }));
    await userEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(screen.queryByLabelText('Section detail: Related Work')).not.toBeInTheDocument();
  });
});
