// api.ts

export const API_BASE = "http://localhost:8000";

export type FrameInfo = {
  t: number;
  file: string;
};

export type Timeline = {
  path_id: string;
  expr_start: string;
  expr_end: string;
  pose: string;
  frames: FrameInfo[];
};

// Simple cache to avoid re-fetching the same timeline multiple times
const timelineCache = new Map<string, Promise<Timeline>>();

export async function fetchTimeline(pathId: string): Promise<Timeline> {
  // Check cache first
  const cached = timelineCache.get(pathId);
  if (cached) {
    return cached;
  }

  // Fetch and cache the promise (not just the result, so multiple concurrent
  // requests for the same timeline will share the same fetch)
  const promise = (async () => {
    const res = await fetch(`${API_BASE}/timeline/${encodeURIComponent(pathId)}`);
    if (!res.ok) {
      // Remove from cache on error so we can retry later
      timelineCache.delete(pathId);
      throw new Error(`Failed to fetch timeline ${pathId}: ${res.status}`);
    }
    const data = await res.json();
    data.frames.sort((a: FrameInfo, b: FrameInfo) => a.t - b.t);
    return data;
  })();

  timelineCache.set(pathId, promise);
  return promise;
}

