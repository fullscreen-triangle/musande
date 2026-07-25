"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { useStore } from "@/store/useStore";

export function StructureTab() {
  const data = useStore(s => s.structureData);
  if (!data) return <Empty label="No structure data. Compile a valid script." />;

  return (
    <div className="space-y-4">
      <Metric label="χ (character invariant)" value={data.chi} />
      <Metric label="Realised floor" value={data.floor} />
      <Metric label="Non-local" value={data.nonLocal ? "yes" : "no"} />
      <Metric
        label="χ partition"
        value={data.chiPartition.blocks.map(b => `{${b.join(", ")}}`).join(" | ")}
      />

      <SectionLabel>Self-Graph</SectionLabel>
      <SelfGraphChart />

      <SectionLabel>Partition Landscape</SectionLabel>
      <PartitionLandscape />

      <SectionLabel>Floor Gauge</SectionLabel>
      <FloorGauge />
    </div>
  );
}

function SelfGraphChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.structureData);
  const patchSource = useStore(s => s.patchSource);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 260;
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const { graph, chiPartition } = data;
    const chiBlockSet = new Set<string>();
    if (chiPartition.blocks.length >= 2) {
      chiPartition.blocks[0].forEach(p => chiBlockSet.add(p));
    }

    // Force layout
    const nodes = graph.parts.map(p => ({
      id: p,
      inBlock0: chiBlockSet.has(p),
    }));
    const links = graph.separations.map(s => ({
      source: s.from,
      target: s.to,
      cost: s.cost,
    }));

    const sim = d3.forceSimulation(nodes as any)
      .force("link", d3.forceLink(links as any).id((d: any) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(24));

    // Links
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#3a3a4a")
      .attr("stroke-width", (d: any) => Math.max(1, d.cost))
      .attr("stroke-opacity", 0.8);

    // Edge cost labels
    const edgeLabel = svg.append("g")
      .selectAll("text")
      .data(links)
      .join("text")
      .attr("fill", "#9a9690")
      .attr("font-size", "10px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .attr("text-anchor", "middle")
      .text((d: any) => d.cost);

    // Chi-cut dashed line (between the two blocks)
    const chiCutEdges = links.filter((l: any) => {
      const sIn = chiBlockSet.has(typeof l.source === "string" ? l.source : l.source.id);
      const tIn = chiBlockSet.has(typeof l.target === "string" ? l.target : l.target.id);
      return sIn !== tIn;
    });

    const cutLine = svg.append("g")
      .selectAll("line.cut")
      .data(chiCutEdges)
      .join("line")
      .attr("stroke", "#d4a849")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3")
      .attr("stroke-opacity", 0.6);

    // Nodes
    const node = svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", 14)
      .attr("fill", (d: any) => d.inBlock0 ? "#1e3a5f" : "#3a1e1e")
      .attr("stroke", (d: any) => d.inBlock0 ? "#5b8dd9" : "#c94a4a")
      .attr("stroke-width", 2)
      .attr("cursor", "grab")
      .call(d3.drag<any, any>()
        .on("start", (e: any, d: any) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (e: any, d: any) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e: any, d: any) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    // Node labels
    const label = svg.append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .attr("fill", "#e8e4dd")
      .attr("font-size", "10px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("pointer-events", "none")
      .text((d: any) => d.id);

    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      cutLine
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      edgeLabel
        .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
        .attr("y", (d: any) => (d.source.y + d.target.y) / 2 - 6);

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y);

      label
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y);
    });

    return () => { sim.stop(); };
  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 260 }} />
    </div>
  );
}

function PartitionLandscape() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.structureData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 180;
    const margin = { top: 12, right: 12, bottom: 24, left: 36 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const partitions = data.allPartitions.slice(0, 20);
    if (partitions.length === 0) return;

    const x = d3.scaleBand()
      .domain(partitions.map((_, i) => String(i)))
      .range([0, inner.w])
      .padding(0.3);

    const y = d3.scaleLinear()
      .domain([0, d3.max(partitions, d => d.cost)! * 1.1])
      .range([inner.h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Bars
    g.selectAll("rect")
      .data(partitions)
      .join("rect")
      .attr("x", (_, i) => x(String(i))!)
      .attr("y", d => y(d.cost))
      .attr("width", x.bandwidth())
      .attr("height", d => inner.h - y(d.cost))
      .attr("fill", (_, i) => i === 0 ? "#d4a849" : "#2a2a36")
      .attr("rx", 2);

    // χ line
    g.append("line")
      .attr("x1", 0).attr("x2", inner.w)
      .attr("y1", y(data.chi)).attr("y2", y(data.chi))
      .attr("stroke", "#c94a4a").attr("stroke-dasharray", "4,3").attr("stroke-width", 1);

    g.append("text")
      .attr("x", inner.w - 2).attr("y", y(data.chi) - 4)
      .attr("fill", "#c94a4a").attr("font-size", "9px").attr("text-anchor", "end")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text(`χ = ${data.chi}`);

    // Axes
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).tickFormat(() => ""))
      .selectAll("line,path").attr("stroke", "#2a2a36");

    g.append("g")
      .call(d3.axisLeft(y).ticks(4).tickSize(-inner.w))
      .selectAll("line").attr("stroke", "#1a1a24");

    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 180 }} />
    </div>
  );
}

function FloorGauge() {
  const data = useStore(s => s.structureData);
  if (!data) return null;

  const maxCost = Math.max(...data.graph.separations.map(s => s.cost), data.declaredFloor * 2);
  const floorPct = (data.declaredFloor / maxCost) * 100;

  return (
    <div className="bg-bg-surface rounded border border-border-subtle p-3">
      <div className="flex items-center justify-between text-[10px] font-mono text-fg-muted mb-1.5">
        <span>0</span>
        <span>β = {data.declaredFloor}</span>
        <span>{maxCost}</span>
      </div>
      <div className="relative h-6 bg-bg-deep rounded overflow-hidden">
        {/* Floor level */}
        <div
          className="absolute top-0 bottom-0 bg-accent-red/20 border-r-2 border-accent-red"
          style={{ width: `${floorPct}%` }}
        />
        {/* Separation markers */}
        {data.graph.separations.map((sep, i) => {
          const pct = (sep.cost / maxCost) * 100;
          const ok = sep.cost >= data.declaredFloor;
          return (
            <div
              key={i}
              className={`absolute top-1 w-2 h-4 rounded-sm ${ok ? "bg-accent-green" : "bg-accent-red"}`}
              style={{ left: `calc(${pct}% - 4px)` }}
              title={`(${sep.from}, ${sep.to}): ${sep.cost}`}
            />
          );
        })}
      </div>
      <div className="flex gap-3 mt-2 text-[10px] font-mono text-fg-muted">
        {data.graph.separations.map((sep, i) => (
          <span key={i} className={sep.cost >= data.declaredFloor ? "text-accent-green" : "text-accent-red"}>
            ({sep.from},{sep.to})={sep.cost}
          </span>
        ))}
      </div>
    </div>
  );
}

// --- Shared components ---

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-baseline justify-between">
      <span className="text-[11px] text-fg-muted">{label}</span>
      <span className="font-mono text-xs text-fg-primary">{value}</span>
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
    <div className="flex items-center justify-center h-full text-fg-muted text-xs font-mono">
      {label}
    </div>
  );
}
