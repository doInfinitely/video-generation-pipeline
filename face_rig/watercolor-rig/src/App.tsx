import React, { useEffect, useState } from "react";
import TimelineViewer from "./components/TimelineViewer";
import { fetchTimelines } from "./api";

const App: React.FC = () => {
  const [pathIds, setPathIds] = useState<string[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [manualInput, setManualInput] = useState("");

  useEffect(() => {
    fetchTimelines().then((ids) => {
      setPathIds(ids);
      if (ids.length > 0) {
        setSelectedPath(ids[0]);
        setManualInput(ids[0]);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleManualLoad = () => {
    const trimmed = manualInput.trim();
    if (!trimmed) return;
    setSelectedPath(trimmed);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <h1 className="logo">Watercolor Rig</h1>

        <div className="field">
          <label>Path ID</label>
          <input
            type="text"
            value={manualInput}
            placeholder="neutral_to_speaking_ah__center"
            onChange={(e) => setManualInput(e.target.value)}
          />
          <button className="btn" onClick={handleManualLoad}>
            Load path
          </button>
        </div>

        {pathIds.length > 0 && (
          <div className="field">
            <label>Known timelines</label>
            <div className="path-list">
              {pathIds.map((id) => (
                <button
                  key={id}
                  className={`path-item ${
                    selectedPath === id ? "active" : ""
                  }`}
                  onClick={() => {
                    setSelectedPath(id);
                    setManualInput(id);
                  }}
                >
                  {id}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="footer-note">
          Endpoints are generated offline with <code>generate_sequence.py</code>.
          This UI just previews and regenerates individual frames.
        </div>
      </aside>

      <main className="main">
        <TimelineViewer pathId={selectedPath} />
      </main>
    </div>
  );
};

export default App;
