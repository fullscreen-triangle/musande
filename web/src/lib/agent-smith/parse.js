// =====================================================================
//  Agent Smith — parser.
//  Parses an Agent Smith script (the `agent {...}` / `society {...}`
//  grammar of the paper) into a specification AST. Pure, dependency-free.
//
//  Grammar (concrete surface):
//    agent <id> {
//      purpose (minimise <phi> | reach <outcome>)
//      scenes { scene <id> serves <purpose> with <hook> ... }
//      self { parts { a, b, ... } separations { (a, b: cost), ... } }
//      budget <num>
//      floor  <num>
//      coherence keeps { a, b, ... }
//    }
//    society <id> { <agent-or-ref> ... tie (a,b: cost) ... couple <K> }
//
//  The parser is deliberately forgiving about whitespace and comments
//  (// to end of line) and strict about structure, so that typing
//  (typecheck.js) — not parsing — is where an agent is rejected.
// =====================================================================

/** A parse error carries a message and a 1-based line number. */
export class ParseError extends Error {
  constructor(message, line) {
    super(line ? `line ${line}: ${message}` : message);
    this.line = line || null;
    this.name = "ParseError";
  }
}

// ---- tokenizer -------------------------------------------------------

const PUNCT = new Set(["{", "}", "(", ")", ",", ":", "="]);

function tokenize(src) {
  const toks = [];
  let line = 1;
  let i = 0;
  const n = src.length;
  while (i < n) {
    const c = src[i];
    if (c === "\n") {
      line++;
      i++;
      continue;
    }
    if (c === " " || c === "\t" || c === "\r") {
      i++;
      continue;
    }
    // line comment
    if (c === "/" && src[i + 1] === "/") {
      while (i < n && src[i] !== "\n") i++;
      continue;
    }
    if (PUNCT.has(c)) {
      toks.push({ t: c, line });
      i++;
      continue;
    }
    // string literal
    if (c === '"') {
      let j = i + 1;
      let s = "";
      while (j < n && src[j] !== '"') {
        s += src[j];
        j++;
      }
      if (j >= n) throw new ParseError("unterminated string", line);
      toks.push({ t: "str", v: s, line });
      i = j + 1;
      continue;
    }
    // number
    if (/[0-9]/.test(c) || (c === "-" && /[0-9]/.test(src[i + 1] || ""))) {
      let j = i + 1;
      while (j < n && /[0-9.eE+\-]/.test(src[j])) j++;
      const raw = src.slice(i, j);
      const v = Number(raw);
      if (Number.isNaN(v)) throw new ParseError(`bad number "${raw}"`, line);
      toks.push({ t: "num", v, line });
      i = j;
      continue;
    }
    // identifier / keyword
    if (/[A-Za-z_]/.test(c)) {
      let j = i + 1;
      while (j < n && /[A-Za-z0-9_.]/.test(src[j])) j++;
      toks.push({ t: "id", v: src.slice(i, j), line });
      i = j;
      continue;
    }
    throw new ParseError(`unexpected character "${c}"`, line);
  }
  toks.push({ t: "eof", line });
  return toks;
}

// ---- recursive-descent parser ---------------------------------------

class Parser {
  constructor(toks) {
    this.toks = toks;
    this.p = 0;
  }
  peek() {
    return this.toks[this.p];
  }
  next() {
    return this.toks[this.p++];
  }
  at(t) {
    return this.peek().t === t;
  }
  atKw(kw) {
    const tk = this.peek();
    return tk.t === "id" && tk.v === kw;
  }
  eat(t) {
    const tk = this.peek();
    if (tk.t !== t) throw new ParseError(`expected "${t}", got "${tk.v ?? tk.t}"`, tk.line);
    return this.next();
  }
  eatKw(kw) {
    const tk = this.peek();
    if (tk.t !== "id" || tk.v !== kw)
      throw new ParseError(`expected "${kw}", got "${tk.v ?? tk.t}"`, tk.line);
    return this.next();
  }
  id() {
    const tk = this.peek();
    if (tk.t !== "id") throw new ParseError(`expected identifier, got "${tk.v ?? tk.t}"`, tk.line);
    return this.next().v;
  }
  num() {
    const tk = this.peek();
    if (tk.t !== "num") throw new ParseError(`expected number, got "${tk.v ?? tk.t}"`, tk.line);
    return this.next().v;
  }

  // ---- top level ----
  parseProgram() {
    const tk = this.peek();
    if (this.atKw("agent")) return this.parseAgent();
    if (this.atKw("society")) return this.parseSociety();
    throw new ParseError(`expected "agent" or "society", got "${tk.v ?? tk.t}"`, tk.line);
  }

