// ToolsWordCloud.tsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

type Props = {
  facultyName: string;
  facultyColor?: string; // tint for "no data" fallback
};

const TOOLTIP_W = 220;
const TOOLTIP_H = 70;

function parseFill(node: SVGTextElement): string {
  const attr = node.getAttribute("fill");
  if (attr) return attr;
  const style = node.getAttribute("style") || "";
  const m = style.match(/fill:\s*([^;]+)/i);
  return m ? m[1].trim() : "#334155";
}

function rgba(input: string, a = 1): string {
  const s = input.trim();
  if (/^rgba?\(/i.test(s)) {
    const nums = s.replace(/[^\d.,]/g, "").split(",").map((v) => parseFloat(v));
    const [r, g, b] = nums;
    return `rgba(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}, ${a})`;
  }
  if (s[0] === "#") {
    let r = 0, g = 0, b = 0;
    if (s.length === 4) {
      r = parseInt(s[1] + s[1], 16);
      g = parseInt(s[2] + s[2], 16);
      b = parseInt(s[3] + s[3], 16);
    } else {
      r = parseInt(s.slice(1, 3), 16);
      g = parseInt(s.slice(3, 5), 16);
      b = parseInt(s.slice(5, 7), 16);
    }
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  }
  return input;
}

const ToolsWordCloud: React.FC<Props> = ({ facultyName, facultyColor = "#6b21a8" }) => {
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [gender, setGender] = useState("All");
  const [experience, setExperience] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [noData, setNoData] = useState(false);

  // tooltip state
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverLabel, setHoverLabel] = useState<string | null>(null);
  const [hoverColor, setHoverColor] = useState<string>("#334155");
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [countInfo, setCountInfo] = useState<{ count: number; total: number; share: number } | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  const fetchSvg = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (gender && gender !== "All") params.append("gender", gender);
      if (experience) params.append("experience", experience);
      if (profile) params.append("profile", profile);
      params.append("_", String(Date.now()));
      const res = await fetch(
        `http://localhost:8000/api/faculty/${encodeURIComponent(facultyName)}/tools-wordcloud-svg?${params.toString()}`,
        { cache: "no-store" }
      );
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

  useEffect(() => { fetchSvg(); }, [fetchSvg]);

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

  // hook up pointer listeners to compute tooltip + counts
  useEffect(() => {
    const holder = containerRef.current;
    if (!holder || !responsiveSvg) return;

    let rafId: number | null = null;

    const schedulePos = (ev: MouseEvent) => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const rect = holder.getBoundingClientRect();
        const x = Math.min(Math.max(0, ev.clientX - rect.left + 12), rect.width - (TOOLTIP_W + 12));
        const y = Math.min(Math.max(0, ev.clientY - rect.top + 12), rect.height - (TOOLTIP_H + 12));
        setTooltipPos({ x, y });
      });
    };

    const onMove = (ev: MouseEvent) => {
      schedulePos(ev);
      const t = (ev.target as Element | null)?.closest?.("text") as SVGTextElement | null;
      if (!t) {
        setShowTooltip(false);
        return;
      }
      const label = (t.textContent || "").trim();
      if (!label) {
        setShowTooltip(false);
        return;
      }
      setHoverLabel(label);
      setHoverColor(parseFill(t));
      setShowTooltip(true);

      // fetch counts (debounce is overkill; network is local)
      const params = new URLSearchParams();
      params.append("tool", label);
      if (gender && gender !== "All") params.append("gender", gender);
      if (experience) params.append("experience", experience);
      if (profile) params.append("profile", profile);

      fetch(
        `http://localhost:8000/api/faculty/${encodeURIComponent(facultyName)}/tools-wordcount?${params.toString()}`
      )
        .then((r) => r.json())
        .then((j) => setCountInfo({ count: j.count || 0, total: j.total || 0, share: j.share || 0 }))
        .catch(() => setCountInfo({ count: 0, total: 0, share: 0 }));
    };

    const onOut = (ev: MouseEvent) => {
      const next = ev.relatedTarget as Node | null;
      if (next && holder.contains(next)) return;
      setShowTooltip(false);
    };

    holder.addEventListener("mousemove", onMove);
    holder.addEventListener("mouseout", onOut);
    return () => {
      holder.removeEventListener("mousemove", onMove);
      holder.removeEventListener("mouseout", onOut);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [responsiveSvg, facultyName, gender, experience, profile]);

  const tintBg = rgba(facultyColor, 0.06);
  const tintBorder = `1px solid ${rgba(facultyColor, 0.25)}`;
  const tintText = facultyColor;

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap justify-center gap-2 mb-6">
        <select
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="All">All Genders</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Non-binary">Non-binary</option>
          <option value="No answer">No answer</option>
        </select>
        <select
          value={experience ?? ""}
          onChange={(e) => setExperience(e.target.value || null)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-purple-200 transition"
        >
          <option value="">All Experience</option>
          <option value="Less than 5">Less than 5</option>
          <option value="Between 5 and 10">Between 5 and 10</option>
          <option value="Between 11 and 20">Between 11 and 20</option>
          <option value="More than 20">More than 20</option>
        </select>
        <select
          value={profile ?? ""}
          onChange={(e) => setProfile(e.target.value || null)}
          className="border border-slate-300 rounded-md px-3 py-1 text-slate-700 text-sm shadow-sm hover:border-slate-400 focus:ring-2 focus:ring-purple-200 transition"
        >
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

      <h3 className="text-[28px] text-slate-800 mb-4 text-center">
        Which AI tools are actually being used?
      </h3>

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
            <p style={{ color: tintText, fontWeight: 600 }}>
              No data for the selected filters.
            </p>
          </div>
        )}

        {showTooltip && hoverLabel && (
          <div
            className="absolute z-50 rounded-xl shadow-lg border border-slate-200 bg-white p-2"
            style={{ left: tooltipPos.x, top: tooltipPos.y, width: TOOLTIP_W, height: TOOLTIP_H, pointerEvents: "none" }}
          >
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-medium text-slate-700">{hoverLabel}</span>
              <span className="inline-block w-2 h-2 rounded-full" style={{ background: hoverColor }} />
            </div>
            <div className="px-1 pt-1">
              {countInfo ? (
                <p className="text-xs text-slate-600">
                  Occurrences: <span className="font-semibold">{countInfo.count}</span>
                  {countInfo.total > 0 && (
                    <> ({(countInfo.share * 100).toFixed(1)}%)</>
                  )}
                </p>
              ) : (
                <p className="text-xs text-slate-400">Loading…</p>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default ToolsWordCloud;
