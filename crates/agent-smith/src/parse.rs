// =====================================================================
//  Agent Smith — parser.
//  Parses an Agent Smith script into a specification AST (ast.rs). Pure,
//  dependency-free. A direct port of parse.js: same tokenizer (// line
//  comments, string/number/identifier rules, PUNCT set), same
//  recursive-descent grammar, same 1-based line tracking, same error
//  messages. Forgiving about whitespace/comments, strict about structure.
// =====================================================================

use crate::ast::*;
use crate::error::ParseError;

type PResult<T> = Result<T, ParseError>;

// ---- tokenizer -------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
enum Tok {
    Punct(char), // one of { } ( ) , : =
    Str(String),
    Num(f64),
    Id(String),
    Eof,
}

#[derive(Debug, Clone)]
struct Token {
    t: Tok,
    line: u32,
}

fn is_punct(c: char) -> bool {
    matches!(c, '{' | '}' | '(' | ')' | ',' | ':' | '=')
}

fn tokenize(src: &str) -> PResult<Vec<Token>> {
    let chars: Vec<char> = src.chars().collect();
    let n = chars.len();
    let mut toks: Vec<Token> = Vec::new();
    let mut line: u32 = 1;
    let mut i = 0usize;

    while i < n {
        let c = chars[i];
        if c == '\n' {
            line += 1;
            i += 1;
            continue;
        }
        if c == ' ' || c == '\t' || c == '\r' {
            i += 1;
            continue;
        }
        // line comment: // to end of line
        if c == '/' && i + 1 < n && chars[i + 1] == '/' {
            while i < n && chars[i] != '\n' {
                i += 1;
            }
            continue;
        }
        if is_punct(c) {
            toks.push(Token { t: Tok::Punct(c), line });
            i += 1;
            continue;
        }
        // string literal
        if c == '"' {
            let mut j = i + 1;
            let mut s = String::new();
            while j < n && chars[j] != '"' {
                s.push(chars[j]);
                j += 1;
            }
            if j >= n {
                return Err(ParseError::new("unterminated string", Some(line)));
            }
            toks.push(Token { t: Tok::Str(s), line });
            i = j + 1;
            continue;
        }
        // number: digit, or '-' followed by a digit
        if c.is_ascii_digit() || (c == '-' && i + 1 < n && chars[i + 1].is_ascii_digit()) {
            let mut j = i + 1;
            while j < n && matches!(chars[j], '0'..='9' | '.' | 'e' | 'E' | '+' | '-') {
                j += 1;
            }
            let raw: String = chars[i..j].iter().collect();
            match raw.parse::<f64>() {
                Ok(v) => toks.push(Token { t: Tok::Num(v), line }),
                Err(_) => return Err(ParseError::new(format!("bad number \"{}\"", raw), Some(line))),
            }
            i = j;
            continue;
        }
        // identifier / keyword: [A-Za-z_][A-Za-z0-9_.]*
        if c.is_ascii_alphabetic() || c == '_' {
            let mut j = i + 1;
            while j < n && (chars[j].is_ascii_alphanumeric() || chars[j] == '_' || chars[j] == '.') {
                j += 1;
            }
            let s: String = chars[i..j].iter().collect();
            toks.push(Token { t: Tok::Id(s), line });
            i = j;
            continue;
        }
        return Err(ParseError::new(format!("unexpected character \"{}\"", c), Some(line)));
    }
    toks.push(Token { t: Tok::Eof, line });
    Ok(toks)
}

// ---- recursive-descent parser ---------------------------------------

struct Parser {
    toks: Vec<Token>,
    p: usize,
}

/// Human-facing token name, matching the JS `tk.v ?? tk.t` reporting.
fn tok_name(t: &Tok) -> String {
    match t {
        Tok::Punct(c) => c.to_string(),
        Tok::Str(s) => s.clone(),
        Tok::Num(v) => fmt_num(*v),
        Tok::Id(s) => s.clone(),
        Tok::Eof => "eof".to_string(),
    }
}

/// Format a number the way JS String() would for the common integer/float
/// cases that appear in these scripts (used only in error messages).
fn fmt_num(v: f64) -> String {
    if v.fract() == 0.0 && v.is_finite() {
        format!("{}", v as i64)
    } else {
        format!("{}", v)
    }
}

