"use client";

import React from "react";
import { useStore } from "@/store/useStore";

export function ConsoleTab() {
  const consoleLog = useStore(s => s.consoleLog);
  const compiled = useStore(s => s.compiled);

  return (
    <div className="space-y-3">
      {/* Invariant summary */}
      {compiled?.check.ok && compiled.check.agents.length > 0 && (
        <div className="bg-bg-surface rounded border border-border-subtle overflow-hidden">
          <div className="px-3 py-1.5 border-b border-border-subtle">
            <span className="text-[10px] font-semibold text-fg-muted uppercase tracking-wider">
              Invariant Summary
            </span>
          </div>
          <table className="w-full text-[11px] font-mono">
            <thead>
              <tr className="border-b border-border-subtle text-fg-muted text-[10px]">
                <th className="text-left p-2">Agent</th>
                <th className="text-left p-2">Regime</th>
                <th className="text-right p-2">χ</th>
                <th className="text-right p-2">Floor</th>
                <th className="text-right p-2">Non-local</th>
              </tr>
            </thead>
            <tbody>
              {compiled.check.agents.map(ac => (
                <tr key={ac.name} className="border-b border-border-subtle/50">
                  <td className="p-2 text-accent-amber">{ac.name}</td>
                  <td className="p-2 text-fg-secondary">{ac.regime}</td>
                  <td className="p-2 text-right text-accent-blue">{ac.chi}</td>
                  <td className="p-2 text-right text-fg-primary">{ac.floor}</td>
                  <td className="p-2 text-right">
                    <span className={ac.nonLocal ? "text-accent-green" : "text-accent-red"}>
                      {ac.nonLocal ? "yes" : "no"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Console log */}
      <div className="bg-bg-surface rounded border border-border-subtle">
        <div className="px-3 py-1.5 border-b border-border-subtle flex items-center justify-between">
          <span className="text-[10px] font-semibold text-fg-muted uppercase tracking-wider">
            Output
          </span>
          <span className="text-[10px] text-fg-muted font-mono">{consoleLog.length} lines</span>
        </div>
        <div className="p-3 max-h-[400px] overflow-y-auto">
          {consoleLog.length === 0 ? (
            <span className="text-fg-muted text-xs font-mono">No output yet. Edit a script to compile.</span>
          ) : (
            consoleLog.map((line, i) => (
              <div key={i} className="font-mono text-[11px] leading-relaxed">
                {line.startsWith("✓") ? (
                  <span className="text-accent-green">{line}</span>
                ) : line.startsWith("✗") ? (
                  <span className="text-accent-red">{line}</span>
                ) : line.startsWith("  ") ? (
                  <span className="text-fg-secondary">{line}</span>
                ) : (
                  <span className="text-fg-muted">{line}</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Four invariants */}
      <div className="bg-bg-surface rounded border border-border-subtle p-3">
        <div className="text-[10px] font-semibold text-fg-muted uppercase tracking-wider mb-2">
          Implementation Invariants
        </div>
        <div className="space-y-1.5">
          <InvariantRow
            label="Conserved identity (χ)"
            ok={!!compiled?.check.ok}
            detail="Graph invariant under relabelling"
          />
          <InvariantRow
            label="Never-resetting count (m)"
            ok={!!compiled?.check.ok}
            detail="Monotone counter, persisted across sessions"
          />
          <InvariantRow
            label="Search-not-fetch"
            ok={!!compiled?.check.ok}
            detail="Every answer commits ≥1 act"
          />
          <InvariantRow
            label="Exclusive phases"
            ok={!!compiled?.check.ok}
            detail="Construction and commitment disjoint"
          />
        </div>
      </div>
    </div>
  );
}

function InvariantRow({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs ${ok ? "text-accent-green" : "text-fg-muted"}`}>
        {ok ? "●" : "○"}
      </span>
      <span className="text-xs text-fg-primary">{label}</span>
      <span className="text-[10px] text-fg-muted ml-auto">{detail}</span>
    </div>
  );
}
