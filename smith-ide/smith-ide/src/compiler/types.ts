// =====================================================================
//  DSL AST types for .smith scripts.
//  The compiler (being built separately) will parse into these types.
//  The UI renders from these types.
// =====================================================================

// --- AST nodes ---

export interface SmithFile {
  kind: "file";
  items: TopLevelItem[];
}

export type TopLevelItem = AgentDecl | SocietyDecl;

export interface AgentDecl {
  kind: "agent";
  name: string;
  purpose: PurposeDecl;
  scenes: SceneDecl[];
  self: SelfDecl;
  budget: number;
  floor: number;
  coherence?: CoherenceDecl;
  line?: number; // source line for editor linking
}

export interface SocietyDecl {
  kind: "society";
  name: string;
  agents: AgentDecl[];
  ties: TieDecl[];
  couple: number;
  line?: number;
}

export interface PurposeDecl {
  kind: "purpose";
  mode: "minimise" | "reach";
  target: string;
}

export interface SceneDecl {
  kind: "scene";
  name: string;
  serves: string;
  hook: string;
  gainK?: number; // gain profile parameter k for γ(a) = ln(1 + ka)
  line?: number;
}

export interface SelfDecl {
  kind: "self";
  parts: string[];
  separations: SeparationDecl[];
}

export interface SeparationDecl {
  from: string;
  to: string;
  cost: number;
  line?: number;
}

export interface TieDecl {
  from: string;
  to: string;
  cost: number;
}

export interface CoherenceDecl {
  keeps: string[];
}

// --- Template (for epidemiology tutorials) ---

export interface TemplateDecl {
  kind: "template";
  name: string;
  structure: { dimension: string; weight: number }[];
  convergenceTime?: number;
}

export interface ProbeDecl {
  kind: "probe";
  template: string;
  against: string;
}

// --- Compiler output ---

export interface CheckResult {
  ok: boolean;
  errors: Diagnostic[];
  agents: AgentCheck[];
}

export interface AgentCheck {
  name: string;
  regime: "character" | "task";
  chi: number;
  floor: number;
  nonLocal: boolean;
  chiPartition: string[][];
}

export interface Diagnostic {
  message: string;
  line?: number;
  severity: "error" | "warning" | "info";
}

// --- Runtime output ---

export interface StepRecord {
  tick: number;
  agent: string;
  outcome: "commit" | "observe" | "decline" | "quiescent";
  scene?: string;
  price: number;
  residual: number;
  delta: number;
  count: number;
  phase: "construction" | "commitment";
  disposition?: number[];
}

export interface RunResult {
  steps: StepRecord[];
  finalCounts: Record<string, number>;
}

// --- Compiled program (what the compiler produces) ---

export interface CompiledProgram {
  file: SmithFile;
  check: CheckResult;
}
