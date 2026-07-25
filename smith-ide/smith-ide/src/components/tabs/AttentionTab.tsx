"use client";

import React, { useRef, useEffect } from "react";
import * as d3 from "d3";
import { useStore } from "@/store/useStore";

export function AttentionTab() {
  const data = useStore(s => s.attentionData);
  if (!data) return <Empty label="No attention data." />;

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Attention price p*</span>
        <span className="font-mono text-xs text-accent-amber">{data.result.price.toFixed(4)}</span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Budget used</span>
        <span className="font-mono text-xs text-fg-primary">
          {data.result.budgetUsed.toFixed(4)} / {data.budget}
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-fg-muted">Total gain</span>
        <span className="font-mono text-xs text-fg-primary">{data.result.totalGain.toFixed(4)}</span>
      </div>

      <SectionLabel>Water-Filling Diagram</SectionLabel>
      <WaterFillChart />

      <SectionLabel>Marginal Gain Curves</SectionLabel>
      <MarginalGainChart />

      <SectionLabel>Allocations</SectionLabel>
      <AllocationTable />
    </div>
  );
}

function WaterFillChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.attentionData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 220;
    const margin = { top: 16, right: 16, bottom: 32, left: 44 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const allocs = data.result.allocations;
    const price = data.result.price;

    const x = d3.scaleBand()
      .domain(allocs.map(a => a.scene))
      .range([0, inner.w])
      .padding(0.2);

    const maxMargin = Math.max(...data.profiles.map(p => p.entryMargin)) * 1.1;
    const y = d3.scaleLinear().domain([0, maxMargin]).range([inner.h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Column heights (entry margins)
    g.selectAll("rect.column")
      .data(allocs)
      .join("rect")
      .attr("class", "column")
      .attr("x", d => x(d.scene)!)
      .attr("y", d => {
        const prof = data.profiles.find(p => p.name === d.scene);
        return y(prof?.entryMargin ?? 0);
      })
      .attr("width", x.bandwidth())
      .attr("height", d => {
        const prof = data.profiles.find(p => p.name === d.scene);
        return inner.h - y(prof?.entryMargin ?? 0);
      })
      .attr("fill", "#1a1a24")
      .attr("stroke", "#2a2a36")
      .attr("rx", 3);

    // Filled water (allocation area)
    g.selectAll("rect.water")
      .data(allocs)
      .join("rect")
      .attr("class", "water")
      .attr("x", d => x(d.scene)!)
      .attr("y", () => y(price))
      .attr("width", x.bandwidth())
      .attr("height", d => {
        if (d.allocation <= 0) return 0;
        return inner.h - y(price);
      })
      .attr("fill", d => d.allocation > 0 ? "#5b8dd940" : "transparent")
      .attr("stroke", d => d.allocation > 0 ? "#5b8dd9" : "transparent")
      .attr("rx", 3);

    // Water level line (p*)
    g.append("line")
      .attr("x1", -8).attr("x2", inner.w + 8)
      .attr("y1", y(price)).attr("y2", y(price))
      .attr("stroke", "#d4a849")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3");

    g.append("text")
      .attr("x", inner.w + 4).attr("y", y(price) - 4)
      .attr("fill", "#d4a849").attr("font-size", "9px").attr("text-anchor", "end")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text(`p* = ${price.toFixed(3)}`);

    // Allocation labels
    g.selectAll("text.alloc")
      .data(allocs)
      .join("text")
      .attr("class", "alloc")
      .attr("x", d => x(d.scene)! + x.bandwidth() / 2)
      .attr("y", inner.h + 14)
      .attr("text-anchor", "middle")
      .attr("fill", d => d.allocation > 0 ? "#e8e4dd" : "#5a5854")
      .attr("font-size", "9px")
      .attr("font-family", "'JetBrains Mono', monospace")
      .text(d => d.scene);

    // Y axis
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-inner.w))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.selectAll(".domain").attr("stroke", "#2a2a36");
    g.selectAll("text").attr("fill", "#5a5854").attr("font-size", "9px");

  }, [data]);

  return (
    <div className="bg-bg-surface rounded border border-border-subtle">
      <svg ref={svgRef} className="w-full" style={{ height: 220 }} />
    </div>
  );
}

