export type Snapshot<T> = T;

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value));

export function useHistory<T>(limit = 10) {
  const past: Snapshot<T>[] = [];
  const future: Snapshot<T>[] = [];

  return {
    push(state: T): void {
      past.push(clone(state));
      if (past.length > limit) {
        past.shift();
      }
      future.length = 0;
    },
    undo(current: T): T | null {
      if (!past.length) {
        return null;
      }
      const previous = past.pop()!;
      future.push(clone(current));
      if (future.length > limit) {
        future.shift();
      }
      return clone(previous);
    },
    redo(current: T): T | null {
      if (!future.length) {
        return null;
      }
      const next = future.pop()!;
      past.push(clone(current));
      if (past.length > limit) {
        past.shift();
      }
      return clone(next);
    },
    reset(): void {
      past.length = 0;
      future.length = 0;
    },
    canUndo(): boolean {
      return past.length > 0;
    },
    canRedo(): boolean {
      return future.length > 0;
    },
  };
}
