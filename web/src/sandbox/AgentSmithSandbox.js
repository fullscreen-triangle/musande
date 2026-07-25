// =====================================================================
//  Agent Smith Sandbox — the shell.
//
//  A single VS-Code-style component: an explorer of example scripts on the
//  left, an editor in the middle, a run/output pane on the right. It exists
//  to dissolve the AND-gate the other tool imposes — that page demands BOTH
//  the theory AND the syntax AND a model key before anything happens. Here:
//
//    - the scripts are pre-written economic stories (a trading desk), so no
//      syntax knowledge is needed to press Run;
//    - the engine runs OFFLINE and deterministic (runner uses useModel:false),
//      so no API key is needed;
//    - the charts show the framework quantities as a by-product, so the theory
//      is met as the ANSWER to a question the story already asked.
//
//  The one non-obvious wire: the editor's gutter highlights the lines the
//  current brush selection touches (store.highlightLines). Brush a slice of
//  output → the code that produced it lights up. That is the whole point.
// =====================================================================

import React, { useEffect, useRef, useState, useCallback } from "react";
import { SCRIPTS } from "./scripts";
import { useSandbox } from "./store";
import { compileAndRun } from "./runner";
import SandboxCharts from "./SandboxCharts";

const DEBOUNCE_MS = 500;

