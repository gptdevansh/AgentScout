/* ── Shared React hooks ───────────────────────────────────────────────── */

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Generic async data fetcher with loading/error states.
 */
export function useAsync<T>(
  fn: () => Promise<T>,
  deps: unknown[] = [],
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    fn()
      .then(setData)
      .catch((err) => setError(err?.message ?? String(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}

/**
 * Interval-based polling hook.
 */
export function usePolling(callback: () => void, intervalMs: number, active = true) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => savedCallback.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, active]);
}
