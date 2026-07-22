// =====================================================================
//  /api/agent-smith-think — the Tier-1 model bridge.
//  Receives { provider, model, key, prompt, schema } and calls the chosen
//  provider. The key is the USER'S key, passed per-request (never stored on
//  the server, never in the bundle). Returns { text, provider, model }.
//
//  This is the single seam where the tool talks to a model. In a Buhera OS
//  deployment this route is replaced by one that wraps chatCascade and reads
//  keys from the server environment instead of the request.
// =====================================================================

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "POST only" });
    return;
  }
  const { provider, model, key, prompt } = req.body || {};
  if (!provider || !prompt) {
    res.status(400).json({ error: "provider and prompt are required" });
    return;
  }
  if (provider !== "ollama" && !key) {
    res.status(400).json({ error: `a key is required for ${provider}` });
    return;
  }

  try {
    let text;
    switch (provider) {
      case "huggingface":
        text = await callHuggingFace(model, key, prompt);
        break;
      case "openai":
        text = await callOpenAI(model, key, prompt);
        break;
      case "anthropic":
        text = await callAnthropic(model, key, prompt);
        break;
      case "gemini":
        text = await callGemini(model, key, prompt);
        break;
      case "ollama":
        text = await callOllama(model, key || "http://localhost:11434", prompt);
        break;
      default:
        res.status(400).json({ error: `unknown provider "${provider}"` });
        return;
    }
    res.status(200).json({ text: (text || "").trim(), provider, model });
  } catch (e) {
    res.status(502).json({ error: `${provider} error: ${e.message}` });
  }
}

// ---- provider adapters ----------------------------------------------

async function callHuggingFace(model, key, prompt) {
  // HF Inference API — chat completions style (router).
  const r = await fetch(`https://api-inference.huggingface.co/models/${model}/v1/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 64,
      temperature: 0.2,
    }),
  });
  if (!r.ok) throw new Error(`${r.status} ${await safeText(r)}`);
  const j = await r.json();
  return j.choices?.[0]?.message?.content ?? "";
}

async function callOpenAI(model, key, prompt) {
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: model || "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 64,
      temperature: 0.2,
    }),
  });
  if (!r.ok) throw new Error(`${r.status} ${await safeText(r)}`);
  const j = await r.json();
  return j.choices?.[0]?.message?.content ?? "";
}

async function callAnthropic(model, key, prompt) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: model || "claude-haiku-4-5-20251001",
      max_tokens: 64,
      messages: [{ role: "user", content: prompt }],
    }),
  });
  if (!r.ok) throw new Error(`${r.status} ${await safeText(r)}`);
  const j = await r.json();
  return j.content?.[0]?.text ?? "";
}

async function callGemini(model, key, prompt) {
  const m = model || "gemini-2.0-flash";
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${key}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { maxOutputTokens: 64, temperature: 0.2 },
      }),
    }
  );
  if (!r.ok) throw new Error(`${r.status} ${await safeText(r)}`);
  const j = await r.json();
  return j.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
}

async function callOllama(model, url, prompt) {
  const base = url.replace(/\/$/, "");
  const r = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: model || "llama3.2",
      messages: [{ role: "user", content: prompt }],
      stream: false,
      options: { temperature: 0.2, num_predict: 64 },
    }),
  });
  if (!r.ok) throw new Error(`${r.status} ${await safeText(r)}`);
  const j = await r.json();
  return j.message?.content ?? "";
}

async function safeText(r) {
  try {
    return await r.text();
  } catch {
    return "";
  }
}
