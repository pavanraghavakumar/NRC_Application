import {afterEach, describe, expect, it, vi} from 'vitest';
import {api, formatApiProblem} from './api';

afterEach(() => vi.restoreAllMocks());

describe('api', () => {
  it.each(['POST', 'PATCH'])('sends JSON for %s while preserving caller headers', async method => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({id: 'record-1'}), {
      status: method === 'POST' ? 201 : 200,
      headers: {'Content-Type': 'application/json'},
    }));

    await api('/goals', {method, headers: {'If-Match': '"1"'}, body: JSON.stringify({goal: 'Safety'})});

    const request = fetchMock.mock.calls[0];
    const headers = new Headers((request[1] as RequestInit).headers);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('Accept')).toBe('application/json');
    expect(headers.get('If-Match')).toBe('"1"');
  });

  it('does not label a bodyless request as JSON', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({items: []}), {status: 200}));
    await api('/goals');
    const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
    expect(headers.get('Content-Type')).toBeNull();
  });

  it('renders RFC problem details and field validation arrays readably', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      title: 'Validation failed',
      detail: 'Please correct the highlighted fields.',
      errors: [
        {field: 'goal_text', code: 'required', message: 'Goal Text is required.'},
        {loc: ['body', 'sequence'], msg: 'Sequence must be a number.'},
      ],
    }), {status: 400, headers: {'Content-Type': 'application/problem+json'}}));

    await expect(api('/goals', {method: 'POST', body: '{}'})).rejects.toThrow(
      'Please correct the highlighted fields. goal_text: Goal Text is required. body › sequence: Sequence must be a number.',
    );
  });
});

describe('formatApiProblem', () => {
  it('never stringifies a structured detail as [object Object]', () => {
    expect(formatApiProblem({detail: {message: 'Readable backend problem'}}, 422)).toBe('Readable backend problem');
  });
});
