"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef } from "react";

// react-force-graph-3d is WebGL — load client-side only.
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });

// A dark 3d knowledge graph. `data` = { nodes, links }; `flow` = list of
// "src>tgt" link ids to pulse this step. Re-passing data re-runs the force
// simulation, which IS the reshuffle the showcase wants to show.
export default function ForceGraph({ data, flow = [], onNodeClick }) {
  const fgRef = useRef();

  // gently reheat the simulation each time data changes so nodes reshuffle
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3ReheatSimulation?.();
    }
  }, [data]);

  const flowSet = new Set(flow);

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={data}
      backgroundColor="#0a0a0a"
      showNavInfo={false}
      nodeLabel={(n) => `${n.label}${n.content ? ` — ${n.content}` : ""}`}
      nodeColor={(n) => n.color}
      nodeVal={(n) => n.val}
      nodeOpacity={0.9}
      nodeResolution={12}
      linkColor={(l) => linkColor(l, flowSet)}
      linkWidth={(l) => (flowSet.has(linkId(l)) ? 2.2 : l.kind === "sep" ? 0.4 : 0.8)}
      linkOpacity={0.5}
      linkDirectionalParticles={(l) => (flowSet.has(linkId(l)) ? 4 : l.kind === "flow" ? 2 : 0)}
      linkDirectionalParticleWidth={2}
      linkDirectionalParticleSpeed={0.012}
      onNodeClick={onNodeClick}
      cooldownTicks={80}
      warmupTicks={20}
    />
  );
}

function linkId(l) {
  const s = typeof l.source === "object" ? l.source.id : l.source;
  const t = typeof l.target === "object" ? l.target.id : l.target;
  return `${s}>${t}`;
}

function linkColor(l, flowSet) {
  if (flowSet.has(linkId(l))) return "#ffffff";
  switch (l.kind) {
    case "flow":
      return "#ba5a17";
    case "coord":
      return "#1d9e75";
    case "toward":
      return "#555";
    case "sep":
      return "#2a2a2a";
    case "prompt":
      return "#444";
    default:
      return "#333";
  }
}
