"use client";

import { useEffect, useMemo, useRef, useState } from "react";

/**
 * Globe3D
 * A dependency-free, pure-CSS 3D globe rendered with stacked latitude and
 * longitude rings, orbiting rings, and an ambient glow.
 *
 * Fully responsive: it fills its parent's width (capped by `maxSize`) and
 * measures itself so all internal geometry scales fluidly. The whole element
 * is `pointer-events-none` so its overflowing glow/orbit never block clicks.
 */
export default function Globe3D({ maxSize = 340 }: { maxSize?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(maxSize);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const update = () => {
      const w = el.clientWidth;
      if (w > 0) setSize(Math.min(w, maxSize));
    };

    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [maxSize]);

  const meridians = useMemo(
    () => Array.from({ length: 9 }, (_, i) => (i * 180) / 9),
    []
  );

  const parallels = useMemo(() => {
    const lines = [];
    for (let i = 1; i < 8; i++) {
      const t = i / 8;
      const angle = (t - 0.5) * Math.PI;
      const widthRatio = Math.cos(angle);
      const top = (1 - Math.sin(angle)) / 2;
      lines.push({ widthRatio, top });
    }
    return lines;
  }, []);

  return (
    <div
      className="pointer-events-none relative aspect-square w-full"
      style={{ maxWidth: maxSize }}
      aria-hidden
    >
      <div ref={ref} className="globe-scene absolute inset-0">
        {/* Ambient glow */}
        <div
          className="globe-glow absolute rounded-full"
          style={{
            inset: -size * 0.22,
            background:
              "radial-gradient(circle, hsl(var(--amazon-orange) / 0.45) 0%, hsl(var(--amazon-orange) / 0.12) 45%, transparent 70%)",
            filter: "blur(8px)",
          }}
        />

        <div className="globe-floating relative h-full w-full">
          <div className="globe-sphere relative h-full w-full">
            {/* Core sphere */}
            <div
              className="absolute inset-0 rounded-full"
              style={{
                background:
                  "radial-gradient(circle at 32% 28%, #2b3a4d 0%, #1b2733 45%, #0d141d 100%)",
                boxShadow:
                  "inset -22px -22px 60px rgba(0,0,0,0.7), inset 18px 18px 40px hsl(var(--amazon-orange) / 0.12), 0 0 60px hsl(var(--amazon-orange) / 0.25)",
              }}
            />

            {/* Longitude rings */}
            {meridians.map((deg, i) => (
              <div
                key={`m-${i}`}
                className="globe-meridian"
                style={{ transform: `rotateY(${deg}deg)` }}
              />
            ))}

            {/* Latitude rings */}
            {parallels.map((p, i) => {
              const w = p.widthRatio * size;
              return (
                <div
                  key={`p-${i}`}
                  className="globe-parallel"
                  style={{
                    width: w,
                    height: w,
                    top: p.top * size - w / 2,
                    transform: "rotateX(90deg)",
                  }}
                />
              );
            })}

            {/* Specular highlight */}
            <div
              className="absolute rounded-full"
              style={{
                width: size * 0.32,
                height: size * 0.32,
                top: size * 0.16,
                left: size * 0.2,
                background:
                  "radial-gradient(circle, rgba(255,255,255,0.35) 0%, transparent 70%)",
                filter: "blur(6px)",
              }}
            />
          </div>
        </div>

        {/* Orbiting ring (tilted) */}
        <div className="absolute inset-0" style={{ transform: "rotateX(72deg)" }}>
          <div
            className="orbit-ring absolute rounded-full"
            style={{
              inset: -size * 0.12,
              border: "2px solid hsl(var(--amazon-gold) / 0.55)",
              boxShadow: "0 0 18px hsl(var(--amazon-orange) / 0.4)",
            }}
          >
            <div
              className="absolute rounded-full"
              style={{
                width: 14,
                height: 14,
                top: -7,
                left: "50%",
                marginLeft: -7,
                background: "hsl(var(--amazon-orange))",
                boxShadow: "0 0 16px hsl(var(--amazon-orange))",
              }}
            />
          </div>
        </div>

        {/* Second orbit, reversed */}
        <div
          className="absolute inset-0"
          style={{ transform: "rotateX(108deg) rotateZ(30deg)" }}
        >
          <div
            className="orbit-ring-reverse absolute rounded-full"
            style={{
              inset: -size * 0.02,
              border: "1px dashed hsl(var(--amazon-gold) / 0.4)",
            }}
          />
        </div>
      </div>
    </div>
  );
}
