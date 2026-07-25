"use client";

import React, { useState } from "react";
import { useStore } from "@/store/useStore";

export function Explorer() {
  const files = useStore(s => s.files);
  const activeFile = useStore(s => s.activeFile);
  const setActiveFile = useStore(s => s.setActiveFile);
  const addFile = useStore(s => s.addFile);
  const [showNewInput, setShowNewInput] = useState(false);
  const [newFileName, setNewFileName] = useState("");

  const tutorialFiles = files.filter(f => f.isTutorial);
  const userFiles = files.filter(f => !f.isTutorial);

  const handleNewFile = () => {
    if (newFileName.trim()) {
      const name = newFileName.endsWith(".smith") ? newFileName : `${newFileName}.smith`;
      addFile(name, `// ${name}\n\nagent my_agent {\n  purpose minimise residual\n  scenes {\n    scene work serves residual with work_hook\n  }\n  self {\n    parts { a, b }\n    separations { (a, b: 2) }\n  }\n  budget 1.0\n  floor  2.0\n}\n`);
      setNewFileName("");
      setShowNewInput(false);
    }
  };

  return (
    <div className="h-full bg-bg-panel border-r border-border-subtle flex flex-col">
      {/* Header */}
      <div className="h-9 flex items-center justify-between px-3 border-b border-border-subtle flex-shrink-0">
        <span className="text-[11px] font-semibold text-fg-secondary uppercase tracking-wider">
          Explorer
        </span>
        <button
          onClick={() => setShowNewInput(!showNewInput)}
          className="text-fg-muted hover:text-fg-primary text-sm leading-none px-1"
          title="New file"
        >
          +
        </button>
      </div>

      {/* New file input */}
      {showNewInput && (
        <div className="px-2 py-1.5 border-b border-border-subtle">
          <input
            type="text"
            value={newFileName}
            onChange={e => setNewFileName(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") handleNewFile(); if (e.key === "Escape") setShowNewInput(false); }}
            placeholder="filename.smith"
            autoFocus
            className="w-full bg-bg-surface border border-border-active rounded px-2 py-1 text-xs font-mono text-fg-primary outline-none focus:border-accent-amber"
          />
        </div>
      )}

      {/* File tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {/* Tutorials section */}
        <SectionHeader label="Tutorials" count={tutorialFiles.length} />
        {tutorialFiles.map(f => (
          <FileItem
            key={f.name}
            name={f.name}
            active={f.name === activeFile}
            onClick={() => setActiveFile(f.name)}
          />
        ))}

        {/* User files */}
        {userFiles.length > 0 && (
          <>
            <SectionHeader label="My Scripts" count={userFiles.length} />
            {userFiles.map(f => (
              <FileItem
                key={f.name}
                name={f.name}
                active={f.name === activeFile}
                onClick={() => setActiveFile(f.name)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function SectionHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 mt-1">
      <span className="text-[10px] font-semibold text-fg-muted uppercase tracking-wider">
        {label}
      </span>
      <span className="text-[10px] text-fg-muted">({count})</span>
    </div>
  );
}

function FileItem({ name, active, onClick }: { name: string; active: boolean; onClick: () => void }) {
  // Extract tutorial number for display
  const num = name.match(/^(\d+)/)?.[1];

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-1 flex items-center gap-2 text-xs font-mono transition-colors ${
        active
          ? "bg-bg-surface text-accent-amber border-l-2 border-accent-amber"
          : "text-fg-secondary hover:bg-bg-hover hover:text-fg-primary border-l-2 border-transparent"
      }`}
    >
      {num && (
        <span className={`text-[10px] w-4 text-right ${active ? "text-accent-amber" : "text-fg-muted"}`}>
          {num}
        </span>
      )}
      <span className="truncate">{name.replace(/^\d+-/, "")}</span>
    </button>
  );
}
