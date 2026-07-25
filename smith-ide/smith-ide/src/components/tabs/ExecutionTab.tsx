"use client";

import React, { useRef, useEffect } from "react";
import * as d3 from "d3";
import { useStore } from "@/store/useStore";

export function ExecutionTab() {
  const data = useStore(s => s.executionData);
  if (!data || data.steps.length === 0) return <Empty label="No execution data. Run a valid script." />;

  return (
    <div className="space-y-4">
      <SectionLabel>Phase Timeline</SectionLabel>
      <PhaseTimeline />

      <SectionLabel>Committed Count</SectionLabel>
      <CommittedCountChart />

      <SectionLabel>Outcome Log</SectionLabel>
      <OutcomeLog />
    </div>
  );
}

function PhaseTimeline() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.executionData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 120;
    const margin = { top: 12, right: 12, bottom: 24, left: 80 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    // Get unique agents
    const agents = [...new Set(data.steps.map(s => s.agent))];
    const maxTick = d3.max(data.steps, s => s.tick) ?? 30;

    const x = d3.scaleLinear().domain([0, maxTick]).range([0, inner.w]);
    const y = d3.scaleBand().domain(agents).range([0, inner.h]).padding(0.3);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Phase blocks
    g.selectAll("rect")
      .data(data.steps)
      .join("rect")
      .attr("x", d => x(d.tick - 0.4))
      .attr("y", d => y(d.agent)!)
      .attr("width", x(1) - x(0) - 1)
      .attr("height", y.bandwidth())
      .attr("fill", d => d.phase === "construction" ? "#2a4a6a" : "#6a4a2a")
      .attr("rx", 1)
      .attr("opacity", d => d.outcome === "quiescent" ? 0.3 : 0.8);

    // Agent labels
    g.selectAll("text.agent")
      .data(agents)
      .join("text")
      .attr("class", "agent")
      .attr("x", -4)
      .attr("y", d => y(d)! + y.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", "#9a9690")
      .attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text(d => d);

    // X axis
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).ticks(10).tickSize(-inner.h))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

    // Legend
    const legend = svg.append("g").attr("transform", `translate(${margin.left},${height - 8})`);
    legend.append("rect").attr("x", 0).attr("y", -6).attr("width", 8).attr("height", 8).attr("fill", "#2a4a6a").attr("rx", 1);
    legend.append("text").attr("x", 12).attr("y", 0).attr("fill", "#5a5854").attr("font-size", "8px").text("construction");
    legend.append("rect").attr("x", 90).attr("y", -6).attr("width", 8).attr("height", 8).attr("fill", "#6a4a2a").attr("rx", 1);
    legend.append("text").attr("x", 102).attr("y", 0).attr("fill", "#5a5854").attr("font-size", "8px").text("commitment");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 120 }} />
    </div>
  );
}

function CommittedCountChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.executionData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 160;
    const margin = { top: 12, right: 12, bottom: 24, left: 44 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    // Get first agent's steps
    const agents = [...new Set(data.steps.map(s => s.agent))];
    const colors = ["#5b8dd9", "#5fa85f", "#d4a849", "#c94a4a"];

    const maxTick = d3.max(data.steps, s => s.tick) ?? 30;
    const maxCount = d3.max(data.steps, s => s.count) ?? 10;

    const x = d3.scaleLinear().domain([0, maxTick]).range([0, inner.w]);
    const y = d3.scaleLinear().domain([0, maxCount * 1.1]).range([inner.h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Staircase per agent
    agents.forEach((agent, idx) => {
      const agentSteps = data.steps.filter(s => s.agent === agent);
      const line = d3.line<typeof agentSteps[0]>()
        .x(d => x(d.tick))
        .y(d => y(d.count))
        .curve(d3.curveStepAfter);

      g.append("path")
        .datum(agentSteps)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", colors[idx % colors.length])
        .attr("stroke-width", 1.5);
    });

    // Axes
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).ticks(10).tickSize(-inner.h))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-inner.w))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

    // Y label
    g.append("text")
      .attr("x", -margin.left + 10).attr("y", -4)
      .attr("fill", "#5a5854").attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text("count m");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 160 }} />
    </div>
  );
}

function OutcomeLog() {
  const data = useStore(s => s.executionData);
  if (!data) return null;

  const outcomeColor: Record<string, string> = {
    commit: "text-accent-green",
    observe: "text-accent-blue",
    decline: "text-accent-red",
    quiescent: "text-fg-muted",
  };

  return (
    <div className="bg-bg-surface rounded border border-border-subtle overflow-hidden max-h-60 overflow-y-auto">
      <table className="w-full text-[11px] font-mono">
        <thead className="sticky top-0 bg-bg-surface">
          <tr className="border-b border-border-subtle text-fg-muted text-[10px]">
            <th className="text-left p-1.5 w-10">Tick</th>
            <th className="text-left p-1.5">Agent</th>
            <th className="text-left p-1.5">Outcome</th>
            <th className="text-left p-1.5">Scene</th>
            <th className="text-right p-1.5">Residual</th>
            <th className="text-right p-1.5">Δ</th>
            <th className="text-right p-1.5">m</th>
          </tr>
        </thead>
        <tbody>
          {data.steps.map((step, i) => (
            <tr key={i} className="border-b border-border-subtle/50 hover:bg-bg-hover">
              <td className="p-1.5 text-fg-muted">{step.tick}</td>
              <td className="p-1.5 text-fg-secondary">{step.agent}</td>
              <td className={`p-1.5 ${outcomeColor[step.outcome] ?? "text-fg-secondary"}`}>
                {step.outcome}
              </td>
              <td className="p-1.5 text-fg-muted">{step.scene ?? "—"}</td>
              <td className="p-1.5 text-right text-fg-secondary">{step.residual.toFixed(4)}</td>
              <td className="p-1.5 text-right text-fg-muted">{step.delta > 0 ? `-${step.delta.toFixed(4)}` : "—"}</td>
              <td className="p-1.5 text-right text-accent-amber">{step.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
