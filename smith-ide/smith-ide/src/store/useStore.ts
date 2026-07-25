import { create } from "zustand";
import { compile, run, agentToGraph } from "../compiler/compiler";
import { tutorials, type TutorialScript } from "../tutorials/scripts";
import {
  type SmithFile, type CheckResult, type AgentDecl,
  type StepRecord, type RunResult, type CompiledProgram,
} from "../compiler/types";
import {
  characterInvariant, allPartitionCosts, realisedFloor,
  waterFill, logGainProfile, orderParameter, kuramotoRun,
  crowdFailureCurve, type WaterFillResult, type WeightedGraph,
  type GainProfile, type Partition, type KuramotoState,
} from "../engine/math";

export type OutputTab = "structure" | "attention" | "execution" | "society" | "console";

export interface FileEntry {
  name: string;
  source: string;
  isTutorial: boolean;
}

// --- Derived data for each tab ---

export interface StructureData {
  graph: WeightedGraph;
  chi: number;
  chiPartition: Partition;
  floor: number;
  declaredFloor: number;
  allPartitions: Partition[];
  nonLocal: boolean;
}

export interface AttentionData {
  profiles: GainProfile[];
  result: WaterFillResult;
  budget: number;
}

export interface ExecutionData {
  steps: StepRecord[];
  finalCounts: Record<string, number>;
}

export interface SocietyData {
  kuramotoHistory: KuramotoState[];
  coupling: number;
  agentNames: string[];
  crowdCurve: { M: number; failure: number }[];
}

export interface IDEStore {
  // --- Files ---
  files: FileEntry[];
  activeFile: string;
  source: string;

  // --- Compilation ---
  compiled: CompiledProgram | null;
  runResult: RunResult | null;
  consoleLog: string[];

  // --- Derived data ---
  structureData: StructureData | null;
  attentionData: AttentionData | null;
  executionData: ExecutionData | null;
  societyData: SocietyData | null;

  // --- UI ---
  activeTab: OutputTab;
  explorerWidth: number;
  editorWidth: number;

  // --- Actions ---
  setActiveFile: (name: string) => void;
  setSource: (source: string) => void;
  setActiveTab: (tab: OutputTab) => void;
  compileAndRun: () => void;
  addFile: (name: string, source: string) => void;
  patchSource: (line: number, oldText: string, newText: string) => void;
  setExplorerWidth: (w: number) => void;
  setEditorWidth: (w: number) => void;
}

function buildFiles(): FileEntry[] {
  return tutorials.map(t => ({
    name: t.filename,
    source: t.source,
    isTutorial: true,
  }));
}

function computeStructure(agent: AgentDecl): StructureData {
  const graph = agentToGraph(agent);
  const { chi, partition } = characterInvariant(graph);
  const floor = realisedFloor(graph);
  const allPartitions = allPartitionCosts(graph);
  const nonLocal = partition.blocks.every(b => b.length > 1);
  return {
    graph,
    chi,
    chiPartition: partition,
    floor,
    declaredFloor: agent.floor,
    allPartitions,
    nonLocal,
  };
}

function computeAttention(agent: AgentDecl): AttentionData {
  const profiles = agent.scenes.map((s, i) =>
    logGainProfile(s.name, s.gainK ?? (1.5 + i * 0.5))
  );
  const result = waterFill(profiles, agent.budget);
  return { profiles, result, budget: agent.budget };
}

function computeSociety(file: SmithFile): SocietyData | null {
  const soc = file.items.find(i => i.kind === "society");
  if (!soc || soc.kind !== "society") return null;

  const M = soc.agents.length;
  if (M === 0) return null;

  // Random initial phases, identical velocities for simplicity
  const initialPhases = soc.agents.map((_, i) => (2 * Math.PI * i) / M + Math.random() * 0.5);
  const velocities = soc.agents.map(() => 1.0);

  const history = kuramotoRun(initialPhases, velocities, soc.couple, 0.1, 500);
  const crowdCurve = crowdFailureCurve(0.6, 15);

  return {
    kuramotoHistory: history,
    coupling: soc.couple,
    agentNames: soc.agents.map(a => a.name),
    crowdCurve,
  };
}

export const useStore = create<IDEStore>((set, get) => ({
  files: buildFiles(),
  activeFile: tutorials[0].filename,
  source: tutorials[0].source,
  compiled: null,
  runResult: null,
  consoleLog: [],
  structureData: null,
  attentionData: null,
  executionData: null,
  societyData: null,
  activeTab: "structure",
  explorerWidth: 220,
  editorWidth: 420,

  setActiveFile: (name) => {
    const file = get().files.find(f => f.name === name);
    if (file) {
      set({ activeFile: name, source: file.source });
      // Auto-compile
      setTimeout(() => get().compileAndRun(), 0);
    }
  },

  setSource: (source) => {
    set({ source });
    // Update the file entry
    const files = get().files.map(f =>
      f.name === get().activeFile ? { ...f, source } : f
    );
    set({ files });
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  compileAndRun: () => {
    const source = get().source;
    const log: string[] = [];

    try {
      log.push(`Compiling ${get().activeFile}...`);
      const compiled = compile(source);

      if (!compiled.check.ok) {
        for (const err of compiled.check.errors) {
          log.push(`✗ ${err.severity}: ${err.message}${err.line ? ` (line ${err.line})` : ""}`);
        }
        set({ compiled, consoleLog: log, structureData: null, attentionData: null, executionData: null, societyData: null, runResult: null });
        return;
      }

      log.push(`✓ OK — ${compiled.check.agents.length} agent(s)`);
      for (const ac of compiled.check.agents) {
        log.push(`  ${ac.name}  regime=${ac.regime}  χ=${ac.chi}  floor=${ac.floor}  non-local=${ac.nonLocal}`);
      }

      // Run
      log.push(`Running (30 ticks)...`);
      const runResult = run(compiled.file, 30);
      log.push(`✓ ${runResult.steps.length} step records`);

      // Compute derived data
      const firstAgent = getFirstAgent(compiled.file);
      const structureData = firstAgent ? computeStructure(firstAgent) : null;
      const attentionData = firstAgent ? computeAttention(firstAgent) : null;
      const executionData: ExecutionData = { steps: runResult.steps, finalCounts: runResult.finalCounts };
      const societyData = computeSociety(compiled.file);

      set({
        compiled,
        runResult,
        consoleLog: log,
        structureData,
        attentionData,
        executionData,
        societyData,
      });
    } catch (e: any) {
      log.push(`✗ Internal error: ${e.message}`);
      set({ consoleLog: log });
    }
  },

  addFile: (name, source) => {
    const files = [...get().files, { name, source, isTutorial: false }];
    set({ files, activeFile: name, source });
  },

  patchSource: (_line, oldText, newText) => {
    const source = get().source.replace(oldText, newText);
    get().setSource(source);
    get().compileAndRun();
  },

  setExplorerWidth: (w) => set({ explorerWidth: w }),
  setEditorWidth: (w) => set({ editorWidth: w }),
}));

function getFirstAgent(file: SmithFile): AgentDecl | null {
  for (const item of file.items) {
    if (item.kind === "agent") return item;
    if (item.kind === "society" && item.agents.length > 0) return item.agents[0];
  }
  return null;
}