export default function AgentSmithSandbox() {
  const source = useSandbox((s) => s.source);
  const setSource = useSandbox((s) => s.setSource);
  const setArtifacts = useSandbox((s) => s.setArtifacts);
  const setRunning = useSandbox((s) => s.setRunning);
  const running = useSandbox((s) => s.running);
  const build = useSandbox((s) => s.build);
  const logLines = useSandbox((s) => s.logLines);
  const highlightLines = useSandbox((s) => s.highlightLines);
  const hasSelection = useSandbox((s) => s.hasSelection);
  const clearSelection = useSandbox((s) => s.clearSelection);
  const selVersion = useSandbox((s) => s.selVersion);

  const [activeScript, setActiveScript] = useState(SCRIPTS[0].name);
  const [tab, setTab] = useState("charts"); // charts | log
  const debounceRef = useRef(null);

  const run = useCallback(
    async (src) => {
      setRunning(true);
      try {
        const out = await compileAndRun(src);
        setArtifacts(out);
      } finally {
        setRunning(false);
      }
    },
    [setArtifacts, setRunning]
  );

  // load the first script on mount
  useEffect(() => {
    const first = SCRIPTS[0];
    setSource(first.source);
    run(first.source);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // debounced auto-compile-and-run whenever the source changes
  const onEdit = useCallback(
    (value) => {
      setSource(value);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => run(value), DEBOUNCE_MS);
    },
    [setSource, run]
  );

  const openScript = useCallback(
    (name) => {
      const s = SCRIPTS.find((x) => x.name === name);
      if (!s) return;
      setActiveScript(name);
      clearSelection();
      setSource(s.source);
      run(s.source);
    },
    [setSource, run, clearSelection]
  );

  const activeMeta = SCRIPTS.find((s) => s.name === activeScript);
  const highlightSet = new Set(highlightLines);
  void selVersion;

  return (
    <div className="ags-root">
      <SandboxStyles />

      <div className="ags-titlebar">
        <span className="ags-dot ags-dot-r" />
        <span className="ags-dot ags-dot-y" />
        <span className="ags-dot ags-dot-g" />
        <span className="ags-title">agent-smith — sandbox</span>
        <span className="ags-title-sub">
          offline · deterministic · no key required
        </span>
      </div>

      <div className="ags-body">
        {/* EXPLORER */}
        <aside className="ags-explorer">
          <div className="ags-explorer-head">EXAMPLES · the desk, step by step</div>
          {SCRIPTS.map((s) => (
            <button
              key={s.name}
              className={`ags-file ${s.name === activeScript ? "ags-file-active" : ""}`}
              onClick={() => openScript(s.name)}
              title={s.blurb}
            >
              <span className="ags-file-id">{s.id}</span>
              <span className="ags-file-name">{s.title}</span>
            </button>
          ))}
          <div className="ags-explorer-note">
            Every file is a real script in the economic “skin”. Press a chart
            slice and the code that made it lights up.
          </div>
        </aside>

        {/* EDITOR */}
        <main className="ags-editor-pane">
          <div className="ags-tabbar">
            <span className="ags-doc-tab">{activeScript}</span>
            <span className="ags-blurb">{activeMeta?.blurb}</span>
            {running && <span className="ags-running">running…</span>}
          </div>
          <Editor value={source} onChange={onEdit} highlightSet={highlightSet} />
          <BuildStatus build={build} />
        </main>

        {/* OUTPUT */}
        <section className="ags-output-pane">
          <div className="ags-tabbar ags-output-tabs">
            <button
              className={`ags-tab ${tab === "charts" ? "ags-tab-active" : ""}`}
              onClick={() => setTab("charts")}
            >
              charts
            </button>
            <button
              className={`ags-tab ${tab === "log" ? "ags-tab-active" : ""}`}
              onClick={() => setTab("log")}
            >
              log
            </button>
            <span className="ags-spacer" />
            {hasSelection() && (
              <button className="ags-clear" onClick={clearSelection}>
                clear selection ✕
              </button>
            )}
          </div>
          <div className="ags-output-scroll">
            {tab === "charts" ? <SandboxCharts /> : <LogView logLines={logLines} />}
          </div>
        </section>
      </div>
    </div>
  );
}

// ---- editor: textarea + a synced gutter that highlights brushed lines ----

function Editor({ value, onChange, highlightSet }) {
  const taRef = useRef(null);
  const gutterRef = useRef(null);
  const lines = value.split("\n");

  // keep the gutter scrolled in lockstep with the textarea
  const onScroll = () => {
    if (gutterRef.current && taRef.current) {
      gutterRef.current.scrollTop = taRef.current.scrollTop;
    }
  };

  return (
    <div className="ags-editor">
      <div className="ags-gutter" ref={gutterRef}>
        {lines.map((_, i) => {
          const n = i + 1;
          const hot = highlightSet.has(n);
          return (
            <div key={n} className={`ags-gutter-line ${hot ? "ags-gutter-hot" : ""}`}>
              {n}
            </div>
          );
        })}
      </div>
      <div className="ags-code-wrap">
        {/* highlight underlay: a colored band behind brushed lines */}
        <div className="ags-highlight-underlay" aria-hidden>
          {lines.map((_, i) => (
            <div
              key={i}
              className={`ags-hl-line ${highlightSet.has(i + 1) ? "ags-hl-on" : ""}`}
            />
          ))}
        </div>
        <textarea
          ref={taRef}
          value={value}
          spellCheck={false}
          onChange={(e) => onChange(e.target.value)}
          onScroll={onScroll}
          className="ags-textarea"
        />
      </div>
    </div>
  );
}

function BuildStatus({ build }) {
  if (!build) return <div className="ags-buildbar ags-build-neutral">…</div>;
  if (!build.ok) {
    return (
      <div className="ags-buildbar ags-build-err">
        {(build.errors ?? []).slice(0, 3).map((e, i) => (
          <div key={i}>
            ✗ {e.line ? `line ${e.line}: ` : ""}
            {e.message}
          </div>
        ))}
        {(build.errors ?? []).length > 3 && (
          <div>…and {(build.errors ?? []).length - 3} more</div>
        )}
      </div>
    );
  }
  const agents = build.program?.agents ?? [];
  return (
    <div className="ags-buildbar ags-build-ok">
      ✓ typed OK ·{" "}
      {agents
        .map((a) => `${a.name} (χ=${a.chi}, floor=${a.floor}, ${a.regime})`)
        .join("  ·  ")}
    </div>
  );
}

function LogView({ logLines }) {
  if (!logLines.length) return <div className="ags-empty">No output yet.</div>;
  return (
    <pre className="ags-log">
      {logLines.map((l, i) => (
        <div key={i} className={l.startsWith("✗") ? "ags-log-err" : ""}>
          {l}
        </div>
      ))}
    </pre>
  );
}

// =====================================================================
//  Styles — scoped, injected once. Dark IDE palette, matches the smith-ide
//  reference colours (bg-deep #14141c, surface #1a1a24, accent amber/blue).
// =====================================================================

function SandboxStyles() {
  return (
    <style jsx global>{`
      .ags-root {
        --bg-deep: #14141c;
        --bg-surface: #1a1a24;
        --bg-raised: #22222e;
        --border: #2a2a36;
        --fg: #e8e4dd;
        --fg-muted: #9a9690;
        --fg-dim: #5a5854;
        --amber: #d4a849;
        --blue: #5b8dd9;
        --red: #c94a4a;
        --green: #5fa85f;
        font-family: ui-sans-serif, system-ui, sans-serif;
        color: var(--fg);
        background: var(--bg-deep);
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 82vh;
        min-height: 620px;
      }
      .ags-titlebar {
        display: flex;
        align-items: center;
        gap: 7px;
        padding: 8px 14px;
        background: var(--bg-surface);
        border-bottom: 1px solid var(--border);
        font-size: 12px;
      }
      .ags-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
      .ags-dot-r { background: #ec6a5e; }
      .ags-dot-y { background: #f4bf4f; }
      .ags-dot-g { background: #61c554; }
      .ags-title { margin-left: 8px; font-weight: 600; color: var(--fg-muted); }
      .ags-title-sub { margin-left: auto; color: var(--fg-dim); font-family: monospace; font-size: 11px; }

      .ags-body { display: grid; grid-template-columns: 210px 1fr 1fr; flex: 1; min-height: 0; }

      /* explorer */
      .ags-explorer {
        background: var(--bg-surface);
        border-right: 1px solid var(--border);
        display: flex; flex-direction: column;
        overflow-y: auto;
      }
      .ags-explorer-head {
        padding: 10px 12px 6px;
        font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
        color: var(--fg-dim);
      }
      .ags-file {
        display: flex; align-items: baseline; gap: 8px;
        text-align: left; width: 100%;
        padding: 7px 12px; border: none; background: none; cursor: pointer;
        color: var(--fg-muted); font-size: 13px;
        border-left: 2px solid transparent;
      }
      .ags-file:hover { background: var(--bg-raised); color: var(--fg); }
      .ags-file-active { background: var(--bg-raised); color: var(--fg); border-left-color: var(--amber); }
      .ags-file-id { font-family: monospace; font-size: 10px; color: var(--fg-dim); }
      .ags-explorer-note {
        margin-top: auto; padding: 12px; font-size: 11px; line-height: 1.5;
        color: var(--fg-dim); border-top: 1px solid var(--border);
      }

      /* editor */
      .ags-editor-pane, .ags-output-pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
      .ags-editor-pane { border-right: 1px solid var(--border); }
      .ags-tabbar {
        display: flex; align-items: center; gap: 12px;
        padding: 7px 12px; background: var(--bg-surface);
        border-bottom: 1px solid var(--border); font-size: 12px; min-height: 34px;
      }
      .ags-doc-tab { font-family: monospace; color: var(--fg); }
      .ags-blurb { color: var(--fg-dim); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .ags-running { margin-left: auto; color: var(--amber); font-family: monospace; font-size: 11px; }

      .ags-editor { position: relative; display: flex; flex: 1; min-height: 0; background: var(--bg-deep); }
      .ags-gutter {
        overflow: hidden; padding: 12px 0; text-align: right;
        color: var(--fg-dim); font-family: monospace; font-size: 12px; line-height: 1.55;
        user-select: none; width: 42px; flex-shrink: 0; background: var(--bg-surface);
      }
      .ags-gutter-line { padding: 0 8px; }
      .ags-gutter-hot { color: var(--amber); font-weight: 700; background: #d4a84922; }

      .ags-code-wrap { position: relative; flex: 1; min-width: 0; }
      .ags-highlight-underlay {
        position: absolute; inset: 0; padding: 12px 0; margin: 0;
        pointer-events: none; font-size: 12px; line-height: 1.55;
      }
      .ags-hl-line { height: calc(1.55em); }
      .ags-hl-on { background: #d4a8491e; box-shadow: inset 2px 0 0 var(--amber); }
      .ags-textarea {
        position: relative; z-index: 1;
        width: 100%; height: 100%; resize: none; border: none; outline: none;
        background: transparent; color: var(--fg);
        font-family: monospace; font-size: 12px; line-height: 1.55;
        padding: 12px 14px; caret-color: var(--amber);
      }

      .ags-buildbar { padding: 6px 12px; font-family: monospace; font-size: 11px; border-top: 1px solid var(--border); }
      .ags-build-ok { color: var(--green); background: #5fa85f14; }
      .ags-build-err { color: var(--red); background: #c94a4a14; }
      .ags-build-neutral { color: var(--fg-dim); }

      /* output */
      .ags-output-tabs { gap: 4px; }
      .ags-tab {
        border: none; background: none; cursor: pointer;
        color: var(--fg-dim); font-size: 12px; padding: 3px 10px; border-radius: 5px;
      }
      .ags-tab:hover { color: var(--fg); }
      .ags-tab-active { color: var(--fg); background: var(--bg-raised); }
      .ags-spacer { flex: 1; }
      .ags-clear {
        border: 1px solid var(--border); background: var(--bg-raised); cursor: pointer;
        color: var(--amber); font-size: 11px; font-family: monospace;
        padding: 2px 8px; border-radius: 5px;
      }
      .ags-output-scroll { flex: 1; overflow-y: auto; padding: 12px; min-height: 0; }

      .ags-grid { display: flex; flex-direction: column; gap: 14px; }
      .ags-frame { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
      .ags-frame-title { margin: 0 0 8px; font-size: 12px; font-weight: 600; color: var(--fg-muted); }
      .ags-svg { width: 100%; display: block; }
      .ags-metrics { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 8px; }
      .ags-metric { display: inline-flex; gap: 6px; align-items: baseline; }
      .ags-metric-k { font-size: 10px; color: var(--fg-dim); text-transform: uppercase; letter-spacing: .05em; }
      .ags-metric-v { font-family: monospace; font-size: 13px; color: var(--amber); }
      .ags-note { margin: 8px 0 0; font-size: 11px; line-height: 1.55; color: var(--fg-muted); }
      .ags-empty { color: var(--fg-dim); font-size: 12px; font-family: monospace; padding: 24px; text-align: center; }
      .ags-society { }

      .ags-log { margin: 0; font-family: monospace; font-size: 11px; line-height: 1.6; color: var(--fg-muted); white-space: pre-wrap; }
      .ags-log-err { color: var(--red); }

      @media (max-width: 900px) {
        .ags-body { grid-template-columns: 1fr; grid-template-rows: auto auto auto; }
        .ags-root { height: auto; }
        .ags-editor { min-height: 320px; }
      }
    `}</style>
  );
}
