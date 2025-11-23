import React, { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import Plot from "react-plotly.js";

type DistResponse = {
  label: string;
  levels: string[];
  counts: Record<string, number>;
  total: number;
};

const LEVEL_ORDER = [
  "I don't know any",
  "I know a few",
  "I know several",
  "I know many",
];

// Short labels for the radar/spider (fixed order)
const SHORT_LEVELS = ["None", "Few", "Several", "Many"] as const;

// reverse map
const SHORT_TO_LONG: Record<(typeof SHORT_LEVELS)[number], string> = {
  None: "I don't know any",
  Few: "I know a few",
  Several: "I know several",
  Many: "I know many",
};
// POLAR order controls where labels sit around the circle.
// Index 0 is at 0° (right), index 2 at 180° (left).
// This puts None (right) and Few (left).
const POLAR_ORDER: (typeof SHORT_LEVELS)[number][] = ["None", "Many", "Few", "Several"];

// Smaller tooltip chart size so labels fit comfortably
const TOOLTIP_W = 200;
const TOOLTIP_H = 148;

function parseFontSizePx(node: SVGTextElement): number {
  const direct = node.getAttribute("font-size");
  if (direct) return parseFloat(direct);
  const style = node.getAttribute("style") || "";
  const m = style.match(/font-size:\s*([\d.]+)px/i);
  return m ? parseFloat(m[1]) : 16;
}

function parseFill(node: SVGTextElement): string {
  const attr = node.getAttribute("fill");
  if (attr) return attr;
  const style = node.getAttribute("style") || "";
  const m = style.match(/fill:\s*([^;]+)/i);
  return m ? m[1].trim() : "#334155";
}

function rgbOrHexToRgba(input: string, alpha = 1): string {
  const s = input.trim();
  if (/^rgba?\(/i.test(s)) {
    const nums = s.replace(/[^\d.,]/g, "").split(",").map((v) => parseFloat(v));
    const [r, g, b] = nums;
    return `rgba(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}, ${alpha})`;
  }
  if (s[0] === "#") {
    let r = 0, g = 0, b = 0;
    if (s.length === 4) {
      r = parseInt(s[1] + s[1], 16);
      g = parseInt(s[2] + s[2], 16);
      b = parseInt(s[3] + s[3], 16);
    } else if (s.length >= 7) {
      r = parseInt(s.slice(1, 3), 16);
      g = parseInt(s.slice(3, 5), 16);
      b = parseInt(s.slice(5, 7), 16);
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return input;
}

type Props = {
  facultyName: string;
  facultyColor?: string;
};

const KnowledgeApplicationsWordCloud: React.FC<Props> = ({ facultyName, facultyColor }) => {
  const tint = facultyColor ?? "#64748b";

  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [gender, setGender] = useState("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Tooltip + parsing state
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverLabel, setHoverLabel] = useState<string | null>(null);
  const [hoverColor, setHoverColor] = useState<string>("#334155");
  const [hoverAlpha, setHoverAlpha] = useState<number>(0.5);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [dist, setDist] = useState<DistResponse | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [noData, setNoData] = useState(false);

  const fontRangeRef = useRef<{ min: number; max: number }>({ min: 12, max: 72 });
  const distCache = useRef<Map<string, DistResponse>>(new Map());

  const fetchSvg = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (gender && gender !== "All") params.append("gender", gender);
      if (experience) params.append("experience", experience);
      if (profile) params.append("profile", profile);
      params.append("_", String(Date.now())); // cache-bust

      const url = `http://localhost:8000/api/faculty/${encodeURIComponent(
        facultyName
      )}/knowledge-applications-wordcloud-svg?${params.toString()}`;

      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      setSvgMarkup(text);
      setNoData(false);
    } catch {
      setSvgMarkup(null);
      setNoData(true);
    } finally {
      setLoading(false);
    }
  }, [facultyName, gender, experience, profile]);

  useEffect(() => {
    fetchSvg();
  }, [fetchSvg]);

  const responsiveSvg = useMemo(() => {
    if (!svgMarkup) return null;
    let out = svgMarkup;
    if (!out.includes("max-width:100%")) {
      out = out.replace("<svg ", "<svg style='max-width:100%;height:auto;display:block' ");
    }
    if (!out.includes("<style>") || !out.includes("text:hover")) {
      out = out.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
      );
    }
    return out;
  }, [svgMarkup]);

  useEffect(() => {
    const holder = containerRef.current;
    if (!holder || !responsiveSvg) return;

    let rafId: number | null = null;
    let mo: MutationObserver | null = null;
    let hideTimer: number | null = null;

    const clearTimers = () => {
      if (rafId) cancelAnimationFrame(rafId);
      if (hideTimer) window.clearTimeout(hideTimer);
      rafId = null;
      hideTimer = null;
    };

    const hideTooltipNow = () => {
      clearTimers();
      setShowTooltip(false);
      setDist(null);
      setHoverLabel(null);
    };

    const schedulePos = (ev: PointerEvent | MouseEvent) => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const rect = holder.getBoundingClientRect();
        const x = Math.min(Math.max(0, (ev as MouseEvent).clientX - rect.left + 12), rect.width - (TOOLTIP_W + 12));
        const y = Math.min(Math.max(0, (ev as MouseEvent).clientY - rect.top + 12), rect.height - (TOOLTIP_H + 12));
        setTooltipPos({ x, y });
      });
    };

    const onPointerMoveDoc = (ev: PointerEvent) => {
      if (!showTooltip) return;
      schedulePos(ev);
      const rect = holder.getBoundingClientRect();
      const inside = ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom;
      if (!inside) hideTooltipNow();
    };

    const onPointerMoveHolder = (ev: PointerEvent) => {
      schedulePos(ev);
      const target = ev.target as Element | null;
      const textEl = target?.closest?.("text") as SVGTextElement | null;

      if (textEl) {
        if (hideTimer) { window.clearTimeout(hideTimer); hideTimer = null; }

        const label = (textEl.textContent || "").trim();
        if (!label) return;

        setHoverLabel((prev) => {
          if (prev === label) return prev;

          const color = parseFill(textEl);
          const fs = parseFontSizePx(textEl);
          const { min, max } = fontRangeRef.current;
          const norm = Math.max(0, Math.min(1, (fs - min) / Math.max(1, max - min)));
          const alpha = 0.35 + 0.45 * norm;

          setHoverColor(color);
          setHoverAlpha(alpha);

          const key = [facultyName, label, gender || "All", experience || "", profile || ""].join("|");
          if (distCache.current.has(key)) {
            setDist(distCache.current.get(key)!);
          } else {
            const params = new URLSearchParams();
            params.append("app_label", label);
            if (gender && gender !== "All") params.append("gender", gender);
            if (experience) params.append("experience", experience);
            if (profile) params.append("profile", profile);

            fetch(
              `http://localhost:8000/api/faculty/${encodeURIComponent(
                facultyName
              )}/knowledge-applications-distribution-count?${params.toString()}`
            )
              .then((r) => r.json())
              .then((data: DistResponse) => {
                distCache.current.set(key, data);
                setDist(data);
              })
              .catch(() => {
                setDist({
                  label,
                  levels: LEVEL_ORDER,
                  counts: LEVEL_ORDER.reduce((a, v) => ((a[v] = 0), a), {} as Record<string, number>),
                  total: 0,
                });
              });
          }

          return label;
        });

        setShowTooltip((s) => (s ? s : true));
      } else {
        if (!hideTimer) hideTimer = window.setTimeout(hideTooltipNow, 140);
      }
    };

    const onPointerOutHolder = (ev: PointerEvent) => {
      const next = ev.relatedTarget as Node | null;
      if (next && holder.contains(next)) return;
      hideTooltipNow();
    };

    const initOnceSvgIsReady = () => {
      const svgEl = holder.querySelector("svg");
      if (!svgEl) return false;

      const texts = svgEl.querySelectorAll("text");
      setNoData(texts.length === 0);
      if (texts.length === 0) return true;

      // font range + subtle brightness
      let minFS = Infinity;
      let maxFS = -Infinity;
      texts.forEach((t) => {
        const fs = parseFontSizePx(t as SVGTextElement);
        if (fs < minFS) minFS = fs;
        if (fs > maxFS) maxFS = fs;
      });
      if (!isFinite(minFS) || minFS === Infinity) minFS = 12;
      if (!isFinite(maxFS) || maxFS <= 0) maxFS = 72;
      fontRangeRef.current = { min: minFS, max: maxFS };

      texts.forEach((t) => {
        const fs = parseFontSizePx(t as SVGTextElement);
        const norm = Math.max(0, Math.min(1, (fs - minFS) / Math.max(1, maxFS - minFS)));
        const brightness = 1.15 - 0.3 * norm;
        const existing = (t as SVGTextElement).getAttribute("style") || "";
        (t as SVGTextElement).setAttribute(
          "style",
          `${existing}; filter: brightness(${brightness.toFixed(2)}) saturate(1.05);`
        );
      });

      // listeners
      holder.addEventListener("pointermove", onPointerMoveHolder, { passive: true });
      holder.addEventListener("pointerout", onPointerOutHolder);
      document.addEventListener("pointermove", onPointerMoveDoc, { passive: true });
      window.addEventListener("scroll", hideTooltipNow, true);
      window.addEventListener("blur", hideTooltipNow);
      window.addEventListener("resize", hideTooltipNow);

      const cleanup = () => {
        holder.removeEventListener("pointermove", onPointerMoveHolder);
        holder.removeEventListener("pointerout", onPointerOutHolder);
        document.removeEventListener("pointermove", onPointerMoveDoc);
        window.removeEventListener("scroll", hideTooltipNow, true);
        window.removeEventListener("blur", hideTooltipNow);
        window.removeEventListener("resize", hideTooltipNow);
      };
      (holder as any).__wcCleanup = cleanup;
      return true;
    };

    const start = () => {
      if (initOnceSvgIsReady()) return;
      const moInstance = new MutationObserver(() => {
        if (initOnceSvgIsReady()) {
          moInstance.disconnect();
        }
      });
      mo = moInstance;
      mo.observe(holder, { childList: true, subtree: true });
    };

    requestAnimationFrame(start);

    return () => {
      if (mo) mo.disconnect();
      (holder as any).__wcCleanup?.();
      clearTimers();
    };
  }, [responsiveSvg, facultyName, gender, experience, profile, showTooltip]);

  // Tinted styles for the centered “no data” message
  const tintBg = rgbOrHexToRgba(tint, 0.06);
  const tintBorder = `1px solid ${rgbOrHexToRgba(tint, 0.25)}`;
  const tintText = tint;

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-6">
        <select value={gender} onChange={(e) => setGender(e.target.value)} className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" aria-label="Filter by gender">
          <option value="All">All Genders</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Non-binary">Non-binary</option>
          <option value="No answer">No answer</option>
        </select>

        <select value={experience ?? ""} onChange={(e) => setExperience(e.target.value || null)} className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" aria-label="Filter by teaching experience">
          <option value="">All Experience</option>
          <option value="Less than 5">Less than 5</option>
          <option value="Between 5 and 10">Between 5 and 10</option>
          <option value="Between 11 and 20">Between 11 and 20</option>
          <option value="More than 20">More than 20</option>
        </select>

        <select value={profile ?? ""} onChange={(e) => setProfile(e.target.value || null)} className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-red-200 transition" aria-label="Filter by profile">
          <option value="">All Profiles</option>
          <option value="Senior Lecturer">Senior Lecturer</option>
          <option value="Associate">Associate</option>
          <option value="PreDoc">PreDoc</option>
          <option value="PostDoc">PostDoc</option>
          <option value="Collab">Collab</option>
          <option value="Lecturer">Lecturer</option>
          <option value="Professor">Professor</option>
        </select>
      </div>

      <h3 className="text-[34px] text-slate-800 mb-4 text-center">
        What's the knowledge among tasks?
      </h3>

      {/* Display: keep opacity steady so “no data” doesn’t fade away */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.25 }}
        className="relative flex flex-col items-center w-full min-h-[260px]"
      >
        {loading ? (
          <div className="w-full max-w-5xl h-[420px] rounded-lg bg-slate-100 border border-slate-200 animate-pulse" />
        ) : responsiveSvg ? (
          <>
            <div
              ref={containerRef}
              className="w-full max-w-5xl"
              dangerouslySetInnerHTML={{ __html: responsiveSvg }}
            />
            {noData && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div
                  className="rounded-xl px-4 py-3 text-center"
                  style={{
                    background: tintBg,
                    border: tintBorder,
                    color: tintText,
                    fontWeight: 600,
                    letterSpacing: "0.2px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
                  }}
                >
                  No data for the selected filters.
                </div>
              </div>
            )}
          </>
        ) : (
          <div
            className="w-full max-w-5xl h-[420px] rounded-lg flex items-center justify-center"
            style={{ background: tintBg, border: tintBorder }}
          >
            <p style={{ color: tintText, fontWeight: 600 }}>No data for the selected filters.</p>
          </div>
        )}

        {/* Hover tooltip with spider chart — smaller + short axis labels */}
        {showTooltip && hoverLabel && (
          <div
            className="absolute z-50 rounded-xl shadow-lg border border-slate-200 bg-white p-2"
            style={{ left: tooltipPos.x, top: tooltipPos.y, width: TOOLTIP_W, pointerEvents: "none" }}
          >
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-medium text-slate-700">{hoverLabel}</span>
              <span className="inline-block w-2 h-2 rounded-full" style={{ background: hoverColor }} />
            </div>

            {dist && dist.total > 0 ? (
              <Plot
                data={[
                  (() => {
                    // build r values in the same order as POLAR_ORDER
                    const rCore = POLAR_ORDER.map(short => {
                      const long = SHORT_TO_LONG[short];
                      return (dist.counts[long] || 0);
                    });
                    return {
                      type: "scatterpolar" as const,
                      r: rCore.concat(rCore[0]),                   // close the loop
                      theta: POLAR_ORDER.concat(POLAR_ORDER[0]),   // short labels, same order
                      fill: "toself",
                      name: hoverLabel!,
                      line: { color: hoverColor, width: 2 },
                      fillcolor: rgbOrHexToRgba(hoverColor, hoverAlpha),
                      hovertemplate: "<b>%{theta}</b><br>Count: <b>%{r}</b><extra></extra>",
                    };
                  })(),
                ]}
                layout={{
                  margin: { t: 6, r: 10, b: 6, l: 10 },
                  polar: {
                    domain: { x: [0,100], y: [0.08, 0.93] }, // shrinks the plot so labels fit
                    bgcolor: "rgba(0,0,0,0)",
                    radialaxis: {
                      showticklabels: false,
                      ticks: "",
                      showline: false,
                      gridcolor: "#e2e8f0",
                    },
                    angularaxis: {
                      categoryorder: "array",
                      categoryarray: POLAR_ORDER,     // <-- enforce placement (None at 0°, Few at 180°)
                      rotation: 0,                    // 0° = right; set 180 to flip left/right if you prefer
                      direction: "counterclockwise",  // default; change to "clockwise" if you want the other spin
                      gridcolor: "#e2e8f0",
                      linecolor: "#cbd5e1",
                      tickfont: { size: 8, color: "#334155" },
                      tickpadding: 2,
                    },
                  },
                  showlegend: false,
                  paper_bgcolor: "rgba(0,0,0,0)",
                  plot_bgcolor: "rgba(0,0,0,0)",
                  height: TOOLTIP_H, // you already set smaller tooltip H/W
                }}
                config={{ displayModeBar: false, staticPlot: true }}
                style={{ width: "100%", height: TOOLTIP_H }}
              />
            ) : (
              <div className="px-2 py-3 text-center">
                <p className="text-xs text-slate-500">
                  No responses for <span className="font-medium">{hoverLabel}</span> with current filters.
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default KnowledgeApplicationsWordCloud;
