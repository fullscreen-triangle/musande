"use client";

import React, { useEffect, useCallback, useRef } from "react";
import { useStore } from "@/store/useStore";
import { Explorer } from "./Explorer";
import { Editor } from "./Editor";
import { OutputPanel } from "./OutputPanel";

export function IDE() {
  const explorerWidth = useStore(s => s.explorerWidth);
  const editorWidth = useStore(s => s.editorWidth);
  const setExplorerWidth = useStore(s => s.setExplorerWidth);
  const setEditorWidth = useStore(s => s.setEditorWidth);
  const compileAndRun = useStore(s => s.compileAndRun);

  // Compile on mount
  useEffect(() => {
    compileAndRun();
  }, [compileAndRun]);

  return (
    <div className="flex flex-col h-screen">
      {/* Title bar */}
      <TitleBar />

      {/* Main content: three columns */}
      <div className="flex flex-1 min-h-0">
        {/* Explorer */}
        <div style={{ width: explorerWidth, minWidth: 160, maxWidth: 360 }} className="flex-shrink-0">
          <Explorer />
        </div>

        <Resizer onResize={(dx) => setExplorerWidth(Math.max(160, Math.min(360, explorerWidth + dx)))} />

        {/* Editor */}
        <div style={{ width: editorWidth, minWidth: 280, maxWidth: 800 }} className="flex-shrink-0">
          <Editor />
        </div>

        <Resizer onResize={(dx) => setEditorWidth(Math.max(280, Math.min(800, editorWidth + dx)))} />

        {/* Output */}
        <div className="flex-1 min-w-[300px]">
          <OutputPanel />
        </div>
      </div>

      {/* Status bar */}
      <StatusBar />
    </div>
  );
}

function TitleBar() {
  const activeFile = useStore(s => s.activeFile);
  const compiled = useStore(s => s.compiled);
  const ok = compiled?.check.ok;

  return (
    <div className="h-9 bg-bg-panel border-b border-border-subtle flex items-center px-4 gap-3 flex-shrink-0">
      <span className="font-mono text-accent-amber font-semibold text-xs tracking-widest uppercase">
        Smith
      </span>
      <span className="text-fg-muted">—</span>
      <span className="text-fg-secondary font-mono text-xs">{activeFile}</span>
      {compiled && (
        <span className={`ml-auto text-xs font-mono ${ok ? "text-accent-green" : "text-accent-red"}`}>
          {ok ? "✓ OK" : `✗ ${compiled.check.errors.filter(e => e.severity === "error").length} error(s)`}
        </span>
      )}
    </div>
  );
}

function StatusBar() {
  const compiled = useStore(s => s.compiled);
  const runResult = useStore(s => s.runResult);

  const agents = compiled?.check.agents ?? [];
  const steps = runResult?.steps.length ?? 0;

  return (
    <div className="h-6 bg-bg-panel border-t border-border-subtle flex items-center px-4 gap-6 flex-shrink-0">
      <span className="text-fg-muted font-mono text-[11px]">
        {agents.length} agent{agents.length !== 1 ? "s" : ""}
      </span>
      {agents.length > 0 && (
        <span className="text-fg-muted font-mono text-[11px]">
          χ = {agents[0].chi}
        </span>
      )}
      <span className="text-fg-muted font-mono text-[11px]">
        {steps} steps
      </span>
      <span className="ml-auto text-fg-muted font-mono text-[11px]">
        β &gt; 0
      </span>
    </div>
  );
}

function Resizer({ onResize }: { onResize: (dx: number) => void }) {
  const dragging = useRef(false);
  const lastX = useRef(0);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    lastX.current = e.clientX;
    e.preventDefault();

    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const dx = e.clientX - lastX.current;
      lastX.current = e.clientX;
      onResize(dx);
    };

    const onMouseUp = () => {
      dragging.current = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }, [onResize]);

  return <div className="resizer" onMouseDown={onMouseDown} />;
}
