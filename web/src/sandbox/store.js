// =====================================================================
//  Agent Smith Sandbox — the crossfilter store + source-line index.
//
//  This is the piece the earlier UI sketch faked with a blind string
//  replace. Here it is real. Two jobs:
//
//   1. CROSSFILTER. A run produces a flat table of per-agent-per-tick
//      records. Every chart reads the SAME table through a shared brush
//      selection over four dimensions: agent, scene, outcome, tick-range.
//      Brushing one chart narrows the selection; every other chart and the
//      log re-render against the filtered slice. No chart owns the data.
//
//   2. BRUSH → CODE. The selection also carries the scenes / agents it
//      touches. A source-line index (built by scanning the DSL text) maps
//      each scene, agent and part to the line that declares it. So brushing
//      "all the ticks where the hedger committed on `offset`" doesn't just
//      filter the charts — it highlights the exact `scene offset ...` line in
//      the editor. That is the whole teaching move: see an output slice, see
//      the code that produced it, at once.
// =====================================================================

import { create } from "zustand";

// ---- source-line index ----------------------------------------------
//
// Scan a .smith source and record, for each named entity, the 1-based line
// it is declared on. Cheap, tolerant, regex-based — the DSL is line-oriented
// (`agent NAME {`, `scene NAME serves ...`, part names inside `parts { ... }`).

export function buildSourceIndex(source) {
  const lines = source.split("\n");
  const agents = {}; // name -> line
  const scenes = {}; // name -> { line, agent }
  const parts = {}; // name -> line
  const targets = {}; // purpose target -> line (first mention)

  let currentAgent = null;

  lines.forEach((raw, i) => {
    const line = i + 1;
    const text = raw.replace(/\/\/.*$/, ""); // strip line comments

    const mAgent = text.match(/\bagent\s+([A-Za-z_]\w*)/);
    if (mAgent) {
      currentAgent = mAgent[1];
      agents[currentAgent] = line;
    }

    // society header also opens a naming scope for its target lines
    const mScene = text.match(/\bscene\s+([A-Za-z_]\w*)\s+serves\s+([A-Za-z_]\w*)/);
    if (mScene) {
      scenes[mScene[1]] = { line, agent: currentAgent };
      if (!(mScene[2] in targets)) targets[mScene[2]] = line;
    }

    const mPurpose = text.match(/\bpurpose\s+(?:minimise|minimize|reach)\s+([A-Za-z_]\w*)/);
    if (mPurpose && !(mPurpose[1] in targets)) targets[mPurpose[1]] = line;

    // parts { a, b, c } — possibly on one line
    const mParts = text.match(/\bparts\s*\{([^}]*)\}/);
    if (mParts) {
      for (const p of mParts[1].split(",")) {
        const name = p.trim();
        if (name) parts[name] = line;
      }
    }
  });

  return { agents, scenes, parts, targets, lineCount: lines.length };
}

/** Which source lines does a selection touch? → sorted unique line numbers. */
export function linesForSelection(index, sel) {
  if (!index) return [];
  const set = new Set();
  for (const s of sel.scenes) {
    const hit = index.scenes[s];
    if (hit) set.add(hit.line);
  }
  for (const a of sel.agents) {
    if (index.agents[a]) set.add(index.agents[a]);
  }
  return [...set].sort((x, y) => x - y);
}

// ---- crossfilter predicate ------------------------------------------

const EMPTY_SEL = {
  agents: new Set(), // empty set = no constraint on this dimension
  scenes: new Set(),
  outcomes: new Set(),
  tickRange: null, // [lo, hi] inclusive, or null
};

function passes(rec, sel) {
  if (sel.agents.size && !sel.agents.has(rec.agent)) return false;
  if (sel.scenes.size && !sel.scenes.has(rec.scene)) return false;
  if (sel.outcomes.size && !sel.outcomes.has(rec.outcome)) return false;
  if (sel.tickRange) {
    const [lo, hi] = sel.tickRange;
    if (rec.tick < lo || rec.tick > hi) return false;
  }
  return true;
}

// ---- the store -------------------------------------------------------

export const useSandbox = create((set, get) => ({
  // source + compile/run artefacts
  source: "",
  index: null, // source-line index
  build: null, // { ok, program, errors }
  society: null, // { chi, side, couple } | null
  records: [], // flat table: one row per agent per tick
  structure: null, // { chi, side, floor, declaredFloor, graph, allPartitions }
  attention: null, // { profiles, allocations, price, budget }
  logLines: [], // console text
  running: false,

  // crossfilter selection + a version tick so charts can re-key
  sel: EMPTY_SEL,
  selVersion: 0,

  // active source-line highlight (driven by the selection)
  highlightLines: [],

  setSource: (source) => set({ source, index: buildSourceIndex(source) }),

  setArtifacts: ({ build, records, structure, attention, society, logLines }) =>
    set({
      build,
      records: records ?? [],
      structure: structure ?? null,
      attention: attention ?? null,
      society: society ?? null,
      logLines: logLines ?? [],
      // clear any stale brush on a fresh run
      sel: EMPTY_SEL,
      selVersion: get().selVersion + 1,
      highlightLines: [],
    }),

  setRunning: (running) => set({ running }),

  // --- crossfilter actions. Each toggles/sets one dimension and recomputes
  //     the derived code highlight. Charts subscribe to `sel`/`selVersion`.

  toggleDim: (dim, value) => {
    const sel = get().sel;
    const next = new Set(sel[dim]);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    const merged = { ...sel, [dim]: next };
    set({
      sel: merged,
      selVersion: get().selVersion + 1,
      highlightLines: linesForSelection(get().index, merged),
    });
  },

  setTickRange: (range) => {
    const merged = { ...get().sel, tickRange: range };
    set({
      sel: merged,
      selVersion: get().selVersion + 1,
      highlightLines: linesForSelection(get().index, merged),
    });
  },

  // set the whole selection at once (used by brush gestures that select a
  // rectangle of agent × tick, which implies both an agent set and a range)
  setSelection: (partial) => {
    const merged = { ...get().sel, ...partial };
    set({
      sel: merged,
      selVersion: get().selVersion + 1,
      highlightLines: linesForSelection(get().index, merged),
    });
  },

  clearSelection: () =>
    set({
      sel: EMPTY_SEL,
      selVersion: get().selVersion + 1,
      highlightLines: [],
    }),

  // derived: the filtered record slice (charts that respect the brush use
  // this; the chart that OWNS a brush dimension reads the full table so it
  // can still show the unselected context greyed out).
  filtered: () => get().records.filter((r) => passes(r, get().sel)),
  isSelected: (rec) => passes(rec, get().sel),
  hasSelection: () => {
    const s = get().sel;
    return !!(s.agents.size || s.scenes.size || s.outcomes.size || s.tickRange);
  },
}));
