"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { useStore } from "@/store/useStore";

export function SocietyTab() {
  const data = useStore(s => s.societyData);
  if (!data) return <Empty label="No society. Declare a society block to see coordination." />;

  const lastState = data.kuramotoHistory[data.kuramotoHistory.length - 1];

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Order parameter R</span>
        <span className="font-mono text-xs text-accent-amber">{lastState.R.toFixed(5)}</span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Coordination cost C</span>
        <span className="font-mono text-xs text-fg-primary">{lastState.cost.toFixed(5)}</span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Coupling K</span>
        <span className="font-mono text-xs text-fg-primary">{data.coupling}</span>
      </div>

      <SectionLabel>Phase Circle</SectionLabel>
      <PhaseCircle />

      <SectionLabel>Synchronisation Curve (R vs step)</SectionLabel>
      <SyncCurve />

      <SectionLabel>Crowd Sharpening</SectionLabel>
      <CrowdChart />
    </div>
  );
}

function PhaseCircle() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.societyData);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (data) setStep(data.kuramotoHistory.length - 1);
  }, [data]);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const size = Math.min(svgRef.current.clientWidth, 240);
    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 30;
    svg.attr("viewBox", `0 0 ${size} ${size}`);

    const state = data.kuramotoHistory[Math.min(step, data.kuramotoHistory.length - 1)];
    const colors = ["#5b8dd9", "#5fa85f", "#d4a849", "#c94a4a", "#4db8b8", "#d97799", "#7a5fd9"];

    // Circle
    svg.append("circle")
      .attr("cx", cx).attr("cy", cy).attr("r", radius)
      .attr("fill", "none").attr("stroke", "#2a2a36").attr("stroke-width", 1);

    // Crosshair
    svg.append("line").attr("x1", cx - radius).attr("y1", cy).attr("x2", cx + radius).attr("y2", cy)
      .attr("stroke", "#1a1a24").attr("stroke-width", 0.5);
    svg.append("line").attr("x1", cx).attr("y1", cy - radius).attr("x2", cx).attr("y2", cy + radius)
      .attr("stroke", "#1a1a24").attr("stroke-width", 0.5);

    // Mean phase arrow
    const arrowLen = radius * state.R;
    const ax = cx + arrowLen * Math.cos(state.psi);
    const ay = cy - arrowLen * Math.sin(state.psi);
    svg.append("line")
      .attr("x1", cx).attr("y1", cy).attr("x2", ax).attr("y2", ay)
      .attr("stroke", "#d4a849").attr("stroke-width", 2)
      .attr("marker-end", "url(#arrow)");

    // Arrow marker
    svg.append("defs").append("marker")
      .attr("id", "arrow").attr("viewBox", "0 0 10 10")
      .attr("refX", 9).attr("refY", 5)
      .attr("markerWidth", 6).attr("markerHeight", 6)
      .attr("orient", "auto-start-reverse")
      .append("path").attr("d", "M 0 0 L 10 5 L 0 10 z").attr("fill", "#d4a849");

    // Agent dots
    state.phases.forEach((phi, i) => {
      const px = cx + radius * Math.cos(phi);
      const py = cy - radius * Math.sin(phi);
      svg.append("circle")
        .attr("cx", px).attr("cy", py).attr("r", 6)
        .attr("fill", colors[i % colors.length])
        .attr("stroke", "#0a0a0f").attr("stroke-width", 1.5);

      // Name label
      const lx = cx + (radius + 16) * Math.cos(phi);
      const ly = cy - (radius + 16) * Math.sin(phi);
      svg.append("text")
        .attr("x", lx).attr("y", ly)
        .attr("text-anchor", "middle").attr("dy", "0.35em")
        .attr("fill", "#9a9690").attr("font-size", "8px")
        .attr("font-family", "'JetBrains Mono', monospace")
        .text(data.agentNames[i] ?? `${i}`);
    });

    // R label
    svg.append("text")
      .attr("x", cx).attr("y", cy + 10)
      .attr("text-anchor", "middle")
      .attr("fill", "#d4a849").attr("font-size", "10px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text(`R = ${state.R.toFixed(3)}`);

  }, [data, step]);

  if (!data) return null;

  return (
    <div className="bg-bg-surface rounded border border-border-subtle p-2">
      <svg ref={svgRef} className="w-full" style={{ height: 240 }} />
      <input
        type="range"
        min={0}
        max={data.kuramotoHistory.length - 1}
        value={step}
        onChange={e => setStep(parseInt(e.target.value))}
        className="w-full mt-2 accent-accent-amber"
      />
      <div className="text-center text-[10px] font-mono text-fg-muted">
        Step {step} / {data.kuramotoHistory.length - 1}
      </div>
    </div>
  );
}

