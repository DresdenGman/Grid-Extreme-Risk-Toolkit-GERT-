import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import BriefActions from '../../components/BriefActions';
import { BRIEF_QUESTIONS, exerciseReceipt, WINTER_BRIEF } from '../../lib/briefs';

describe('winter brief self-check', () => {
  it('requires both valid initial answers and a valid timestamp', () => {
    for (const answers of [[-1, 0], [2], [3, 0], [2, NaN], [2.5, 0]]) expect(() => exerciseReceipt(answers, '2026-09-13T09:00:00Z')).toThrow(RangeError);
    expect(() => exerciseReceipt([2, 0], 'invalid')).toThrow(RangeError);
  });
  it('retains wrong answers without upgrading them to a successful review', () => {
    const receipt = exerciseReceipt([0, 2], '2026-09-13T09:00:00Z');
    expect(receipt.correct_answers).toBe(0);
    expect(receipt.responses[0].initial_answer).toBe(BRIEF_QUESTIONS[0].options[0]);
    expect(receipt.limitations).toContain('not independently verified');
    expect(receipt).not.toHaveProperty('email');
  });
  it('scores the two questions and preserves the brief version', () => {
    const receipt = exerciseReceipt([2, 0], '2026-09-13T09:00:00Z');
    expect(receipt.correct_answers).toBe(2);
    expect(receipt.brief_version).toBe(WINTER_BRIEF.version);
  });
  it('reveals explanations, locks initial answers, and makes no network request', () => {
    const request = vi.spyOn(globalThis, 'fetch');
    render(<BriefActions />);
    expect(screen.getByRole('button', { name: 'Check my answers' })).toBeDisabled();
    fireEvent.click(screen.getByLabelText(BRIEF_QUESTIONS[0].options[2]));
    fireEvent.click(screen.getByLabelText(BRIEF_QUESTIONS[1].options[0]));
    fireEvent.click(screen.getByRole('button', { name: 'Check my answers' }));
    expect(screen.getByText('2 of 2 initial answers correct.')).toBeInTheDocument();
    expect(screen.getByLabelText(BRIEF_QUESTIONS[0].options[0])).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Download my exercise record' })).toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
    request.mockRestore();
  });
});
