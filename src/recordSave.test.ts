import { describe, expect, it, vi } from 'vitest';
import { applyPersistedSave } from './recordSave';

describe('applyPersistedSave', () => {
  it('resets dirty state and replaces a new route with the persisted record route', () => {
    const reset = vi.fn();
    const navigate = vi.fn();
    const record = { id: 'goal-123', goal: 'Persisted goal', row_version: 1 };

    expect(applyPersistedSave(record, {
      isNew: true,
      workspace: 'sp',
      entity: 'goals',
      reset,
      navigate,
    })).toBe(true);
    expect(reset).toHaveBeenCalledWith(record);
    expect(navigate).toHaveBeenCalledWith('/sp/goals/goal-123', { replace: true });
  });

  it('resets an updated record without navigating', () => {
    const reset = vi.fn();
    const navigate = vi.fn();
    const record = { id: 'office-123', office: 'Persisted office', row_version: 2 };

    expect(applyPersistedSave(record, {
      isNew: false,
      workspace: 'sp',
      entity: 'offices',
      reset,
      navigate,
    })).toBe(false);
    expect(reset).toHaveBeenCalledWith(record);
    expect(navigate).not.toHaveBeenCalled();
  });
});
