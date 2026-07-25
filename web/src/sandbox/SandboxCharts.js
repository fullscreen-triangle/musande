// =====================================================================
//  Agent Smith Sandbox — charts (plain SVG, no D3).
//
//  Every chart is a hand-drawn SVG with a fixed viewBox and its own tiny
//  scale helpers — same discipline as the rest of the OS web tools (no D3
//  lifecycle, no chart library). What is different here is that the charts
//  are CROSSFILTER-LINKED through the shared sandbox store:
//
//    - The Phase Timeline and the Count Staircase are BRUSHABLE: drag over a
//      span of ticks (optionally on one agent's lane) and the selection is
//      pushed to the store. Every other view — the outcome log, the water-
//      fill highlight, AND the editor's line highlight — reacts.
//    - Clicking a scene column in the Water-Fill diagram toggles that scene
//      in the selection, which highlights the `scene ...` line in the code.
//    - Selected records draw at full opacity; unselected ones grey back, so
//      the brushed slice stands out against its context.
//
//  This is the "see an output slice, see the code that made it" mechanism,
//  built for real (not a string replace).
// =====================================================================

import React, { useMemo, useRef, useState, useCallback } from "react";
import { useSandbox } from "./store";

const AGENT_COLORS = ["#5b8dd9", "#5fa85f", "#d4a849", "#c94a4a", "#4db8b8", "#a479e2"];

function agentColor(name, agents) {
  const i = Math.max(0, agents.indexOf(name));
  return AGENT_COLORS[i % AGENT_COLORS.length];
}

// tiny scale helpers ---------------------------------------------------
const lin = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);
const ticks = (max, n = 5) => Array.from({ length: n + 1 }, (_, i) => Math.round((i * max) / n));

// =====================================================================
//  The output grid: given structure/attention/records, lay the charts out.
// =====================================================================

export default function SandboxCharts() {
  const records = useSandbox((s) => s.records);
  const structure = useSandbox((s) => s.structure);
  const attention = useSandbox((s) => s.attention);
  const society = useSandbox((s) => s.society);

  if (!records.length && !structure) {
    return <Empty label="Compile and run a script to see the charts." />;
  }

  return (
    <div className="ags-grid">
      <ChartFrame title="Character χ — the self-graph and its cheapest cut">
        <SelfGraph structure={structure} />
      </ChartFrame>

      <ChartFrame title="Water-filling — attention divides at a single price p*">
        <WaterFill attention={attention} />
      </ChartFrame>

      <ChartFrame title="Phase timeline — drag to brush ticks (blue: construct · amber: commit)">
        <PhaseTimeline records={records} />
      </ChartFrame>

      <ChartFrame title="Committed count — the monotone staircase (I2)">
        <CountStaircase records={records} />
      </ChartFrame>

      <ChartFrame title="Residual descent — and where it stops (the floor β)">
        <ResidualDescent records={records} structure={structure} />
      </ChartFrame>

      {society && (
        <ChartFrame title="Society χ — coordination without shared internals">
          <SocietyBadge society={society} />
        </ChartFrame>
      )}
    </div>
  );
}

// =====================================================================
//  Structure — the self-graph with the χ cut drawn as dashed edges.
//  A simple deterministic circular layout (no force sim needed for <8 parts).
// =====================================================================