function MarginalGainChart() {
  const svgRef = useRef<SVGSVGElement>(null);
  const data = useStore(s => s.attentionData);

  useEffect(() => {
    if (!svgRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 180;
    const margin = { top: 12, right: 12, bottom: 24, left: 44 };
    const inner = { w: width - margin.left - margin.right, h: height - margin.top - margin.bottom };
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const maxA = data.budget * 1.5;
    const x = d3.scaleLinear().domain([0, maxA]).range([0, inner.w]);
    const maxGP = Math.max(...data.profiles.map(p => p.entryMargin)) * 1.1;
    const y = d3.scaleLinear().domain([0, maxGP]).range([inner.h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const colors = ["#5b8dd9", "#5fa85f", "#d4a849", "#c94a4a", "#4db8b8"];

    // Curves
    data.profiles.forEach((prof, idx) => {
      const points: [number, number][] = [];
      for (let a = 0; a <= maxA; a += maxA / 100) {
        points.push([a, prof.gammaPrime(a)]);
      }
      const line = d3.line()
        .x(d => x(d[0]))
        .y(d => y(d[1]));

      g.append("path")
        .datum(points)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", colors[idx % colors.length])
        .attr("stroke-width", 1.5);

      // Label
      g.append("text")
        .attr("x", x(maxA) - 4)
        .attr("y", y(prof.gammaPrime(maxA)) - 4)
        .attr("fill", colors[idx % colors.length])
        .attr("font-size", "9px")
        .attr("text-anchor", "end")
        .attr("font-family", "'JetBrains Mono', monospace")
        .text(prof.name);
    });

    // p* horizontal
    g.append("line")
      .attr("x1", 0).attr("x2", inner.w)
      .attr("y1", y(data.result.price)).attr("y2", y(data.result.price))
      .attr("stroke", "#d4a849")
      .attr("stroke-dasharray", "4,3")
      .attr("stroke-width", 1);

    // Axes
    g.append("g").attr("transform", `translate(0,${inner.h})`)
      .call(d3.axisBottom(x).ticks(5).tickSize(-inner.h))
      .selectAll("line").attr("stroke", "#1a1a24");
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickSize(-inner.w))
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

function AllocationTable() {
  const data = useStore(s => s.attentionData);
  if (!data) return null;

  return (
    <div className="bg-bg-surface rounded border border-border-subtle overflow-hidden">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-border-subtle text-fg-muted text-[10px]">
            <th className="text-left p-2">Scene</th>
            <th className="text-right p-2">a*</th>
            <th className="text-right p-2">γ&apos;(0)</th>
            <th className="text-right p-2">γ&apos;(a*)</th>
            <th className="text-right p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.result.allocations.map(alloc => {
            const prof = data.profiles.find(p => p.name === alloc.scene);
            const active = alloc.allocation > 0;
            return (
              <tr key={alloc.scene} className={`border-b border-border-subtle ${active ? "" : "opacity-40"}`}>
                <td className="p-2 text-fg-primary">{alloc.scene}</td>
                <td className="p-2 text-right text-accent-blue">{alloc.allocation.toFixed(4)}</td>
                <td className="p-2 text-right text-fg-secondary">{prof?.entryMargin.toFixed(4) ?? "—"}</td>
                <td className="p-2 text-right text-fg-secondary">{alloc.marginalGain.toFixed(4)}</td>
                <td className="p-2 text-right">
                  <span className={`text-[10px] ${active ? "text-accent-green" : "text-accent-red"}`}>
                    {active ? "active" : "dry"}
                  </span>
                </td>
              </tr>
            );
          })}
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