function SyncCurve() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.societyData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 160;
    const margin = { top: 12, right: 12, bottom: 24, left: 44 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const history = data.kuramotoHistory;

    const x = d3.scaleLinear().domain([0, history.length - 1]).range([0, inner.w]);
    const y = d3.scaleLinear().domain([0, 1]).range([inner.h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // R curve
    const rLine = d3.line<typeof history[0]>()
      .x((_, i) => x(i))
      .y(d => y(d.R));

    g.append("path")
      .datum(history)
      .attr("d", rLine)
      .attr("fill", "none")
      .attr("stroke", "#d4a849")
      .attr("stroke-width", 2);

    // Cost curve (1 - R)
    const cLine = d3.line<typeof history[0]>()
      .x((_, i) => x(i))
      .y(d => y(d.cost));

    g.append("path")
      .datum(history)
      .attr("d", cLine)
      .attr("fill", "none")
      .attr("stroke", "#c94a4a")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "4,2");

    // R = 1 line
    g.append("line")
      .attr("x1", 0).attr("x2", inner.w)
      .attr("y1", y(1)).attr("y2", y(1))
      .attr("stroke", "#2a2a36").attr("stroke-dasharray", "2,4");

    // Labels
    g.append("text").attr("x", inner.w - 4).attr("y", y(history[history.length - 1].R) - 6)
      .attr("text-anchor", "end").attr("fill", "#d4a849").attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace").text("R");
    g.append("text").attr("x", inner.w - 4).attr("y", y(history[history.length - 1].cost) + 12)
      .attr("text-anchor", "end").attr("fill", "#c94a4a").attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace").text("C = 1−R");

    // Axes
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).ticks(8).tickSize(-inner.h))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-inner.w))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 160 }} />
    </div>
  );
}

function CrowdChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.societyData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 160;
    const margin = { top: 12, right: 12, bottom: 24, left: 44 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const curve = data.crowdCurve;
    const x = d3.scaleLinear().domain([1, curve.length]).range([0, inner.w]);
    const y = d3.scaleLog().domain([0.001, 1]).range([inner.h, 0]).clamp(true);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Curve
    const line = d3.line<typeof curve[0]>()
      .x(d => x(d.M))
      .y(d => y(Math.max(0.001, d.failure)));

    g.append("path")
      .datum(curve)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "#5fa85f")
      .attr("stroke-width", 2);

    // Dots
    g.selectAll("circle")
      .data(curve)
      .join("circle")
      .attr("cx", d => x(d.M))
      .attr("cy", d => y(Math.max(0.001, d.failure)))
      .attr("r", 3)
      .attr("fill", "#5fa85f");

    // Axes
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).ticks(curve.length).tickFormat(d => String(d)))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.append("g")
      .call(d3.axisLeft(y).ticks(4, ".0e").tickSize(-inner.w))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

    // Labels
    g.append("text").attr("x", inner.w / 2).attr("y", inner.h + 20)
      .attr("text-anchor", "middle").attr("fill", "#5a5854").attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace").text("Crowd size M");
    g.append("text").attr("x", -margin.left + 8).attr("y", -4)
      .attr("fill", "#5a5854").attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace").text("∏ qᵢ");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 160 }} />
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] font-semibold text-fg-muted uppercase tracking-wider mt-4 mb-1 border-t border-border-subtle pt-3">
      {children}
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-32 text-fg-muted text-xs font-mono">
      {label}
    </div>
  );
}