function SelfGraph({ structure }) {
  const toggleDim = useSandbox((s) => s.toggleDim);
  if (!structure || !structure.parts.length) return <Empty label="No structure." />;

  const W = 360, H = 240, cx = W / 2, cy = H / 2, R = 84;
  const parts = structure.parts;
  const pos = {};
  parts.forEach((p, i) => {
    const a = (2 * Math.PI * i) / parts.length - Math.PI / 2;
    pos[p] = { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) };
  });
  const sideSet = new Set(structure.side);
  const isCut = (a, b) => sideSet.has(a) !== sideSet.has(b);

  return (
    <div>
      <div className="ags-metrics">
        <Metric k="χ" v={structure.chi} />
        <Metric k="realised floor" v={structure.floor} />
        <Metric k="non-local" v={structure.nonLocal ? "yes" : "no"} />
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="ags-svg" style={{ height: 240 }}>
        {structure.separations.map((e, i) => {
          const s = pos[e.a], t = pos[e.b];
          if (!s || !t) return null;
          const cut = isCut(e.a, e.b);
          return (
            <g key={i}>
              <line
                x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                stroke={cut ? "#d4a849" : "#3a3a4a"}
                strokeWidth={cut ? 2 : Math.max(1, e.cost)}
                strokeDasharray={cut ? "6,3" : "none"}
                strokeOpacity={0.85}
              />
              <text
                x={(s.x + t.x) / 2} y={(s.y + t.y) / 2 - 5}
                fill="#9a9690" fontSize="10" textAnchor="middle" fontFamily="monospace"
              >
                {e.cost}
              </text>
            </g>
          );
        })}
        {parts.map((p) => {
          const inSide = sideSet.has(p);
          return (
            <g key={p} style={{ cursor: "default" }}>
              <circle
                cx={pos[p].x} cy={pos[p].y} r={15}
                fill={inSide ? "#1e3a5f" : "#3a1e1e"}
                stroke={inSide ? "#5b8dd9" : "#c94a4a"}
                strokeWidth={2}
              />
              <text
                x={pos[p].x} y={pos[p].y} dy="0.35em"
                fill="#e8e4dd" fontSize="10" textAnchor="middle"
                fontFamily="monospace" pointerEvents="none"
              >
                {p}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="ags-note">
        The dashed amber edges are the cheapest way to split this agent into two
        parts — their total weight is χ. It is realised by a <em>set</em> of
        edges, never a single label: that is what “non-local” means.
      </p>
    </div>
  );
}

// =====================================================================
//  Water-filling — columns are per-scene entry margins (g0), the amber line
//  is the single equalizing price p*, fill shows the attended scenes. Click
//  a column to toggle that scene in the crossfilter (→ highlights the code).
// =====================================================================

function WaterFill({ attention }) {
  const toggleDim = useSandbox((s) => s.toggleDim);
  const sel = useSandbox((s) => s.sel);
  if (!attention || !attention.rows.length) return <Empty label="No attention data." />;

  const W = 360, H = 220, m = { t: 16, r: 16, b: 34, l: 36 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const rows = attention.rows;
  const maxG = Math.max(...rows.map((r) => r.g0)) * 1.1 || 1;
  const y = lin(0, maxG, ih, 0);
  const bw = iw / rows.length;
  const price = attention.price;

  return (
    <div>
      <div className="ags-metrics">
        <Metric k="price p*" v={price.toFixed(4)} />
        <Metric k="budget" v={attention.budget} />
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="ags-svg" style={{ height: 220 }}>
        <g transform={`translate(${m.l},${m.t})`}>
          {rows.map((r, i) => {
            const selected = sel.scenes.has(r.scene);
            const x = i * bw + bw * 0.15;
            const w = bw * 0.7;
            const colTop = y(r.g0);
            const waterTop = y(price);
            return (
              <g key={r.scene} onClick={() => toggleDim("scenes", r.scene)} style={{ cursor: "pointer" }}>
                {/* full column (entry margin) */}
                <rect
                  x={x} y={colTop} width={w} height={ih - colTop}
                  fill="#1a1a24" stroke={selected ? "#e8e4dd" : "#2a2a36"}
                  strokeWidth={selected ? 2 : 1} rx={3}
                />
                {/* filled water above the price line */}
                {r.active && (
                  <rect
                    x={x} y={waterTop} width={w} height={ih - waterTop}
                    fill={selected ? "#5b8dd980" : "#5b8dd940"} stroke="#5b8dd9" rx={3}
                  />
                )}
                <text
                  x={x + w / 2} y={ih + 14} textAnchor="middle"
                  fill={r.active ? "#e8e4dd" : "#5a5854"} fontSize="9" fontFamily="monospace"
                >
                  {r.scene}
                </text>
              </g>
            );
          })}
          {/* price line */}
          <line x1={-6} x2={iw + 6} y1={y(price)} y2={y(price)} stroke="#d4a849" strokeWidth={2} strokeDasharray="6,3" />
          <text x={iw} y={y(price) - 4} textAnchor="end" fill="#d4a849" fontSize="9" fontFamily="monospace">
            p* = {price.toFixed(3)}
          </text>
          {ticks(maxG, 4).map((tv, i) => (
            <text key={i} x={-6} y={y(tv)} dy="0.32em" textAnchor="end" fill="#5a5854" fontSize="9" fontFamily="monospace">
              {tv}
            </text>
          ))}
        </g>
      </svg>
      <p className="ags-note">
        Attention pours into the steepest markets until every attended one
        returns the same marginal edge <em>p*</em>. Columns below the amber
        line stay dry. <strong>Click a column</strong> to light up its line in
        the code.
      </p>
    </div>
  );
}

// =====================================================================
//  Phase timeline — brushable. Rows = agents, x = tick. Drag to select a
//  tick span (and, if the drag stays within one lane, that agent too).
// =====================================================================

function PhaseTimeline({ records }) {
  const setSelection = useSandbox((s) => s.setSelection);
  const clearSelection = useSandbox((s) => s.clearSelection);
  const isSelected = useSandbox((s) => s.isSelected);
  const selVersion = useSandbox((s) => s.selVersion);
  const svgRef = useRef(null);
  const [drag, setDrag] = useState(null); // { x0, x1, lane }

  const agents = useMemo(() => [...new Set(records.map((r) => r.agent))], [records]);
  const maxTick = useMemo(() => Math.max(1, ...records.map((r) => r.tick)), [records]);

  const W = 360, H = 40 + agents.length * 26, m = { t: 10, r: 12, b: 22, l: 72 };
  const iw = W - m.l - m.r, laneH = 20;
  const x = lin(0.5, maxTick + 0.5, 0, iw);
  const laneY = (agent) => agents.indexOf(agent) * 26;

  const pxToTick = useCallback(
    (px) => {
      const rect = svgRef.current.getBoundingClientRect();
      const localX = ((px - rect.left) / rect.width) * W - m.l;
      return Math.round(0.5 + (localX / iw) * maxTick);
    },
    // W and m.l are render-stable constants
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [iw, maxTick]
  );
  const pxToLane = useCallback(
    (py) => {
      const rect = svgRef.current.getBoundingClientRect();
      const localY = ((py - rect.top) / rect.height) * H - m.t;
      const idx = Math.floor(localY / 26);
      return agents[idx] ?? null;
    },
    // H and m.t are render-stable constants
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [agents]
  );

  const onDown = (e) => {
    const t = pxToTick(e.clientX);
    setDrag({ x0: t, x1: t, lane: pxToLane(e.clientY) });
  };
  const onMove = (e) => {
    if (!drag) return;
    setDrag((d) => ({ ...d, x1: pxToTick(e.clientX) }));
  };
  const onUp = () => {
    if (!drag) return;
    const lo = Math.max(1, Math.min(drag.x0, drag.x1));
    const hi = Math.min(maxTick, Math.max(drag.x0, drag.x1));
    if (hi < lo) {
      clearSelection();
    } else {
      setSelection({
        tickRange: [lo, hi],
        agents: drag.lane ? new Set([drag.lane]) : new Set(),
      });
    }
    setDrag(null);
  };

  return (
    <div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="ags-svg"
        style={{ height: H, cursor: "crosshair", userSelect: "none" }}
        onMouseDown={onDown}
        onMouseMove={onMove}
        onMouseUp={onUp}
        onMouseLeave={() => drag && onUp()}
      >
        <g transform={`translate(${m.l},${m.t})`}>
          {records.map((r, i) => {
            const on = isSelected(r); // read selVersion so this re-renders
            void selVersion;
            const bx = x(r.tick - 0.42), bw = x(r.tick + 0.42) - x(r.tick - 0.42);
            const by = laneY(r.agent);
            const commit = r.outcome === "commit";
            return (
              <rect
                key={i}
                x={bx} y={by} width={Math.max(1, bw - 1)} height={laneH}
                rx={1}
                fill={commit ? "#6a4a2a" : "#2a4a6a"}
                opacity={on ? (commit ? 0.95 : 0.7) : 0.18}
              />
            );
          })}
          {agents.map((a) => (
            <text
              key={a} x={-6} y={laneY(a) + laneH / 2} dy="0.32em" textAnchor="end"
              fill={agentColor(a, agents)} fontSize="9" fontFamily="monospace"
            >
              {a}
            </text>
          ))}
          {/* brush rectangle */}
          {drag && (
            <rect
              x={x(Math.min(drag.x0, drag.x1) - 0.5)}
              y={drag.lane ? laneY(drag.lane) - 2 : -2}
              width={Math.abs(x(drag.x1) - x(drag.x0)) + x(0.5) - x(0)}
              height={drag.lane ? laneH + 4 : agents.length * 26}
              fill="#e8e4dd18" stroke="#e8e4dd" strokeDasharray="3,2"
            />
          )}
          {ticks(maxTick, Math.min(maxTick, 10)).map((tv, i) => (
            <text key={i} x={x(tv)} y={agents.length * 26 + 12} textAnchor="middle" fill="#5a5854" fontSize="8" fontFamily="monospace">
              {tv}
            </text>
          ))}
        </g>
      </svg>
      <p className="ags-note">
        <strong>Drag</strong> across ticks to brush a slice — stay in one lane
        to pick that agent too. The log, the code, and the other charts follow
        your selection.
      </p>
    </div>
  );
}

// =====================================================================
//  Count staircase — per agent, count vs tick. Selected ticks drawn bold.
// =====================================================================

function CountStaircase({ records }) {
  const isSelected = useSandbox((s) => s.isSelected);
  const selVersion = useSandbox((s) => s.selVersion);
  const agents = useMemo(() => [...new Set(records.map((r) => r.agent))], [records]);
  const maxTick = Math.max(1, ...records.map((r) => r.tick));
  const maxCount = Math.max(1, ...records.map((r) => r.count));

  const W = 360, H = 180, m = { t: 12, r: 12, b: 22, l: 34 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const x = lin(0, maxTick, 0, iw), y = lin(0, maxCount * 1.1, ih, 0);

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="ags-svg" style={{ height: 180 }}>
        <g transform={`translate(${m.l},${m.t})`}>
          {agents.map((a) => {
            const pts = records.filter((r) => r.agent === a).sort((p, q) => p.tick - q.tick);
            let d = "";
            pts.forEach((p, i) => {
              const px = x(p.tick), py = y(p.count);
              if (i === 0) d += `M ${x(0)} ${y(0)} L ${px} ${y(pts[0].count)}`;
              else d += ` H ${px} V ${py}`;
            });
            void selVersion;
            return (
              <g key={a}>
                <path d={d} fill="none" stroke={agentColor(a, agents)} strokeWidth={1.5} opacity={0.9} />
                {pts.filter(isSelected).map((p, i) => (
                  <circle key={i} cx={x(p.tick)} cy={y(p.count)} r={3} fill={agentColor(a, agents)} />
                ))}
              </g>
            );
          })}
          {ticks(maxCount, 4).map((tv, i) => (
            <text key={i} x={-6} y={y(tv)} dy="0.32em" textAnchor="end" fill="#5a5854" fontSize="9" fontFamily="monospace">{tv}</text>
          ))}
          <text x={0} y={-2} fill="#5a5854" fontSize="9" fontFamily="monospace">count m</text>
        </g>
      </svg>
      <p className="ags-note">
        The count only ever climbs — you cannot un-commit. Brushed ticks are
        marked. A copy restarted at zero would trace a different staircase: a
        different individual.
      </p>
    </div>
  );
}

// =====================================================================
//  Residual descent — the punchline chart. Shows residual falling and
//  flattening at the floor; a dashed line marks the declared floor level.
// =====================================================================

function ResidualDescent({ records, structure }) {
  const agents = useMemo(() => [...new Set(records.map((r) => r.agent))], [records]);
  const maxTick = Math.max(1, ...records.map((r) => r.tick));
  const W = 360, H = 180, m = { t: 12, r: 12, b: 22, l: 40 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const x = lin(0, maxTick, 0, iw), y = lin(0, 1, ih, 0);
  // floorNorm in the engine is min(0.08, 0.02 + 0.01*floor); show it as a band.
  const floorNorm = Math.min(0.08, 0.02 + 0.01 * (structure?.declaredFloor ?? 2));

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="ags-svg" style={{ height: 180 }}>
        <g transform={`translate(${m.l},${m.t})`}>
          {/* floor band */}
          <rect x={0} y={y(floorNorm)} width={iw} height={ih - y(floorNorm)} fill="#c94a4a18" />
          <line x1={0} x2={iw} y1={y(floorNorm)} y2={y(floorNorm)} stroke="#c94a4a" strokeDasharray="4,3" strokeWidth={1} />
          <text x={iw} y={y(floorNorm) - 3} textAnchor="end" fill="#c94a4a" fontSize="9" fontFamily="monospace">
            floor β
          </text>
          {agents.map((a) => {
            const pts = records.filter((r) => r.agent === a).sort((p, q) => p.tick - q.tick);
            const d = pts.map((p, i) => `${i ? "L" : "M"} ${x(p.tick)} ${y(p.residual)}`).join(" ");
            return <path key={a} d={d} fill="none" stroke={agentColor(a, agents)} strokeWidth={1.5} opacity={0.9} />;
          })}
          {[0, 0.5, 1].map((tv, i) => (
            <text key={i} x={-6} y={y(tv)} dy="0.32em" textAnchor="end" fill="#5a5854" fontSize="9" fontFamily="monospace">{tv}</text>
          ))}
          <text x={0} y={-2} fill="#5a5854" fontSize="9" fontFamily="monospace">residual</text>
        </g>
      </svg>
      <p className="ags-note">
        The residual falls and then <strong>stops above zero</strong>, at the
        floor β. No amount of running closes it. That irreducible gap is the
        desk’s private edge — the reason it has a business at all.
      </p>
    </div>
  );
}

function SocietyBadge({ society }) {
  return (
    <div className="ags-society">
      <div className="ags-metrics">
        <Metric k="society χ" v={society.chi} />
        <Metric k="couple" v={society.couple ?? "—"} />
      </div>
      <p className="ags-note">
        The desks share a purpose and a market state, but no internals. The
        society’s own character χ is computed from the ties between them — one
        level up, the same invariant.
      </p>
    </div>
  );
}

// =====================================================================
//  Shared bits
// =====================================================================

function ChartFrame({ title, children }) {
  return (
    <section className="ags-frame">
      <h3 className="ags-frame-title">{title}</h3>
      {children}
    </section>
  );
}

function Metric({ k, v }) {
  return (
    <span className="ags-metric">
      <span className="ags-metric-k">{k}</span>
      <span className="ags-metric-v">{v}</span>
    </span>
  );
}

function Empty({ label }) {
  return <div className="ags-empty">{label}</div>;
}