impl Parser {
    fn new(toks: Vec<Token>) -> Self {
        Parser { toks, p: 0 }
    }
    fn peek(&self) -> &Token {
        &self.toks[self.p]
    }
    fn next(&mut self) -> Token {
        let t = self.toks[self.p].clone();
        self.p += 1;
        t
    }
    fn at_punct(&self, c: char) -> bool {
        matches!(&self.peek().t, Tok::Punct(x) if *x == c)
    }
    fn at_eof(&self) -> bool {
        matches!(self.peek().t, Tok::Eof)
    }
    fn at_kw(&self, kw: &str) -> bool {
        matches!(&self.peek().t, Tok::Id(v) if v == kw)
    }
    fn eat_punct(&mut self, c: char) -> PResult<()> {
        let tk = self.peek().clone();
        if !self.at_punct(c) {
            return Err(ParseError::new(
                format!("expected \"{}\", got \"{}\"", c, tok_name(&tk.t)),
                Some(tk.line),
            ));
        }
        self.next();
        Ok(())
    }
    fn eat_kw(&mut self, kw: &str) -> PResult<()> {
        let tk = self.peek().clone();
        if !self.at_kw(kw) {
            return Err(ParseError::new(
                format!("expected \"{}\", got \"{}\"", kw, tok_name(&tk.t)),
                Some(tk.line),
            ));
        }
        self.next();
        Ok(())
    }
    fn id(&mut self) -> PResult<String> {
        let tk = self.peek().clone();
        match &tk.t {
            Tok::Id(v) => {
                let v = v.clone();
                self.next();
                Ok(v)
            }
            _ => Err(ParseError::new(
                format!("expected identifier, got \"{}\"", tok_name(&tk.t)),
                Some(tk.line),
            )),
        }
    }
    fn num(&mut self) -> PResult<f64> {
        let tk = self.peek().clone();
        match tk.t {
            Tok::Num(v) => {
                self.next();
                Ok(v)
            }
            _ => Err(ParseError::new(
                format!("expected number, got \"{}\"", tok_name(&tk.t)),
                Some(tk.line),
            )),
        }
    }

    // ---- top level ----
    fn parse_program(&mut self) -> PResult<Spec> {
        let tk = self.peek().clone();
        if self.at_kw("agent") {
            return Ok(Spec::Agent(self.parse_agent()?));
        }
        if self.at_kw("society") {
            return Ok(Spec::Society(self.parse_society()?));
        }
        Err(ParseError::new(
            format!("expected \"agent\" or \"society\", got \"{}\"", tok_name(&tk.t)),
            Some(tk.line),
        ))
    }

    // ---- agent ----
    fn parse_agent(&mut self) -> PResult<AgentSpec> {
        let line = self.peek().line;
        self.eat_kw("agent")?;
        let name = self.id()?;
        self.eat_punct('{')?;
        let mut spec = AgentSpec {
            name,
            line,
            purpose: None,
            scenes: Vec::new(),
            self_graph: None,
            budget: None,
            floor: None,
            coherence: None,
        };
        while !self.at_punct('}') {
            if self.at_eof() {
                return Err(ParseError::new("unclosed \"agent\" block", Some(line)));
            }
            if self.at_kw("purpose") {
                spec.purpose = Some(self.parse_purpose()?);
            } else if self.at_kw("scenes") {
                spec.scenes = self.parse_scenes()?;
            } else if self.at_kw("self") {
                spec.self_graph = Some(self.parse_self()?);
            } else if self.at_kw("budget") {
                self.eat_kw("budget")?;
                spec.budget = Some(self.num()?);
            } else if self.at_kw("floor") {
                self.eat_kw("floor")?;
                spec.floor = Some(self.num()?);
            } else if self.at_kw("coherence") {
                spec.coherence = Some(self.parse_coherence()?);
            } else {
                let bad = self.peek().clone();
                return Err(ParseError::new(
                    format!("unexpected \"{}\" in agent body", tok_name(&bad.t)),
                    Some(bad.line),
                ));
            }
        }
        self.eat_punct('}')?;
        Ok(spec)
    }

    fn parse_purpose(&mut self) -> PResult<Purpose> {
        self.eat_kw("purpose")?;
        let tk = self.peek().clone();
        if self.at_kw("minimise") || self.at_kw("minimize") {
            self.next();
            let potential = self.id()?;
            return Ok(Purpose::Minimise { potential, line: tk.line });
        }
        if self.at_kw("reach") {
            self.next();
            let outcome = self.id()?;
            return Ok(Purpose::Reach { outcome, line: tk.line });
        }
        Err(ParseError::new(
            "purpose must be \"minimise <phi>\" or \"reach <outcome>\"",
            Some(tk.line),
        ))
    }

    fn parse_scenes(&mut self) -> PResult<Vec<Scene>> {
        self.eat_kw("scenes")?;
        self.eat_punct('{')?;
        let mut scenes = Vec::new();
        while !self.at_punct('}') {
            if self.at_eof() {
                return Err(ParseError::new("unclosed \"scenes\" block", Some(self.peek().line)));
            }
            let line = self.peek().line;
            self.eat_kw("scene")?;
            let name = self.id()?;
            self.eat_kw("serves")?;
            let serves = self.id()?;
            self.eat_kw("with")?;
            let hook = self.id()?;
            scenes.push(Scene { name, serves, hook, line });
        }
        self.eat_punct('}')?;
        Ok(scenes)
    }

