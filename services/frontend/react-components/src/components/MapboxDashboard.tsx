import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import mapboxgl from "mapbox-gl";
import {
  Palette,
  Microscope,
  Globe,
  Scale,
  TrendingUp,
  BookOpen,
  Pill,
  MessageSquare,
  Brain,
  Atom,
  Map,
  Video,
  Heart,
  Calculator,
  Stethoscope,
  Users,
  FlaskConical,
  ChevronDown,
  X,
} from "lucide-react";
import { createRoot } from "react-dom/client";
import type { Root } from "react-dom/client";
import "mapbox-gl/dist/mapbox-gl.css";

try {
  // @ts-ignore
  const MapboxWorker = require("mapbox-gl/dist/mapbox-gl-csp-worker").default;
  (mapboxgl as any).workerClass = MapboxWorker;
} catch {}

mapboxgl.accessToken =
  "pk.eyJ1IjoibWFudS11YiIsImEiOiJjbTN0M2E4bDcwNTdjMmxzZjUxZzEwd3YwIn0.nP8eJ0etV09R51KoBC47FA";

type MetricKey =
  | "knowledge_score"
  | "uses_score"
  | "perceptions_score"
  | "training_needs_score";

interface Faculty {
  faculty_name: string;
  color: string;
  category_score: number;
  latitude: number;
  longitude: number;
  color_rgb: number[];
  knowledge_score?: number;
  uses_score?: number;
  perceptions_score?: number;
  training_needs_score?: number;
  short_name?: string;
  n_responses?: number;
}

type CameraState = {
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
};

const HIDE_DELAY = 100;
const CAMERA_KEY = "ub-map-camera";
const DEFAULT_CAMERA: CameraState = {
  center: [2.118635482300988, 41.3852202905023],
  zoom: 15.516856636384215,
  pitch: 53.00658978150287,
  bearing: 135.53751895634423,
};

const METRICS: { key: MetricKey; label: string }[] = [
  { key: "knowledge_score", label: "Knowledge" },
  { key: "uses_score", label: "Uses" },
  { key: "perceptions_score", label: "Perceptions" },
  { key: "training_needs_score", label: "Training Needs" },
];

type MapMode = "3d" | "2d";
type MapViz2D = "spikes" | "heatmap";
type MapStyle2D = "light" | "dark";

const clamp01 = (n: number) => Math.max(0, Math.min(100, n || 0));

