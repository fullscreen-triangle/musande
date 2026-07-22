// =====================================================================
//  Agent Smith — model provider registry (client side).
//  Models are REQUIRED: every agent's think step calls a real model.
//  The user supplies API keys for any subscription; HuggingFace enables
//  the many-models crowd (several models polled per judgment → consensus,
//  the crowd-sharpening of the theory).
//
//  This module knows the providers and their models, holds the user's
//  keys (in the browser only), and exposes `think()` which routes a
//  prompt to a chosen provider/model via the /api/agent-smith-think
//  route (keys travel to our own route, never embedded in the bundle).
//
//  In a Buhera OS deployment, `setThinkTransport()` swaps the transport
//  for chatCascade so provider selection is centralised there instead.
// =====================================================================

export const PROVIDERS = {
  huggingface: {
    id: "huggingface",
    label: "HuggingFace",
    keyLabel: "HF token (hf_...)",
    // a spread of small, cheap, instruct models — the crowd
    models: [
      "meta-llama/Llama-3.2-3B-Instruct",
      "mistralai/Mistral-7B-Instruct-v0.3",
      "Qwen/Qwen2.5-7B-Instruct",
      "google/gemma-2-2b-it",
      "HuggingFaceH4/zephyr-7b-beta",
    ],
    crowdCapable: true, // can poll several models for consensus
  },
  openai: {
    id: "openai",
    label: "OpenAI",
    keyLabel: "OpenAI key (sk-...)",
    models: ["gpt-4o-mini", "gpt-4o"],
    crowdCapable: false,
  },
  anthropic: {
    id: "anthropic",
    label: "Anthropic",
    keyLabel: "Anthropic key (sk-ant-...)",
    models: ["claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-4-8"],
    crowdCapable: false,
  },
  gemini: {
    id: "gemini",
    label: "Google Gemini",
    keyLabel: "Gemini API key",
    models: ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    crowdCapable: false,
  },
  ollama: {
    id: "ollama",
    label: "Ollama (local)",
    keyLabel: "Ollama URL (http://localhost:11434)",
    models: ["llama3.2", "qwen2.5", "mistral"],
    crowdCapable: true,
  },
};

const KEYS_STORAGE = "agent-smith:keys";

/** Load user keys from localStorage (browser only). */
export function loadKeys() {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(KEYS_STORAGE) || "{}");
  } catch {
    return {};
  }
}

/** Persist user keys to localStorage. */
export function saveKeys(keys) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEYS_STORAGE, JSON.stringify(keys));
}

/** Which providers have a key set? */
export function configuredProviders(keys = loadKeys()) {
  return Object.values(PROVIDERS).filter((p) => (keys[p.id] || "").trim().length > 0);
}

/** True if at least one provider is usable — the tool requires this. */
export function hasModel(keys = loadKeys()) {
  return configuredProviders(keys).length > 0;
}

// ---- the think transport --------------------------------------------
// Default transport POSTs to our own API route with the chosen provider,
// model, key, and prompt. A Buhera deployment replaces this.

let _transport = async ({ provider, model, key, prompt, schema }) => {
  const res = await fetch("/api/agent-smith-think", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model, key, prompt, schema }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `provider ${provider} returned ${res.status}`);
  }
  return res.json(); // { text, provider, model }
}

/** Swap the transport (Buhera OS: route through chatCascade). */
export function setThinkTransport(fn) {
  _transport = fn;
}

/**
 * think(prompt, opts) — call a model.
 * opts: { providerId?, model?, keys?, crowd? }
 * If crowd is true and the provider is crowd-capable, polls several models
 * and returns { text, votes } where votes is the per-model raw answers.
 * Returns { text, provider, model, votes? }.
 */
export async function think(prompt, opts = {}) {
  const keys = opts.keys || loadKeys();
  const configured = configuredProviders(keys);
  if (configured.length === 0) {
    throw new Error("no model provider configured — add an API key to run agents");
  }
  const provider =
    (opts.providerId && PROVIDERS[opts.providerId]) ||
    configured.find((p) => p.crowdCapable) ||
    configured[0];
  const key = keys[provider.id];

  if (opts.crowd && provider.crowdCapable) {
    const models = provider.models.slice(0, opts.crowdSize || 3);
    const results = await Promise.allSettled(
      models.map((model) => _transport({ provider: provider.id, model, key, prompt, schema: opts.schema }))
    );
    const votes = results
      .filter((r) => r.status === "fulfilled")
      .map((r) => ({ model: r.value.model, text: r.value.text }));
    if (votes.length === 0) throw new Error(`all ${provider.label} models failed`);
    // consensus: majority-ish — return the most common answer, keep votes.
    const text = consensus(votes.map((v) => v.text));
    return { text, provider: provider.id, model: `${provider.label} crowd (${votes.length})`, votes };
  }

  const model = opts.model || provider.models[0];
  const r = await _transport({ provider: provider.id, model, key, prompt, schema: opts.schema });
  return { text: r.text, provider: provider.id, model: r.model || model };
}

/** Crude consensus: the answer nearest to the others (least total edit-ish). */
function consensus(texts) {
  if (texts.length === 1) return texts[0];
  // normalise + majority on the first token/decision word if present
  const norm = texts.map((t) => (t || "").trim().toLowerCase());
  const counts = new Map();
  for (const t of norm) counts.set(t, (counts.get(t) || 0) + 1);
  let best = norm[0];
  let bestN = 0;
  for (const [t, n] of counts) if (n > bestN) ((best = t), (bestN = n));
  // return the original-cased text matching the winning normalised form
  const i = norm.indexOf(best);
  return texts[i] ?? texts[0];
}