    fn parse_self(&mut self) -> PResult<SelfGraph> {
        let line = self.peek().line;
        self.eat_kw("self")?;
        self.eat_punct('{')?;
        let mut parts: Vec<String> = Vec::new();
        let mut separations: Vec<Separation> = Vec::new();
        while !self.at_punct('}') {
            if self.at_eof() {
                return Err(ParseError::new("unclosed \"self\" block", Some(line)));
            }
            if self.at_kw("parts") {
                self.eat_kw("parts")?;
                parts = self.parse_id_list()?;
            } else if self.at_kw("separations") {
                self.eat_kw("separations")?;
                separations = self.parse_separations()?;
            } else {
                let bad = self.peek().clone();
                return Err(ParseError::new(
                    format!("unexpected \"{}\" in self body", tok_name(&bad.t)),
                    Some(bad.line),
                ));
            }
        }
        self.eat_punct('}')?;
        Ok(SelfGraph { parts, separations, line })
    }

    // { a, b, c }
    fn parse_id_list(&mut self) -> PResult<Vec<String>> {
        self.eat_punct('{')?;
        let mut ids = Vec::new();
        while !self.at_punct('}') {
            ids.push(self.id()?);
            if self.at_punct(',') {
                self.next();
            } else if !self.at_punct('}') {
                return Err(ParseError::new("expected \",\" or \"}\"", Some(self.peek().line)));
            }
        }
        self.eat_punct('}')?;
        Ok(ids)
    }

    // { (a, b: 3), (b, c: 2), ... }
    fn parse_separations(&mut self) -> PResult<Vec<Separation>> {
        self.eat_punct('{')?;
        let mut seps = Vec::new();
        while !self.at_punct('}') {
            let line = self.peek().line;
            self.eat_punct('(')?;
            let a = self.id()?;
            self.eat_punct(',')?;
            let b = self.id()?;
            self.eat_punct(':')?;
            let cost = self.num()?;
            self.eat_punct(')')?;
            seps.push(Separation { a, b, cost, line });
            if self.at_punct(',') {
                self.next();
            } else if !self.at_punct('}') {
                return Err(ParseError::new("expected \",\" or \"}\"", Some(self.peek().line)));
            }
        }
        self.eat_punct('}')?;
        Ok(seps)
    }

    fn parse_coherence(&mut self) -> PResult<Coherence> {
        let line = self.peek().line;
        self.eat_kw("coherence")?;
        // optional "keeps"
        if self.at_kw("keeps") {
            self.next();
        }
        let keeps = self.parse_id_list()?;
        Ok(Coherence { keeps, line })
    }

    // ---- society ----
    fn parse_society(&mut self) -> PResult<SocietySpec> {
        let line = self.peek().line;
        self.eat_kw("society")?;
        let name = self.id()?;
        self.eat_punct('{')?;
        let mut spec = SocietySpec {
            name,
            line,
            members: Vec::new(),
            ties: Vec::new(),
            couple: None,
        };
        while !self.at_punct('}') {
            if self.at_eof() {
                return Err(ParseError::new("unclosed \"society\" block", Some(line)));
            }
            if self.at_kw("agent") {
                spec.members.push(Member::Agent(self.parse_agent()?));
            } else if self.at_kw("tie") {
                self.eat_kw("tie")?;
                self.eat_punct('(')?;
                let a = self.id()?;
                self.eat_punct(',')?;
                let b = self.id()?;
                self.eat_punct(':')?;
                let cost = self.num()?;
                self.eat_punct(')')?;
                spec.ties.push(Tie { a, b, cost });
            } else if self.at_kw("couple") {
                self.eat_kw("couple")?;
                spec.couple = Some(self.num()?);
            } else {
                // a bare member reference by name
                let bad = self.peek().clone();
                match &bad.t {
                    Tok::Id(_) => {
                        let name = self.id()?;
                        spec.members.push(Member::Ref { name, line: bad.line });
                    }
                    _ => {
                        return Err(ParseError::new(
                            format!("unexpected \"{}\" in society body", tok_name(&bad.t)),
                            Some(bad.line),
                        ));
                    }
                }
            }
        }
        self.eat_punct('}')?;
        Ok(spec)
    }
}

/// Parse an Agent Smith script into a spec AST.
pub fn parse(src: &str) -> PResult<Spec> {
    let toks = tokenize(src)?;
    let mut parser = Parser::new(toks);
    let spec = parser.parse_program()?;
    if !parser.at_eof() {
        let tk = parser.peek().clone();
        return Err(ParseError::new(
            format!("unexpected trailing \"{}\"", tok_name(&tk.t)),
            Some(tk.line),
        ));
    }
    Ok(spec)
}
