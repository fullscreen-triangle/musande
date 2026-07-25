"use client";

import React from "react";
import { useStore, type OutputTab } from "@/store/useStore";
import { StructureTab } from "./tabs/StructureTab";
import { AttentionTab } from "./tabs/AttentionTab";
import { ExecutionTab } from "./tabs/ExecutionTab";
import { SocietyTab } from "./tabs/SocietyTab";
import { ConsoleTab } from "./tabs/ConsoleTab";

const TABS: { id: OutputTab; label: string; shortLabel: string }[] = [
  { id: "structure", label: "Structure", shortLabel: "χ" },
  { id: "attention", label: "Attention", shortLabel: "α" },
  { id: "execution", label: "Execution", shortLabel: "▶" },
  { id: "society", label: "Society", shortLabel: "Σ" },
  { id: "console", label: "Console", shortLabel: ">" },
];

export function OutputPanel() {
  const activeTab = useStore(s => s.activeTab);
  const setActiveTab = useStore(s => s.setActiveTab);
  const compiled = useStore(s => s.compiled);
  const societyData = useStore(s => s.societyData);

  return (
    <div className="h-full flex flex-col bg-bg-deep">
      {/* Tab bar */}
      <div className="h-9 flex items-center border-b border-border-subtle flex-shrink-0 bg-bg-panel">
        {TABS.map(tab => {
          const isActive = tab.id === activeTab;
          const hasSociety = tab.id === "society" && !societyData;
          const hasData = compiled?.check.ok || tab.id === "console";

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              disabled={tab.id !== "console" && !hasData}
              className={`h-full px-3 flex items-center gap-1.5 text-xs font-mono transition-colors border-b-2 ${
                isActive
                  ? "border-accent-amber text-accent-amber bg-bg-deep"
                  : hasData
                    ? "border-transparent text-fg-secondary hover:text-fg-primary hover:bg-bg-hover"
                    : "border-transparent text-fg-muted cursor-not-allowed"
              } ${hasSociety ? "opacity-40" : ""}`}
            >
              <span className={`text-[10px] ${isActive ? "text-accent-amber" : "text-fg-muted"}`}>
                {tab.shortLabel}
              </span>
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        {activeTab === "structure" && <StructureTab />}
        {activeTab === "attention" && <AttentionTab />}
        {activeTab === "execution" && <ExecutionTab />}
        {activeTab === "society" && <SocietyTab />}
        {activeTab === "console" && <ConsoleTab />}
      </div>
    </div>
  );
}
