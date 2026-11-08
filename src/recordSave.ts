type PersistedRecord = Record<string, unknown> & { id?: unknown };

type SaveTransition = {
  isNew: boolean;
  workspace: string;
  entity: string;
  reset: (record: PersistedRecord) => void;
  navigate: (to: string, options: { replace: boolean }) => void;
};

export function applyPersistedSave(record: PersistedRecord, transition: SaveTransition): boolean {
  transition.reset(record);

  if (!transition.isNew || typeof record.id !== 'string' || !record.id) {
    return false;
  }

  transition.navigate(`/${transition.workspace}/${transition.entity}/${record.id}`, { replace: true });
  return true;
}
