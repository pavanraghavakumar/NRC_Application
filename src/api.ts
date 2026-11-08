export type ApiProblem = {
  title?: unknown;
  detail?: unknown;
  message?: unknown;
  code?: unknown;
  errors?: unknown;
};

const apiBase = '/api/v1';

function readableValue(value: unknown): string[] {
  if (value === null || value === undefined || value === '') return [];
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return [String(value)];
  if (Array.isArray(value)) return value.flatMap(readableValue);
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const message = readableValue(record.message ?? record.msg ?? record.detail);
    if (message.length) {
      const field = readableValue(record.field ?? record.loc).join(' › ');
      return [field ? `${field}: ${message.join(' ')}` : message.join(' ')];
    }
    return Object.entries(record).flatMap(([key, entry]) => readableValue(entry).map(text => `${key}: ${text}`));
  }
  return [String(value)];
}

export function formatApiProblem(problem: ApiProblem, status: number, statusText = ''): string {
  const details = readableValue(problem.errors);
  const primary = readableValue(problem.detail ?? problem.message ?? problem.title);
  const messages = [...primary, ...details].filter((message, index, all) => all.indexOf(message) === index);
  if (messages.length) return messages.join(' ');
  return statusText || `Request failed (${status})`;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body !== undefined && init.body !== null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${apiBase}${path}`, {...init, headers});
  if (!response.ok) {
    const problem = await response.json().catch(() => ({title: response.statusText})) as ApiProblem;
    throw new Error(formatApiProblem(problem, response.status, response.statusText));
  }
  return response.status === 204 ? undefined as T : response.json();
}