const loadCamera = (): CameraState | null => {
  try {
    const raw = sessionStorage.getItem(CAMERA_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (
      Array.isArray(parsed.center) &&
      parsed.center.length === 2 &&
      typeof parsed.zoom === "number" &&
      typeof parsed.pitch === "number" &&
      typeof parsed.bearing === "number"
    ) {
      return parsed as CameraState;
    }
  } catch {}
  return null;
};

const saveCamera = (cam: CameraState) => {
  try {
    sessionStorage.setItem(CAMERA_KEY, JSON.stringify(cam));
  } catch {}
};

const getScoreColor = (score: number): string => {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#84cc16";
  if (score >= 40) return "#eab308";
  if (score >= 20) return "#f97316";
  return "#ef4444";
};

const ScoreIndicator: React.FC<{ score: number }> = ({ score }) => {
  const color = getScoreColor(score);
  const percentage = score;
  return (
    <div className="flex items-center gap-2">
      <div className="relative w-12 h-12">
        <svg className="w-12 h-12 transform -rotate-90">
          <circle cx="24" cy="24" r="20" stroke="#e5e7eb" strokeWidth="4" fill="none" />
          <circle
            cx="24"
            cy="24"
            r="20"
            stroke={color}
            strokeWidth="4"
            fill="none"
            strokeDasharray={`${2 * Math.PI * 20}`}
            strokeDashoffset={`${2 * Math.PI * 20 * (1 - percentage / 100)}`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-semibold text-slate-700">{score.toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
};

/** ---------- Icon mapping (English canonical names) ---------- */
const iconMap = {
  "Fine Arts": Palette,
  Biology: Microscope,
  "Earth Sciences": Globe,
  Law: Scale,
  "Economics and Business": TrendingUp,
  Education: BookOpen,
  Pharmacy: Pill,
  Philology: MessageSquare,
  Philosophy: Brain,
  Physics: Atom,
  "Geography and History": Map,
  "Audiovisual Media": Video,
  Nursing: Heart,
  "Maths and CS": Calculator,
  Medicine: Stethoscope,
  Psychology: Users,
  Chemistry: FlaskConical,
} as const;

type IconKey = keyof typeof iconMap;

const toKey = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

const iconMapLC: Record<string, (typeof iconMap)[IconKey]> = Object.fromEntries(
  (Object.entries(iconMap) as [IconKey, (typeof iconMap)[IconKey]][]).map(([k, v]) => [
    toKey(k),
    v,
  ])
);

// Case/diacritic-insensitive lookup
const pickIconComponent = (facultyName: string) => {
  return iconMapLC[toKey(facultyName)] || Globe;
};

type MarkerHandle = { marker: mapboxgl.Marker; root: Root };

const hexToRgba = (hex: string, alpha: number) => {
  try {
    let h = hex.trim();
    if (!h.startsWith("#")) return `rgba(59,130,246,${alpha})`;
    if (h.length === 4) {
      h = `#${h[1]}${h[1]}${h[2]}${h[2]}${h[3]}${h[3]}`;
    }
    const r = parseInt(h.slice(1, 3), 16);
    const g = parseInt(h.slice(3, 5), 16);
    const b = parseInt(h.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  } catch {
    return `rgba(59,130,246,${alpha})`;
  }
};

const MAPBOX_STYLE_3D = "mapbox://styles/manu-ub/cm3t8g34e002t01qu714v03tj";
const MAPBOX_STYLES_2D: Record<MapStyle2D, string> = {
  light: "mapbox://styles/mapbox/light-v11",
  dark: "mapbox://styles/mapbox/dark-v11",
};

const MapboxDashboard: React.FC = () => {
  // ---- map mode + 2D viz type + 2D style ----
  const [mapMode, setMapMode] = useState<MapMode>("3d");
  const [mapViz2D, setMapViz2D] = useState<MapViz2D>("spikes");
  const [mapStyle2D, setMapStyle2D] = useState<MapStyle2D>("light");

  // keep latest 2D viz in a ref so style-change effect doesn't depend on it
  const mapViz2DRef = useRef<MapViz2D>("spikes");
  useEffect(() => {
    mapViz2DRef.current = mapViz2D;
  }, [mapViz2D]);

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  // track last style URL to avoid redundant setStyle
  const lastStyleRef = useRef<string | null>(null);

  // lifecycle guards for safe resize / style update
  const mapAliveRef = useRef(false);
  const mapLoadedRef = useRef(false);

  const safeResize = useCallback((from: string) => {
    const m = mapRef.current;
    if (!m || !mapAliveRef.current || !mapLoadedRef.current) return;
    const canvas = m.getCanvas?.();
    if (!canvas) return;
    try {
      m.resize();
    } catch {}
  }, []);

  // active DOM markers
  const markersRef = useRef<MarkerHandle[]>([]);

  // ---------- CUSTOM TOOLTIP OVERLAY ----------
  const tooltipElRef = useRef<HTMLDivElement | null>(null);
  const tooltipRootRef = useRef<Root | null>(null);
  const tooltipVisibleRef = useRef(false);
  const tooltipLngLatRef = useRef<[number, number] | null>(null);

  const overTriggerRef = useRef(false);
  const overPopupRef = useRef(false);

  const hideTimerRef = useRef<number | null>(null);
  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current !== null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);
  const scheduleHideTooltip = useCallback(
    (delay = HIDE_DELAY) => {
      clearHideTimer();
      hideTimerRef.current = window.setTimeout(() => {
        if (!overTriggerRef.current && !overPopupRef.current) {
          if (tooltipElRef.current) tooltipElRef.current.style.display = "none";
          tooltipVisibleRef.current = false;
        }
      }, delay);
    },
    [clearHideTimer]
  );

  const ensureTooltipEl = useCallback(
    (map: mapboxgl.Map) => {
      if (tooltipElRef.current) return tooltipElRef.current;

      const el = document.createElement("div");
      el.style.position = "absolute";
      el.style.transform = "translate(-50%, -100%)";
      el.style.zIndex = "5";
      el.style.pointerEvents = "none";
      el.style.padding = "8px 10px";
      el.style.background = "rgba(255,255,255,0.97)";
      el.style.border = "1px solid rgba(0,0,0,0.08)";
      el.style.borderRadius = "12px";
      el.style.boxShadow = "0 8px 24px rgba(0,0,0,0.18)";
      el.style.display = "none";
      el.style.minWidth = "200px";
      el.style.maxWidth = "210px";

      const onEnter = () => {
        overPopupRef.current = true;
        clearHideTimer();
      };
      const onMove = () => {
        overPopupRef.current = true;
        clearHideTimer();
      };
      const onLeave = () => {
        overPopupRef.current = false;
        scheduleHideTooltip(HIDE_DELAY);
      };

      el.addEventListener("mouseenter", onEnter);
      el.addEventListener("mousemove", onMove);
      el.addEventListener("mouseleave", onLeave);

      map.getContainer().appendChild(el);

      tooltipElRef.current = el;
      tooltipRootRef.current = createRoot(el);

      return el;
    },
    [clearHideTimer, scheduleHideTooltip]
  );

  const positionTooltip = useCallback((map: mapboxgl.Map) => {
    if (!tooltipVisibleRef.current || !tooltipElRef.current || !tooltipLngLatRef.current)
      return;
    const p = map.project(tooltipLngLatRef.current);
    tooltipElRef.current.style.left = `${p.x}px`;
    tooltipElRef.current.style.top = `${p.y - 8}px`;
  }, []);

  const onRenderRef = useRef<((e?: any) => void) | null>(null);
  const attachRender = useCallback(
    (map: mapboxgl.Map) => {
      if (onRenderRef.current) return;
      const fn = () => positionTooltip(map);
      onRenderRef.current = fn;
      map.on("render", fn);
    },
    [positionTooltip]
  );
  const detachRender = useCallback((map: mapboxgl.Map) => {
    if (!onRenderRef.current) return;
    map.off("render", onRenderRef.current);
    onRenderRef.current = null;
  }, []);

  const maxResponsesRef = useRef<number>(0);

  const TooltipContent: React.FC<{
    faculty: {
      faculty_name: string;
      color: string;
      n_responses?: number;
      knowledge_score?: number;
      uses_score?: number;
      perceptions_score?: number;
      training_needs_score?: number;
    };
    maxResponses: number;
  }> = ({ faculty, maxResponses }) => {
    const {
      faculty_name,
      color,
      knowledge_score = 0,
      uses_score = 0,
      perceptions_score = 0,
      training_needs_score = 0,
      n_responses = 0,
    } = faculty;

    const Icon = pickIconComponent(faculty_name);

    const participantsPct = maxResponses > 0 ? (n_responses / maxResponses) * 100 : 0;

    const bars = [
      {
        key: "Resp",
        value: participantsPct,
        raw: n_responses,
        color: color,
        textColor: color,
      },
      {
        key: "Know",
        value: knowledge_score,
        raw: knowledge_score,
        color: "#b91c1c",
        textColor: "#b91c1c",
      },
      {
        key: "Uses",
        value: uses_score,
        raw: uses_score,
        color: "#6b21a8",
        textColor: "#6b21a8",
      },
      {
        key: "Perc",
        value: perceptions_score,
        raw: perceptions_score,
        color: "#15803d",
        textColor: "#15803d",
      },
      {
        key: "Train",
        value: training_needs_score,
        raw: training_needs_score,
        color: "#b45309",
        textColor: "#b45309",
      },
    ];

    const W = 185;
    const H = 90;
    const chartTop = 10;
    const chartBottom = 73;
    const chartHeight = chartBottom - chartTop;
    const barWidth = 20;
    const gap = 10;
    const startX = 10;

    return (
      <div
        className="text-[11px] text-slate-700"
        style={{ minWidth: W + "px", maxWidth: W + "px" }}
      >
        <div className="flex items-center gap-2 mb-2">
          <span
            className="inline-flex items-center justify-center rounded-md p-1 shadow-sm"
            style={{
              backgroundColor: `${color}22`,
              color: color,
              border: `1px solid ${color}44`,
            }}
          >
            <Icon className="w-4 h-4" />
          </span>
          <span className="font-semibold text-slate-900 text-[12px] leading-none">
            {faculty_name}
          </span>
        </div>

        <svg
          width={W}
          height={H}
          style={{ display: "block" }}
          aria-label="faculty quick metrics"
        >
          {[25, 50, 75, 100].map((tick) => {
            const y = chartBottom - (tick / 100) * chartHeight;
            return (
              <g key={tick}>
                <line
                  x1={0}
                  x2={W}
                  y1={y}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth={tick === 100 ? 1.5 : 1}
                  strokeDasharray={tick === 100 ? "0" : "2,2"}
                />
                <text
                  x={W - 4}
                  y={y - 2}
                  textAnchor="end"
                  className="fill-slate-400 text-[9px]"
                >
                  {tick}
                </text>
              </g>
            );
          })}

          {bars.map((b, i) => {
            const v = Math.max(0, Math.min(100, b.value || 0));
            const barH = (v / 100) * chartHeight;
            const x = startX + i * (barWidth + gap);
            const y = chartBottom - barH;

            return (
              <g key={b.key}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barH}
                  rx={3}
                  ry={3}
                  fill={b.color}
                  stroke="#ffffff"
                  strokeWidth={0.5}
                />
                <text
                  x={x + barWidth / 2}
                  y={y - 4}
                  textAnchor="middle"
                  className="text-[9px] font-semibold"
                  style={{ fill: b.textColor }}
                >
                  {b.key === "Resp" ? b.raw : Math.round(b.raw ?? 0)}
                </text>
                <text
                  x={x + barWidth / 2}
                  y={chartBottom + 10}
                  textAnchor="middle"
                  className="fill-slate-600 text-[9px]"
                >
                  {b.key}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="text-[9px] text-slate-400 text-right mt-1">
          Responses normalized to 100.
        </div>
      </div>
    );
  };

  const showTooltip = useCallback(
    (
      map: mapboxgl.Map,
      lng: number,
      lat: number,
      facultyInfo: {
        faculty_name: string;
        color: string;
        n_responses?: number;
        knowledge_score?: number;
        uses_score?: number;
        perceptions_score?: number;
        training_needs_score?: number;
      }
    ) => {
      clearHideTimer();

      const el = ensureTooltipEl(map);
      tooltipLngLatRef.current = [lng, lat];

      tooltipRootRef.current?.render(
        <TooltipContent faculty={facultyInfo} maxResponses={maxResponsesRef.current} />
      );

      el.style.display = "block";
      tooltipVisibleRef.current = true;
      positionTooltip(map);
      attachRender(map);
    },
    [ensureTooltipEl, positionTooltip, attachRender, clearHideTimer]
  );

  // camera memory
  const cameraRef = useRef<CameraState>(loadCamera() || DEFAULT_CAMERA);

  // filters + data
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedGender, setSelectedGender] = useState("");
  const [selectedExperience, setSelectedExperience] = useState("");
  const [selectedProfile, setSelectedProfile] = useState("");
  const [facultyData, setFacultyData] = useState<Faculty[]>([]);
  const [selectedFaculties, setSelectedFaculties] = useState<string[]>([]);

  const visibleSelected = selectedFaculties.filter((name) => {
    const f = facultyData.find((d) => d.faculty_name === name);
    return !!f && Number.isFinite(f?.category_score);
  });

  // max n_responses for tooltip scaling
  useEffect(() => {
    let maxR = 0;
    facultyData.forEach((f) => {
      const n = f.n_responses ?? 0;
      if (n > maxR) maxR = n;
    });
    maxResponsesRef.current = maxR;
  }, [facultyData]);

  const allSelectable = useMemo(
    () =>
      facultyData
        .filter((f) => Number.isFinite(f?.category_score))
        .map((f) => f.faculty_name)
        .sort((a, b) => a.localeCompare(b)),
    [facultyData]
  );

  const handleSelectAll = useCallback(() => {
    setSelectedFaculties(allSelectable);
  }, [allSelectable]);

  const handleClearAll = useCallback(() => {
    setSelectedFaculties([]);
  }, []);

  const shortenFacultyLabel = useCallback((n: string) => {
    return n === "Economics and Business" ? "Economics" : n;
  }, []);

  const comparisonData = useMemo(
    () =>
      visibleSelected
        .map((name) => {
          const f = facultyData.find((d) => d.faculty_name === name)!;
          return {
            name: shortenFacultyLabel(f.faculty_name),
            originalName: f.faculty_name,
            score: Number(f.category_score) || 0,
            color: f.color || "#3b82f6",
          };
        })
        .sort((a, b) => b.score - a.score),
    [visibleSelected, facultyData, shortenFacultyLabel]
  );

  const radarSeries = useMemo(() => {
    return visibleSelected
      .map((name) => {
        const f = facultyData.find((d) => d.faculty_name === name);
        if (!f) return null;
        const values = METRICS.map((m) => clamp01(Number((f as any)[m.key])));
        return {
          name: shortenFacultyLabel(f.faculty_name),
          originalName: f.faculty_name,
          color: f.color || "#3b82f6",
          values,
        };
      })
      .filter(Boolean) as {
      name: string;
      originalName: string;
      color: string;
      values: number[];
    }[];
  }, [visibleSelected, facultyData, shortenFacultyLabel]);

  const [mapVisible, setMapVisible] = useState(false);
  const [sourcesReady, setSourcesReady] = useState(false);

  /** ---------- Build/push GeoJSON for spikes / heatmap ---------- */
  const buildGeoJSON = useCallback((rows: Faculty[]) => {
    const d = 0.0003;
    const features = rows
      .map((f) => {
        const lon = Number(f.longitude);
        const lat = Number(f.latitude);
        if (!isFinite(lon) || !isFinite(lat)) return null;
        return {
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [lon - d, lat - d],
                [lon + d, lat - d],
                [lon + d, lat + d],
                [lon - d, lat + d],
                [lon - d, lat - d],
              ],
            ],
          },
          properties: {
            faculty_name: f.faculty_name,
            centerLon: lon,
            centerLat: lat,
            color: f.color || "#888",
            n_responses: f.n_responses ?? 0,
            knowledge_score: f.knowledge_score ?? 0,
            uses_score: f.uses_score ?? 0,
            perceptions_score: f.perceptions_score ?? 0,
            training_needs_score: f.training_needs_score ?? 0,
            score: isFinite(f.category_score) ? f.category_score : 0,
            height: (isFinite(f.category_score) ? f.category_score : 0) * 4.2,
          },
        };
      })
      .filter(Boolean) as any[];

    return { type: "FeatureCollection", features } as any;
  }, []);

  const pushFaculties = useCallback(
    (map: mapboxgl.Map, rows: Faculty[]) => {
      const src = map.getSource("faculties") as mapboxgl.GeoJSONSource | undefined;
      if (!src) return;
      try {
        src.setData(buildGeoJSON(rows));
        map.triggerRepaint();
      } catch (e) {
        console.error("setData failed:", e);
      }
    },
    [buildGeoJSON]
  );

  /** ---------- Fetch filtered data ---------- */
  useEffect(() => {
    const fetchData = async () => {
      const params = new URLSearchParams();
      if (selectedCategory && selectedCategory !== "All")
        params.append("category", selectedCategory);
      if (selectedGender) params.append("gender", selectedGender);
      if (selectedExperience) params.append("teaching_experience", selectedExperience);
      if (selectedProfile) params.append("ub_profile", selectedProfile);

      const qs = params.toString();
      const url = `http://localhost:8000/api/spike-map?${qs}${qs ? "&" : ""}t=${Date.now()}`;

      try {
        const res = await fetch(url, { cache: "no-store" });
        const json = await res.json();
        setFacultyData(json);
      } catch (err) {
        console.error("Error fetching spike map data:", err);
      }
    };
    fetchData();
  }, [selectedCategory, selectedGender, selectedExperience, selectedProfile]);

  /** ---------- Ensure source + spike / heatmap layers exist ---------- */
  const ensureFacultiesArtifacts = useCallback(
    (map: mapboxgl.Map) => {
      try {
        let sourceWasAdded = false;
        if (!map.getSource("faculties")) {
          map.addSource("faculties", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
          });
          sourceWasAdded = true;
        }

        // extruded spikes
        if (!map.getLayer("faculties-layer")) {
          map.addLayer({
            id: "faculties-layer",
            type: "fill-extrusion",
            source: "faculties",
            paint: {
              "fill-extrusion-color": ["get", "color"],
              "fill-extrusion-height": ["max", 1, ["get", "height"]],
              "fill-extrusion-base": 0,
              "fill-extrusion-opacity": 0.9,
            },
            layout: {
              visibility: "visible",
            },
          });
        }

        // heatmap
        if (!map.getLayer("faculties-heatmap")) {
          map.addLayer({
            id: "faculties-heatmap",
            type: "heatmap",
            source: "faculties",
            paint: {
              "heatmap-weight": [
                "interpolate",
                ["linear"],
                ["get", "score"],
                0,
                0,
                100,
                1,
              ],
              "heatmap-intensity": 1,
              "heatmap-radius": 40,
              "heatmap-opacity": 0.8,
            },
            layout: {
              visibility: "none",
            },
          });
        }

        setSourcesReady(true);
        if (sourceWasAdded && facultyData.length) pushFaculties(map, facultyData);
      } catch (e) {
        console.warn("ensureFacultiesArtifacts failed:", e);
      }
    },
    [pushFaculties, facultyData]
  );

  // ---- apply map mode + 2D viz visibility + camera presets ----
  const applyMapModeAndViz = useCallback(
    (map: mapboxgl.Map, mode: MapMode, viz: MapViz2D) => {
      // terrain only in 3D mode
      if (mode === "3d") {
        try {
          if (!map.getSource("mapbox-dem")) {
            map.addSource("mapbox-dem", {
              type: "raster-dem",
              url: "mapbox://mapbox.mapbox-terrain-dem-v1",
              tileSize: 512,
              maxzoom: 14,
            });
          }
        } catch {}
        try {
          map.setTerrain({ source: "mapbox-dem", exaggeration: 1.3 });
        } catch {}
      } else {
        try {
          map.setTerrain(null);
        } catch {}
      }

      const setVis = (id: string, visible: boolean) => {
        if (!map.getLayer(id)) return;
        try {
          map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
        } catch {}
      };

      const showSpikesLayer = mode === "3d" || (mode === "2d" && viz === "spikes");

      setVis("faculties-layer", showSpikesLayer);
      setVis("faculties-heatmap", mode === "2d" && viz === "heatmap");

      // camera presets:
      if (viz === "heatmap" && mode === "2d") {
        // zoom out, top-down
        map.easeTo({
          center: DEFAULT_CAMERA.center,
          zoom: 12.5,
          pitch: 0,
          bearing: 0,
          duration: 600,
        });
      } else {
        // spikes in 3D or 2D → go to default 3D-ish view
        map.easeTo({
          center: DEFAULT_CAMERA.center,
          zoom: DEFAULT_CAMERA.zoom,
          pitch: DEFAULT_CAMERA.pitch,
          bearing: DEFAULT_CAMERA.bearing,
          duration: 600,
        });
      }
    },
    []
  );

  /** ---------- DOM markers with Lucide icons ---------- */
  const rebuildMarkers = useCallback(
    (map: mapboxgl.Map, rows: Faculty[], showMarkers: boolean) => {
      // clear existing
      markersRef.current.forEach(({ marker, root }) => {
        marker.remove();
        root.unmount();
      });
      markersRef.current = [];

      if (!showMarkers) return;

      rows.forEach((f) => {
        const lon = Number(f.longitude);
        const lat = Number(f.latitude);
        if (!isFinite(lon) || !isFinite(lat)) return;

        const Icon = pickIconComponent(f.faculty_name);

        const container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "center";
        container.style.transform = "translateY(-6px)";
        container.style.cursor = "pointer";
        container.style.pointerEvents = "auto";

        const iconWrap = document.createElement("div");
        iconWrap.style.background = "#ffffff";
        iconWrap.style.borderRadius = "9999px";
        iconWrap.style.padding = "6px";
        iconWrap.style.boxShadow = "0 1px 3px rgba(0,0,0,0.25)";
        iconWrap.style.border = "1px solid rgba(0,0,0,0.08)";

        const label = document.createElement("div");
        label.style.marginTop = "4px";
        label.style.padding = "2px 6px";
        label.style.fontSize = "12px";
        label.style.lineHeight = "1";
        label.style.borderRadius = "6px";
        label.style.background = "rgba(255,255,255,0.85)";
        label.style.color = "#111827";
        label.style.whiteSpace = "nowrap";
        label.style.boxShadow = "0 1px 2px rgba(0,0,0,0.12)";
        label.innerText = f.faculty_name;

        container.appendChild(iconWrap);
        container.appendChild(label);

        const root = createRoot(iconWrap);
        root.render(<Icon className="w-5 h-5" style={{ color: f.color }} />);

        const facultyInfoForTip = {
          faculty_name: f.faculty_name,
          color: f.color,
          n_responses: f.n_responses ?? 0,
          knowledge_score: f.knowledge_score ?? 0,
          uses_score: f.uses_score ?? 0,
          perceptions_score: f.perceptions_score ?? 0,
          training_needs_score: f.training_needs_score ?? 0,
        };

        const onEnter = () => {
          overTriggerRef.current = true;
          clearHideTimer();
          showTooltip(map, lon, lat, facultyInfoForTip);
        };
        const onMove = () => {
          overTriggerRef.current = true;
          clearHideTimer();
          showTooltip(map, lon, lat, facultyInfoForTip);
        };
        const onLeave = () => {
          overTriggerRef.current = false;
          scheduleHideTooltip(HIDE_DELAY);
        };
        const onClick = () => {
          overTriggerRef.current = true;
          clearHideTimer();
          showTooltip(map, lon, lat, facultyInfoForTip);
          setSelectedFaculties((prev) =>
            prev.includes(f.faculty_name) ? prev : [...prev, f.faculty_name]
          );
        };

        container.addEventListener("mouseenter", onEnter);
        container.addEventListener("mousemove", onMove);
        container.addEventListener("mouseleave", onLeave);
        container.addEventListener("click", onClick);

        const marker = new mapboxgl.Marker({
          element: container,
          anchor: "bottom",
          offset: [0, -8],
        })
          .setLngLat([lon, lat])
          .addTo(map);

        markersRef.current.push({ marker, root });
      });
    },
    [clearHideTimer, scheduleHideTooltip, showTooltip]
  );

  /** ---------- Apply saved camera ---------- */
  const applyCamera = useCallback((map: mapboxgl.Map) => {
    const cam = cameraRef.current;
    map.jumpTo({
      center: cam.center,
      zoom: cam.zoom,
      pitch: cam.pitch,
      bearing: cam.bearing,
    });
  }, []);

  /** ---------- Initialize map once ---------- */
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const initialCam = cameraRef.current;

    const initialStyle =
      mapMode === "3d" ? MAPBOX_STYLE_3D : MAPBOX_STYLES_2D[mapStyle2D];

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: initialStyle,
      center: initialCam.center,
      zoom: initialCam.zoom,
      pitch: initialCam.pitch,
      bearing: initialCam.bearing,
      antialias: true,
    });

    mapRef.current = map;
    mapAliveRef.current = true;
    mapLoadedRef.current = false;
    lastStyleRef.current = initialStyle;

    map.on("moveend", () => {
      const next: CameraState = {
        center: map.getCenter().toArray() as [number, number],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      };
      cameraRef.current = next;
      saveCamera(next);
    });

    map.on("style.load", () => {
      applyCamera(map);
      ensureFacultiesArtifacts(map);
      // initial mode/viz
      applyMapModeAndViz(map, mapMode, mapViz2DRef.current);
    });

    map.on("load", () => {
      mapLoadedRef.current = true;

      applyCamera(map);

      if (!map.getSource("mapbox-dem")) {
        try {
          map.addSource("mapbox-dem", {
            type: "raster-dem",
            url: "mapbox://mapbox.mapbox-terrain-dem-v1",
            tileSize: 512,
            maxzoom: 14,
          });
        } catch {}
      }
      try {
        if (mapMode === "3d") {
          map.setTerrain({ source: "mapbox-dem", exaggeration: 1.3 });
        }
      } catch {}

      if (!map.getLayer("sky")) {
        try {
          map.addLayer({
            id: "sky",
            type: "sky",
            paint: {
              "sky-type": "atmosphere",
              "sky-atmosphere-sun": [0.0, 0.0],
              "sky-atmosphere-sun-intensity": 15,
            },
          });
        } catch {}
      }

      ensureFacultiesArtifacts(map);

      const queryLayers = ["faculties-layer", "faculties-heatmap"];

      map.on("mousemove", (e) => {
        const feats = map.queryRenderedFeatures(e.point, { layers: queryLayers });
        if (!feats.length) {
          map.getCanvas().style.cursor = "";
          overTriggerRef.current = false;
          scheduleHideTooltip(HIDE_DELAY);
          return;
        }

        const f = feats[0];
        const props: any = f.properties || {};

        const lng: number = Number(props.centerLon ?? e.lngLat.lng);
        const lat: number = Number(props.centerLat ?? e.lngLat.lat);

        const facultyInfoForTip = {
          faculty_name: props.faculty_name ?? "",
          color: props.color ?? "#888",
          n_responses: Number(props.n_responses ?? 0),
          knowledge_score: Number(props.knowledge_score ?? 0),
          uses_score: Number(props.uses_score ?? 0),
          perceptions_score: Number(props.perceptions_score ?? 0),
          training_needs_score: Number(props.training_needs_score ?? 0),
        };

        map.getCanvas().style.cursor = "pointer";
        overTriggerRef.current = true;
        clearHideTimer();
        showTooltip(map, lng, lat, facultyInfoForTip);
      });

      map.on("click", (e) => {
        const feats = map.queryRenderedFeatures(e.point, { layers: queryLayers });
        if (!feats.length) return;

        const f = feats[0];
        const props: any = f.properties || {};

        const lng: number = Number(props.centerLon ?? e.lngLat.lng);
        const lat: number = Number(props.centerLat ?? e.lngLat.lat);

        const facultyInfoForTip = {
          faculty_name: props.faculty_name ?? "",
          color: props.color ?? "#888",
          n_responses: Number(props.n_responses ?? 0),
          knowledge_score: Number(props.knowledge_score ?? 0),
          uses_score: Number(props.uses_score ?? 0),
          perceptions_score: Number(props.perceptions_score ?? 0),
          training_needs_score: Number(props.training_needs_score ?? 0),
        };

        overTriggerRef.current = true;
        clearHideTimer();
        showTooltip(map, lng, lat, facultyInfoForTip);

        const facultyName = props.faculty_name;
        if (facultyName) {
          setSelectedFaculties((prev) =>
            prev.includes(facultyName) ? prev : [...prev, facultyName]
          );
        }
      });

      map.once("idle", () => {
        setMapVisible(true);
        safeResize("idle");
      });
    });

    const fallback = window.setTimeout(() => {
      if (!mapVisible) {
        setMapVisible(true);
        safeResize("fallback");
      }
    }, 2000);

    const ro = new ResizeObserver(() => {
      requestAnimationFrame(() => safeResize("ResizeObserver"));
    });
    if (mapContainer.current) ro.observe(mapContainer.current);

    return () => {
      window.clearTimeout(fallback);
      ro.disconnect();

      markersRef.current.forEach(({ marker, root }) => {
        marker.remove();
        root.unmount();
      });
      markersRef.current = [];

      clearHideTimer();
      overTriggerRef.current = false;
      overPopupRef.current = false;
      tooltipVisibleRef.current = false;
      if (tooltipElRef.current) {
        tooltipElRef.current.remove();
        tooltipElRef.current = null;
      }
      if (mapRef.current) detachRender(mapRef.current);
      tooltipRootRef.current = null;

      mapLoadedRef.current = false;
      mapAliveRef.current = false;
      map.remove();
      mapRef.current = null;
    };
  }, [
    ensureFacultiesArtifacts,
    mapVisible,
    applyCamera,
    safeResize,
    showTooltip,
    clearHideTimer,
    scheduleHideTooltip,
    detachRender,
    applyMapModeAndViz,
    mapMode,
    mapStyle2D,
  ]);

  // when mapMode or 2D viz type changes, just update layers & camera
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoadedRef.current) return;
    applyMapModeAndViz(map, mapMode, mapViz2D);
  }, [mapMode, mapViz2D, applyMapModeAndViz]);

  // when basemap style changes (light/dark in 2D)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapAliveRef.current) return;

    const targetStyle =
      mapMode === "3d" ? MAPBOX_STYLE_3D : MAPBOX_STYLES_2D[mapStyle2D];

    if (lastStyleRef.current === targetStyle) return;
    lastStyleRef.current = targetStyle;

    map.setStyle(targetStyle);

    const onStyleLoad = () => {
      // re-create sources/layers
      ensureFacultiesArtifacts(map);
      if (facultyData.length) pushFaculties(map, facultyData);

      // restore spikes/heatmap visibility + camera
      applyMapModeAndViz(map, mapMode, mapViz2DRef.current);
      // markers will be rebuilt by the separate effect that depends on mapStyle2D
    };

    map.once("style.load", onStyleLoad);

    return () => {
      map.off("style.load", onStyleLoad);
    };
  }, [
    mapMode,
    mapStyle2D,
    ensureFacultiesArtifacts,
    facultyData,
    pushFaculties,
    applyMapModeAndViz,
  ]);

  /** ---------- Update spikes/heatmap data ---------- */
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !sourcesReady) return;
    pushFaculties(map, facultyData);
  }, [facultyData, sourcesReady, pushFaculties]);

  /** ---------- Rebuild markers when data, viz or basemap changes ---------- */
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const spikesActive =
      mapMode === "3d" || (mapMode === "2d" && mapViz2D === "spikes");

    rebuildMarkers(map, facultyData, spikesActive);
  }, [facultyData, mapMode, mapViz2D, mapStyle2D, rebuildMarkers]);

  /** ---------- Ensure markers once visible ---------- */
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapVisible) return;

    const spikesActive = mapMode === "3d" || (mapMode === "2d" && mapViz2D === "spikes");
    rebuildMarkers(map, facultyData, spikesActive);
  }, [mapVisible, facultyData, mapMode, mapViz2D, rebuildMarkers]);

  // -------------------- BAR CHART TOOLTIP --------------------
  const chartBoxRef = useRef<HTMLDivElement | null>(null);
  const [chartTip, setChartTip] = useState<{
    show: boolean;
    x: number;
    y: number;
    name: string;
    score: number;
  } | null>(null);

  const showChartTip = (e: React.MouseEvent, name: string, score: number) => {
    const host = chartBoxRef.current;
    if (!host) return;
    const rect = host.getBoundingClientRect();
    setChartTip({
      show: true,
      x: e.clientX - rect.left + 8,
      y: e.clientY - rect.top - 10,
      name,
      score,
    });
  };
  const hideChartTip = () => setChartTip((t) => (t ? { ...t, show: false } : t));

  // -------------------- RADAR (SPIDER) CHART --------------------
  const radarBoxRef = useRef<HTMLDivElement | null>(null);
  const [radarTip, setRadarTip] = useState<{
    show: boolean;
    x: number;
    y: number;
    faculty: string;
    metric: string;
    value: number;
    color: string;
  } | null>(null);

  const showRadarTip = (
    e: React.MouseEvent,
    faculty: string,
    metric: string,
    value: number,
    color: string
  ) => {
    const host = radarBoxRef.current;
    if (!host) return;
    const rect = host.getBoundingClientRect();
    setRadarTip({
      show: true,
      x: e.clientX - rect.left + 8,
      y: e.clientY - rect.top - 10,
      faculty,
      metric,
      value,
      color,
    });
  };
  const hideRadarTip = () => setRadarTip((t) => (t ? { ...t, show: false } : t));

  const renderRadar = () => {
    const W = 390;
    const H = 390;
    const cx = W / 2;
    const cy = H / 2;
    const R = 175;
    const axes = METRICS.length;

    const angleFor = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / axes;
    const pointAt = (i: number, valuePct: number) => {
      const r = (clamp01(valuePct) / 100) * R;
      const a = angleFor(i);
      return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
    };

    const rings = [25, 50, 75, 100];

    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
        {METRICS.map((m, i) => {
          const end = pointAt(i, 100);
          return (
            <line
              key={`axis-${m.key}`}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="#e5e7eb"
              strokeWidth="1"
            />
          );
        })}

        {rings.map((r) => {
          const path = METRICS.map((_, i) => pointAt(i, r))
            .map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`)
            .join(" ");
          return (
            <path
              key={`ring-${r}`}
              d={`${path} Z`}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={r === 100 ? 1.5 : 1}
              opacity={r === 100 ? 1 : 0.7}
            />
          );
        })}

        {radarSeries.map((s, si) => {
          const pts = s.values.map((v, i) => pointAt(i, v));
          const d =
            pts
              .map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`)
              .join(" ") + " Z";
          return (
            <g key={`series-${si}`} style={{ pointerEvents: "none" }}>
              <path d={d} fill={hexToRgba(s.color, 0.15)} stroke={s.color} strokeWidth={2} />
            </g>
          );
        })}

        {radarSeries.map((s, si) =>
          s.values.map((v, i) => {
            const p = pointAt(i, v);
            return (
              <circle
                key={`pt-${si}-${i}`}
                cx={p.x}
                cy={p.y}
                r={4.5}
                fill={s.color}
                stroke="#fff"
                strokeWidth={1.5}
                style={{ pointerEvents: "auto", cursor: "default" }}
                onMouseEnter={(e) => showRadarTip(e, s.name, METRICS[i].label, v, s.color)}
                onMouseMove={(e) => showRadarTip(e, s.name, METRICS[i].label, v, s.color)}
                onMouseLeave={hideRadarTip}
              />
            );
          })
        )}

        {METRICS.map((m, i) => {
          const labelPt = pointAt(i, 100);
          const a = angleFor(i);
          const cos = Math.cos(a);
          const sin = Math.sin(a);
          const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
          const dy = sin > 0.3 ? "1em" : sin < -0.3 ? "-0.4em" : "0.35em";
          return (
            <text
              key={`label-${m.key}`}
              x={labelPt.x}
              y={labelPt.y}
              textAnchor={anchor as any}
              dominantBaseline="middle"
              className="fill-slate-700 text-sm font-medium"
              dy={dy}
            >
              {m.label}
            </text>
          );
        })}
      </svg>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-[1800px] mx-auto">
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-light text-slate-800 mb-2">Exploring the Map</h1>
          <p className="text-slate-600">Click on any faculty to start exploring.</p>
        </div>

        <div className="grid grid-cols-12 gap-3">
          <div className="col-span-3 space-y-4">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-medium text-slate-800 mb-4">Filters</h2>

              <FilterSelect
                label="Category"
                value={selectedCategory}
                onChange={setSelectedCategory}
                options={[
                  { value: "All", label: "All" },
                  { value: "knowledge", label: "Knowledge of AI" },
                  { value: "uses", label: "Uses of AI" },
                  { value: "perceptions", label: "Perceptions" },
                  { value: "training", label: "Training" },
                ]}
              />
              <FilterSelect
                label="Gender"
                value={selectedGender}
                onChange={setSelectedGender}
                options={[
                  { value: "", label: "All genders" },
                  { value: "Male", label: "Male" },
                  { value: "Female", label: "Female" },
                  { value: "Non-Binary", label: "Non-binary" },
                  { value: "No answer", label: "No anwser" },
                ]}
              />
              <FilterSelect
                label="Teaching Experience"
                value={selectedExperience}
                onChange={setSelectedExperience}
                options={[
                  { value: "", label: "All teaching experiences" },
                  { value: "Less than 5", label: "Less than 5 years" },
                  { value: "Between 5 and 10", label: "Between 5 and 10 years" },
                  { value: "Between 11 and 20", label: "Between 11 and 20 years" },
                  { value: "More than 20", label: "More than 20 years" },
                ]}
              />
              <FilterSelect
                label="Profile"
                value={selectedProfile}
                onChange={setSelectedProfile}
                options={[
                  { value: "", label: "All profiles" },
                  { value: "Senior Lecturer", label: "Senior Lecturer" },
                  { value: "Associate", label: "Associate" },
                  { value: "Collab", label: "Permanent Collaborator" },
                  { value: "Lecturer", label: "Lecturer" },
                  { value: "PreDoc", label: "PreDoc" },
                  { value: "PostDoc", label: "PostDoc" },
                  { value: "Professor", label: "Professor" },
                ]}
              />
            </div>

            <div
              className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6"
              style={{ overflowX: "auto" }}
            >
              <div
                className="flex items-center justify-between mb-1"
                style={{ minWidth: "175px" }}
              >
                <h2 className="text-lg font-medium text-slate-800">Selected faculties</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSelectAll}
                    disabled={
                      allSelectable.length === 0 ||
                      selectedFaculties.length === allSelectable.length
                    }
                    className={`text-xs px-2 py-1 rounded-md border transition
                      ${
                        allSelectable.length === 0 ||
                        selectedFaculties.length === allSelectable.length
                          ? "opacity-50 cursor-not-allowed border-slate-200 text-slate-400 bg-slate-50"
                          : "border-slate-300 text-slate-600 hover:bg-slate-50"
                      }`}
                    title="Select all faculties"
                  >
                    Select all
                  </button>
                  <button
                    onClick={handleClearAll}
                    disabled={selectedFaculties.length === 0}
                    className={`text-xs px-2 py-1 rounded-md border transition
                      ${
                        selectedFaculties.length === 0
                          ? "opacity-50 cursor-not-allowed border-slate-200 text-slate-400 bg-slate-50"
                          : "border-slate-300 text-slate-600 hover:bg-slate-50"
                      }`}
                    title="Clear selection"
                  >
                    Clear
                  </button>
                </div>
              </div>
              <p className="text-sm text-slate-500 mb-4">
                {visibleSelected.length} selected{" "}
                {allSelectable.length ? `· ${allSelectable.length} available` : ""}
              </p>

              <div
                className="space-y-3 max-h-[500px] overflow-y-auto"
                style={{ minWidth: "175px" }}
              >
                {visibleSelected.map((name) => {
                  const f = facultyData.find((d) => d.faculty_name === name)!;
                  const RowIcon = pickIconComponent(f.faculty_name);

                  const handleRemove = (e: React.MouseEvent) => {
                    e.stopPropagation();
                    setSelectedFaculties((prev) => prev.filter((x) => x !== name));
                  };

                  const handleNavigate = () => {
                    window.postMessage(
                      {
                        type: "ub:navigate-to-faculty",
                        facultyName: f.faculty_name,
                      },
                      "*"
                    );
                  };

                  return (
                    <div
                      key={name}
                      className={`
                        group
                        relative
                        flex items-center gap-3 p-2 rounded-lg
                        hover:bg-slate-50
                        transition
                        cursor-pointer
                      `}
                      onClick={handleNavigate}
                    >
                      <div
                        className="p-2 rounded-lg flex-shrink-0"
                        style={{ backgroundColor: `${f.color}20` }}
                      >
                        <div style={{ color: f.color }}>
                          <RowIcon className="w-4 h-4" />
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-700 truncate">
                          {f.faculty_name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {Number(f.category_score).toFixed(2)}
                        </p>
                      </div>

                      <div className="relative flex items-start pr-2">
                        <div className="pr-6">
                          <ScoreIndicator score={f.category_score} />
                        </div>

                        <button
                          onClick={handleRemove}
                          className={`
                            absolute top-0 right-0
                            hidden group-hover:flex
                            items-center justify-center
                            h-5 w-5 rounded-full
                            border border-slate-300
                            bg-white text-slate-500
                            shadow-sm
                            hover:bg-red-50 hover:text-red-600 hover:border-red-300
                            focus:outline-none
                          `}
                          title="Remove from comparison"
                        >
                          <X className="w-3 h-3" strokeWidth={2} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="col-span-9">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              {/* Map header controls */}
              <div className="flex flex-wrap items-center justify-between gap-3 px-4 pt-4 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700 mr-2">Map mode</span>
                  <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 overflow-hidden text-xs">
                    <button
                      onClick={() => setMapMode("3d")}
                      className={
                        "px-3 py-1.5 " +
                        (mapMode === "3d"
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-100")
                      }
                    >
                      3D
                    </button>
                    <button
                      onClick={() => setMapMode("2d")}
                      className={
                        "px-3 py-1.5 border-l border-slate-200 " +
                        (mapMode === "2d"
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-100")
                      }
                    >
                      2D
                    </button>
                  </div>
                </div>

                {mapMode === "2d" && (
              <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-slate-600">Visualization</span>
                  <select
                    value={mapViz2D}
                    onChange={(e) => setMapViz2D(e.target.value as MapViz2D)}
                    className="px-2 py-1 rounded-md border border-slate-200 bg-white text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="spikes">Spikes</option>
                    <option value="heatmap">Heatmap</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-slate-600">Basemap</span>
                  <select
                    value={mapStyle2D}
                    onChange={(e) => setMapStyle2D(e.target.value as MapStyle2D)}
                    className="px-2 py-1 rounded-md border border-slate-200 bg-white text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                  </select>
                </div>
              </div>
            )}

              </div>

              <div className="w-full h-[680px] relative">
                <div ref={mapContainer} className="absolute inset-0" />
                {!mapVisible && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 z-10">
                    <Globe className="w-12 h-12 text-slate-400 mb-3 animate-pulse" />
                    <h3 className="text-lg font-medium text-slate-600 mb-1">
                      Loading map...
                    </h3>
                    <p className="text-sm text-slate-500">
                      Please wait while the map initializes
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-6" style={{ marginTop: "13px" }}>
              {/* Faculty Comparison */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-medium text-slate-800 mb-4">Faculty Comparison</h3>

                {comparisonData.length === 0 ? (
                  <div className="h-[300px] bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl flex items-center justify-center">
                    <div className="text-center">
                      <TrendingUp className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                      <p className="text-slate-600 font-medium">Bar Chart</p>
                      <p className="text-sm text-slate-500 mt-1">
                        Select a faculty on the map to start a comparative analysis
                      </p>
                    </div>
                  </div>
                ) : (
                  <div
                    ref={chartBoxRef}
                    className="relative rounded-xl bg-gradient-to-br from-white to-slate-50 p-4 h-[300px] overflow-y-auto"
                  >
                    <ol className="space-y-3 pr-2">
                      {comparisonData.map((item) => {
                        const RowIcon = pickIconComponent(item.originalName);
                        return (
                          <li
                            key={item.originalName}
                            className={`
                              flex flex-col xl:flex-row
                              xl:items-center
                              gap-2 xl:gap-3
                            `}
                            onMouseEnter={(e) => showChartTip(e, item.name, item.score)}
                            onMouseMove={(e) => showChartTip(e, item.name, item.score)}
                            onMouseLeave={hideChartTip}
                          >
                            <div
                              className={`
                                flex items-center gap-2
                                text-sm font-semibold text-slate-800 truncate
                                w-full
                                xl:w-28 2xl:w-32
                                shrink-0
                              `}
                            >
                              <span
                                className="inline-flex items-center justify-center rounded-md p-1"
                                style={{ background: `${item.color}22`, color: item.color }}
                                title={item.originalName}
                              >
                                <RowIcon className="w-4 h-4" />
                              </span>
                              <span className="truncate">{item.name}</span>
                            </div>

                            <div
                              className={`
                                relative
                                w-full xl:flex-1
                                h-[2.5rem] xl:h-8
                                min-h-[2.5rem]
                                rounded-lg border border-slate-200 bg-slate-100 overflow-hidden
                              `}
                            >
                              {[25, 50, 75, 100].map((p) => (
                                <div
                                  key={p}
                                  className="absolute top-0 bottom-0 border-l border-slate-200"
                                  style={{ left: `${p}%` }}
                                />
                              ))}

                              <div
                                className="absolute inset-y-0 left-0 rounded-r-lg transition-all duration-500"
                                style={{
                                  width: `${Math.max(0, Math.min(100, item.score))}%`,
                                  background: item.color || "#3b82f6",
                                }}
                                role="meter"
                                aria-label={`${item.name} score`}
                                aria-valuenow={Math.round(item.score)}
                                aria-valuemin={0}
                                aria-valuemax={100}
                              />
                            </div>

                            <div
                              className={`
                                w-full xl:w-12
                                text-right text-sm font-semibold text-slate-800
                              `}
                            >
                              {item.score.toFixed(1)}
                            </div>
                          </li>
                        );
                      })}
                    </ol>

                    {chartTip?.show && (
                      <div
                        className="absolute pointer-events-none px-2 py-1 text-[11px] rounded-md shadow-sm border border-slate-200 bg-white text-slate-700"
                        style={{ left: chartTip.x, top: chartTip.y }}
                      >
                        <span className="font-semibold">{chartTip.name}</span>
                        <span className="ml-2">{chartTip.score.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Multi-dimensional Analysis (Spider Chart) */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-lg font-medium text-slate-800 mb-4">
                  Multi-dimensional Analysis
                </h3>

                {radarSeries.length === 0 ? (
                  <div className="h-[300px] bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl flex items-center justify-center">
                    <div className="text-center">
                      <div className="relative w-12 h-12 mx-auto mb-3">
                        <div className="absolute inset-0 border-4 border-slate-300 rounded-full" />
                        <div className="absolute inset-2 border-4 border-slate-400 rounded-full" />
                        <div className="absolute inset-4 border-4 border-slate-500 rounded-full" />
                      </div>
                      <p className="text-slate-600 font-medium">Spider Chart</p>
                      <p className="text-sm text-slate-500 mt-1">
                        Select a faculty on the map to view faculty metrics
                      </p>
                    </div>
                  </div>
                ) : (
                  <div
                    ref={radarBoxRef}
                    className="relative h-[300px] rounded-xl bg-gradient-to-br from-white to-slate-50 p-2"
                  >
                    <div className="absolute inset-0">{renderRadar()}</div>

                    {radarTip?.show && (
                      <div
                        className="absolute pointer-events-none px-2 py-1 text-[11px] rounded-md shadow-sm border border-slate-200 bg-white text-slate-700"
                        style={{ left: radarTip.x, top: radarTip.y }}
                      >
                        <span
                          className="inline-block w-2 h-2 rounded-sm mr-1 align-middle"
                          style={{ background: radarTip.color }}
                        />
                        <span className="font-semibold">{radarTip.faculty}</span>
                        <span className="mx-1">•</span>
                        <span>{radarTip.metric}:</span>{" "}
                        <span className="font-medium">{radarTip.value.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          {/* /Right Side - Map */}
        </div>
      </div>
    </div>
  );
};

const FilterSelect: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}> = ({ label, value, onChange, options }) => (
  <div className="mb-4">
    <label className="block text-sm text-slate-600 mb-2">{label}</label>
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-slate-700 appearance-none cursor-pointer hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
    </div>
  </div>
);

export default MapboxDashboard;
