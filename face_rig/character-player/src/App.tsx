// App.tsx

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE, fetchTimeline, FrameInfo, Timeline } from "./api";
import {
  ExpressionId,
  PoseId,
  State,
  Segment,
  planRoute,
} from "./transitionGraph";

const EXPRESSIONS: ExpressionId[] = [
  "neutral",
  "happy_soft",
  "happy_big",
  "speaking_ah",
  "surprised_ah",
  "speaking_ee",
  "speaking_uw",
  "oh_round",
  "concerned",
  "blink_closed",
];

const POSES: PoseId[] = [
  "center",
  "tilt_left_small",
  "tilt_right_small",
  "nod_down_small",
  "nod_up_small",
];

type ActiveSegment = {
  seg: Segment;
  timeline: Timeline;
  direction: "forward" | "backward";
};

const FPS = 8;

const App: React.FC = () => {
  const [currentState, setCurrentState] = useState<State>({
    expr: "neutral",
    pose: "center",
  });

  const [targetState, setTargetState] = useState<State>({
    expr: "neutral",
    pose: "center",
  });

  const [activeSegments, setActiveSegments] = useState<ActiveSegment[]>([]);
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [restBlink, setRestBlink] = useState(true);
  const [idleFrame, setIdleFrame] = useState<{ timeline: Timeline; frame: FrameInfo } | null>(null);
  const [loadedIdleKey, setLoadedIdleKey] = useState<string>("");

  // Load the idle/resting frame for current state
  useEffect(() => {
    if (isPlaying) return; // Don't load idle frame during playback

    // Create a cache key to prevent re-loading the same state
    const stateKey = `${currentState.expr}@${currentState.pose}`;
    if (stateKey === loadedIdleKey) return; // Already loaded

    const loadIdleFrame = async () => {
      // Strategy: Find any timeline where currentState is an endpoint
      // Try a few common paths that are likely to exist
      
      const candidatePaths: Array<{ pathId: string; useStart: boolean }> = [];
      
      if (currentState.expr === "neutral") {
        // For neutral, use start of any neutral→X timeline
        candidatePaths.push(
          { pathId: `neutral_to_blink__${currentState.pose}`, useStart: true },
          { pathId: `neutral_to_speaking_ah__${currentState.pose}`, useStart: true },
          { pathId: `neutral_to_happy_soft__${currentState.pose}`, useStart: true },
        );
      } else if (currentState.expr === "happy_big") {
        // happy_big is the end of happy_soft_to_happy_big
        candidatePaths.push(
          { pathId: `happy_soft_to_happy_big__${currentState.pose}`, useStart: false },
        );
      } else if (currentState.expr === "surprised_ah") {
        // surprised_ah is the end of speaking_ah_to_surprised
        candidatePaths.push(
          { pathId: `speaking_ah_to_surprised__${currentState.pose}`, useStart: false },
        );
      } else if (currentState.expr === "blink_closed") {
        // blink_closed has a special sequence name: neutral_to_blink (not neutral_to_blink_closed)
        candidatePaths.push(
          { pathId: `neutral_to_blink__${currentState.pose}`, useStart: false },
        );
      } else {
        // For other expressions (speaking_ah, speaking_ee, speaking_uw, oh_round, concerned)
        // Try to find neutral_to_{expression} timeline
        candidatePaths.push(
          { pathId: `neutral_to_${currentState.expr}__${currentState.pose}`, useStart: false },
        );
      }

      // Try each candidate path
      for (const { pathId, useStart } of candidatePaths) {
        try {
          const timeline = await fetchTimeline(pathId);
          const frame = useStart 
            ? timeline.frames[0]
            : timeline.frames[timeline.frames.length - 1];
          setIdleFrame({ timeline, frame });
          setLoadedIdleKey(stateKey); // Mark as loaded
          return; // Success!
        } catch {
          // Try next candidate
        }
      }

      console.warn(`Could not load idle frame for ${currentState.expr} @ ${currentState.pose}`);
    };

    loadIdleFrame();
  }, [currentState, isPlaying, loadedIdleKey]);

  const [currentTimeline, currentFrame]: [Timeline | null, FrameInfo | null] =
    useMemo(() => {
      if (isPlaying && activeSegments.length) {
        const seg = activeSegments[segmentIndex];
        if (!seg) return [null, null];

        const frames =
          seg.direction === "forward"
            ? seg.timeline.frames
            : [...seg.timeline.frames].slice().reverse();

        const idx = Math.min(frameIndex, frames.length - 1);
        return [seg.timeline, frames[idx] ?? null];
      }

      // When idle, show the idle frame
      if (idleFrame) {
        return [idleFrame.timeline, idleFrame.frame];
      }

      return [null, null];
    }, [activeSegments, segmentIndex, frameIndex, isPlaying, idleFrame]);

  // Main player loop
  useEffect(() => {
    if (!isPlaying || !activeSegments.length) return;

    const seg = activeSegments[segmentIndex];
    if (!seg) return;

    const frames =
      seg.direction === "forward"
        ? seg.timeline.frames
        : [...seg.timeline.frames].slice().reverse();

    if (!frames.length) return;

    const intervalMs = 1000 / FPS;
    const id = window.setInterval(() => {
      setFrameIndex((prev) => {
        const next = prev + 1;
        if (next < frames.length) {
          return next;
        } else {
          // move to next segment
          setSegmentIndex((s) => {
            const nextSeg = s + 1;
            if (nextSeg < activeSegments.length) {
              return nextSeg;
            } else {
              // route done
              const lastSeg = activeSegments[activeSegments.length - 1];
              setCurrentState(lastSeg.seg.to);
              setActiveSegments([]);
              setSegmentIndex(0);
              setFrameIndex(0);
              setIsPlaying(false);
              return 0;
            }
          });
          return 0;
        }
      });
    }, intervalMs);

    return () => window.clearInterval(id);
  }, [activeSegments, segmentIndex, isPlaying]);

  // Kick off a route: compute segments, fetch timelines, then play
  const playRouteTo = useCallback(
    async (next: State) => {
      const route = planRoute(currentState, next);
      if (!route.length) {
        setCurrentState(next);
        setTargetState(next);
        return;
      }

      try {
        const segs: ActiveSegment[] = [];
        for (const seg of route) {
          const timeline = await fetchTimeline(seg.pathId);
          segs.push({ seg, timeline, direction: seg.direction });
        }
        setTargetState(next);
        setActiveSegments(segs);
        setSegmentIndex(0);
        setFrameIndex(0);
        setIsPlaying(true);
      } catch (err) {
        console.error("Failed to play route:", err);
        alert("Failed to load one or more timelines. Check server logs.");
      }
    },
    [currentState]
  );

  // --- Resting blink scheduler ---
  useEffect(() => {
    if (!restBlink) return;
    if (isPlaying) return;

    // Only blink from neutral expressions
    if (currentState.expr !== "neutral") return;

    const timeoutMs = 2000 + Math.random() * 4000;
    const id = window.setTimeout(async () => {
      if (!restBlink) return;
      if (isPlaying) return;
      if (currentState.expr !== "neutral") return;

      const blinkTarget: State = {
        expr: "blink_closed",
        pose: currentState.pose,
      };

      const backToNeutral: State = {
        expr: "neutral",
        pose: currentState.pose,
      };

      // route neutral->blink, then blink->neutral
      const forwardRoute = planRoute(currentState, blinkTarget);
      const backRoute = planRoute(blinkTarget, backToNeutral);
      const route = [...forwardRoute, ...backRoute];

      if (!route.length) return;

      try {
        const segs: ActiveSegment[] = [];
        for (const seg of route) {
          const timeline = await fetchTimeline(seg.pathId);
          segs.push({ seg, timeline, direction: seg.direction });
        }
        setActiveSegments(segs);
        setSegmentIndex(0);
        setFrameIndex(0);
        setIsPlaying(true);
      } catch (err) {
        console.error("Blink route failed:", err);
      }
    }, timeoutMs);

    return () => window.clearTimeout(id);
  }, [restBlink, isPlaying, currentState]);

  // Handlers for UI controls
  const handleExpressionClick = (expr: ExpressionId) => {
    const next: State = { expr, pose: currentState.pose };
    playRouteTo(next);
  };

  const handlePoseClick = (pose: PoseId) => {
    const next: State = { expr: currentState.expr, pose };
    playRouteTo(next);
  };

  const currentImageUrl =
    currentTimeline && currentFrame
      ? `${API_BASE}/frames/${currentTimeline.path_id}/${currentFrame.file}`
      : null;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center p-6 gap-4">
      <h1 className="text-2xl font-bold mb-2">Watercolor Face State Tester</h1>

      {/* Preview */}
      <div className="flex flex-col items-center gap-2">
        <div className="w-[320px] h-[480px] bg-slate-800 rounded-xl flex items-center justify-center overflow-hidden">
          {currentImageUrl ? (
            <img
              src={currentImageUrl}
              alt="current"
              className="max-w-full max-h-full object-contain"
            />
          ) : (
            <span className="text-slate-500 text-sm">
              No frame loaded yet…
            </span>
          )}
        </div>
        <div className="text-xs text-slate-300">
          Current state:{" "}
          <span className="font-mono">
            {currentState.expr} @ {currentState.pose}
          </span>
          {isPlaying && activeSegments.length > 0 && (
            <>
              {" "}
              · Transitioning via{" "}
              <span className="font-mono">
                {activeSegments[segmentIndex]?.seg.pathId}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-row gap-6 mt-4">
        {/* Expression buttons */}
        <div>
          <h2 className="font-semibold mb-2 text-sm uppercase tracking-wide text-slate-400">
            Expressions
          </h2>
          <div className="flex flex-wrap gap-2 max-w-[320px]">
            {EXPRESSIONS.map((expr) => {
              const isActive = expr === currentState.expr;
              return (
                <button
                  key={expr}
                  onClick={() => handleExpressionClick(expr)}
                  className={
                    "px-3 py-1 rounded-full text-xs border " +
                    (isActive
                      ? "bg-emerald-500 text-slate-900 border-emerald-400"
                      : "bg-slate-800 border-slate-600 hover:border-emerald-400")
                  }
                >
                  {expr}
                </button>
              );
            })}
          </div>
        </div>

        {/* Pose buttons */}
        <div>
          <h2 className="font-semibold mb-2 text-sm uppercase tracking-wide text-slate-400">
            Poses
          </h2>
          <div className="flex flex-col gap-2">
            {POSES.map((pose) => {
              const isActive = pose === currentState.pose;
              return (
                <button
                  key={pose}
                  onClick={() => handlePoseClick(pose)}
                  className={
                    "px-3 py-1 rounded-full text-xs border text-left " +
                    (isActive
                      ? "bg-sky-500 text-slate-900 border-sky-400"
                      : "bg-slate-800 border-slate-600 hover:border-sky-400")
                  }
                >
                  {pose}
                </button>
              );
            })}
          </div>
        </div>

        {/* Global controls */}
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={restBlink}
              onChange={(e) => setRestBlink(e.target.checked)}
            />
            Resting blink
          </label>
          <button
            className="px-3 py-1 text-xs rounded bg-slate-800 border border-slate-600 hover:border-red-400"
            onClick={() => {
              setActiveSegments([]);
              setIsPlaying(false);
              setSegmentIndex(0);
              setFrameIndex(0);
            }}
          >
            Stop / Reset route
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;