  // ---- agent ----
  parseAgent() {
    const line = this.peek().line;
    this.eatKw("agent");
    const name = this.id();
    this.eat("{");
    const spec = {
      kind: "agent",
      name,
      line,
      purpose: null,
      scenes: [],
      self: null,
      budget: null,
      floor: null,
      coherence: null,
    };
    while (!this.at("}")) {
      if (this.at("eof")) throw new ParseError('unclosed "agent" block', line);
      if (this.atKw("purpose")) spec.purpose = this.parsePurpose();
      else if (this.atKw("scenes")) spec.scenes = this.parseScenes();
      else if (this.atKw("self")) spec.self = this.parseSelf();
      else if (this.atKw("budget")) {
        this.eatKw("budget");
        spec.budget = this.num();
      } else if (this.atKw("floor")) {
        this.eatKw("floor");
        spec.floor = this.num();
      } else if (this.atKw("coherence")) spec.coherence = this.parseCoherence();
      else {
        const bad = this.peek();
        throw new ParseError(`unexpected "${bad.v ?? bad.t}" in agent body`, bad.line);
      }
    }
    this.eat("}");
    return spec;
  }

  parsePurpose() {
    this.eatKw("purpose");
    const tk = this.peek();
    if (this.atKw("minimise") || this.atKw("minimize")) {
      this.next();
      const potential = this.id();
      return { mode: "minimise", potential, line: tk.line };
    }
    if (this.atKw("reach")) {
      this.next();
      const outcome = this.id();
      return { mode: "reach", outcome, line: tk.line };
    }
    throw new ParseError(`purpose must be "minimise <phi>" or "reach <outcome>"`, tk.line);
  }

  parseScenes() {
    this.eatKw("scenes");
    this.eat("{");
    const scenes = [];
    while (!this.at("}")) {
      if (this.at("eof")) throw new ParseError('unclosed "scenes" block', this.peek().line);
      const line = this.peek().line;
      this.eatKw("scene");
      const name = this.id();
      this.eatKw("serves");
      const serves = this.id();
      this.eatKw("with");
      const hook = this.id();
      scenes.push({ name, serves, hook, line });
    }
    this.eat("}");
    return scenes;
  }

  parseSelf() {
    const line = this.peek().line;
    this.eatKw("self");
    this.eat("{");
    let parts = [];
    let separations = [];
    while (!this.at("}")) {
      if (this.at("eof")) throw new ParseError('unclosed "self" block', line);
      if (this.atKw("parts")) {
        this.eatKw("parts");
        parts = this.parseIdList();
      } else if (this.atKw("separations")) {
        this.eatKw("separations");
        separations = this.parseSeparations();
      } else {
        const bad = this.peek();
        throw new ParseError(`unexpected "${bad.v ?? bad.t}" in self body`, bad.line);
      }
    }
    this.eat("}");
    return { parts, separations, line };
  }

  // { a, b, c }
  parseIdList() {
    this.eat("{");
    const ids = [];
    while (!this.at("}")) {
      ids.push(this.id());
      if (this.at(",")) this.next();
      else if (!this.at("}")) throw new ParseError('expected "," or "}"', this.peek().line);
    }
    this.eat("}");
    return ids;
  }

  // { (a, b: 3), (b, c: 2), ... }
  parseSeparations() {
    this.eat("{");
    const seps = [];
    while (!this.at("}")) {
      const line = this.peek().line;
      this.eat("(");
      const a = this.id();
      this.eat(",");
      const b = this.id();
      this.eat(":");
      const cost = this.num();
      this.eat(")");
      seps.push({ a, b, cost, line });
      if (this.at(",")) this.next();
      else if (!this.at("}")) throw new ParseError('expected "," or "}"', this.peek().line);
    }
    this.eat("}");
    return seps;
  }

  parseCoherence() {
    const line = this.peek().line;
    this.eatKw("coherence");
    // optional "keeps"
    if (this.atKw("keeps")) this.next();
    const keeps = this.parseIdList();
    return { keeps, line };
  }

  // ---- society ----
  parseSociety() {
    const line = this.peek().line;
    this.eatKw("society");
    const name = this.id();
    this.eat("{");
    const spec = { kind: "society", name, line, members: [], ties: [], couple: null };
    while (!this.at("}")) {
      if (this.at("eof")) throw new ParseError('unclosed "society" block', line);
      if (this.atKw("agent")) spec.members.push(this.parseAgent());
      else if (this.atKw("tie")) {
        this.eatKw("tie");
        this.eat("(");
        const a = this.id();
        this.eat(",");
        const b = this.id();
        this.eat(":");
        const cost = this.num();
        this.eat(")");
        spec.ties.push({ a, b, cost });
      } else if (this.atKw("couple")) {
        this.eatKw("couple");
        spec.couple = this.num();
      } else {
        // a bare member reference by name
        const bad = this.peek();
        if (bad.t === "id") {
          spec.members.push({ kind: "ref", name: this.id(), line: bad.line });
        } else {
          throw new ParseError(`unexpected "${bad.v ?? bad.t}" in society body`, bad.line);
        }
      }
    }
    this.eat("}");
    return spec;
  }
}

/**
 * Parse an Agent Smith script into a spec AST.
 * @param {string} src
 * @returns {object} the spec (kind: "agent" | "society")
 * @throws {ParseError}
 */
export function parse(src) {
  const toks = tokenize(src);
  const parser = new Parser(toks);
  const spec = parser.parseProgram();
  if (!parser.at("eof")) {
    const tk = parser.peek();
    throw new ParseError(`unexpected trailing "${tk.v ?? tk.t}"`, tk.line);
  }
  return spec;
}
