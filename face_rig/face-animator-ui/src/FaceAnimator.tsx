// src/FaceAnimator.tsx
import React, { useRef, useState, useEffect } from "react";

type Box = {
  x: number;
  y: number;
  width: number;
  height: number;
};

const API_BASE = "http://localhost:8000";

const FaceAnimator: React.FC = () => {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number } | null>(null);
  const [displaySize, setDisplaySize] = useState<{ w: number; h: number } | null>(null);

  const [box, setBox] = useState<Box | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);

  const [part, setPart] = useState<"eyes" | "brows" | "mouth">("eyes");
  const [action, setAction] = useState<string>("blink");

  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const imgRef = useRef<HTMLImageElement | null>(null);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });

    const rect = img.getBoundingClientRect();
    setDisplaySize({ w: rect.width, h: rect.height });
  };

  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setBox(null);
    setVideoUrl(null);
    const url = URL.createObjectURL(file);
    setImageUrl(url);
  };

  const getRelativeCoords = (evt: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    if (!imgRef.current) return null;
    const rect = imgRef.current.getBoundingClientRect();
    const x = evt.clientX - rect.left;
    const y = evt.clientY - rect.top;
    if (x < 0 || y < 0 || x > rect.width || y > rect.height) return null;
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.preventDefault(); // stop image drag / text selection
    if (!imageUrl) return;
    const rel = getRelativeCoords(e);
    if (!rel) return;
    setIsDrawing(true);
    setStartPoint(rel);
    setBox({ x: rel.x, y: rel.y, width: 0, height: 0 });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    if (!isDrawing || !startPoint) return;
    const rel = getRelativeCoords(e);
    if (!rel) return;
    const x = Math.min(startPoint.x, rel.x);
    const y = Math.min(startPoint.y, rel.y);
    const width = Math.abs(rel.x - startPoint.x);
    const height = Math.abs(rel.y - startPoint.y);
    setBox({ x, y, width, height });
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
    setStartPoint(null);
  };

  const handleAnimate = async () => {
    if (!imageFile || !box || !naturalSize || !displaySize) return;

    setLoading(true);
    setVideoUrl(null);

    const sx = naturalSize.w / displaySize.w;
    const sy = naturalSize.h / displaySize.h;

    const origX = Math.round(box.x * sx);
    const origY = Math.round(box.y * sy);
    const origW = Math.round(box.width * sx);
    const origH = Math.round(box.height * sy);

    const formData = new FormData();
    formData.append("file", imageFile);
    formData.append("part", part);
    formData.append("action", action);
    formData.append("x", String(origX));
    formData.append("y", String(origY));
    formData.append("width", String(origW));
    formData.append("height", String(origH));

    try {
      const res = await fetch(`${API_BASE}/animate`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const text = await res.text();
        console.error("Animate error:", res.status, text);
        setLoading(false);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
    } catch (err) {
      console.error("Animate error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [imageUrl, videoUrl]);

  const actionOptionsForPart: Record<string, string[]> = {
    eyes: ["blink", "look_left", "look_right"],
    brows: ["raise", "furrow"],
    mouth: ["talk_loop", "smile"],
  };

  return (
    <div style={{ display: "flex", gap: "24px", alignItems: "flex-start" }}>
      <div style={{ maxWidth: 512 }}>
        <h2>Face Animator</h2>
        <input type="file" accept="image/*" onChange={handleFileChange} />

        {imageUrl && (
          <div
            style={{ position: "relative", marginTop: 16, border: "1px solid #ddd" }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <img
              ref={imgRef}
              src={imageUrl}
              alt="Uploaded"
              style={{
                display: "block",
                maxWidth: "512px",
                maxHeight: "512px",
                userSelect: "none",
              }}
              draggable={false}
              onLoad={handleImageLoad}
            />
            {box && (
              <div
                style={{
                  position: "absolute",
                  left: box.x,
                  top: box.y,
                  width: box.width,
                  height: box.height,
                  border: "2px solid #00ff00",
                  pointerEvents: "none",
                  boxSizing: "border-box",
                }}
              />
            )}
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          <label>
            Part:&nbsp;
            <select
              value={part}
              onChange={(e) => {
                const p = e.target.value as "eyes" | "brows" | "mouth";
                setPart(p);
                const firstAction = actionOptionsForPart[p][0];
                setAction(firstAction);
              }}
            >
              <option value="eyes">Eyes</option>
              <option value="brows">Brows</option>
              <option value="mouth">Mouth</option>
            </select>
          </label>

          <label style={{ marginLeft: 12 }}>
            Action:&nbsp;
            <select value={action} onChange={(e) => setAction(e.target.value)}>
              {actionOptionsForPart[part].map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button
          style={{ marginTop: 12, padding: "8px 16px" }}
          onClick={handleAnimate}
          disabled={!imageFile || !box || loading}
        >
          {loading ? "Animating..." : "Animate Selected Region"}
        </button>
      </div>

      <div style={{ minWidth: 320 }}>
        <h3>Result</h3>
        {videoUrl ? (
          <video
            src={videoUrl}
            style={{ maxWidth: "320px", maxHeight: "320px", border: "1px solid #ddd" }}
            autoPlay
            loop
            muted
            controls
          />
        ) : (
          <p>No animation yet.</p>
        )}
      </div>
    </div>
  );
};

export default FaceAnimator;

