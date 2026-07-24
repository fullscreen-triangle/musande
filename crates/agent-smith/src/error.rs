// =====================================================================
//  Agent Smith — error types.
//  Parse errors carry a 1-based line; type errors carry an optional line.
//  A Diagnostic is the normalised {message, line} shape both produce, so
//  the CLI and library can report them uniformly.
// =====================================================================

use thiserror::Error;

/// A normalised diagnostic: a message and an optional 1-based line number.
/// Both parse and type errors lower to this for uniform reporting.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct Diagnostic {
    pub message: String,
    pub line: Option<u32>,
}

impl Diagnostic {
    pub fn new(message: impl Into<String>, line: Option<u32>) -> Self {
        Diagnostic { message: message.into(), line }
    }
}

impl std::fmt::Display for Diagnostic {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self.line {
            Some(l) => write!(f, "line {}: {}", l, self.message),
            None => f.write_str(&self.message),
        }
    }
}

/// A parse error: a message and an optional 1-based line number.
/// Mirrors the JS `ParseError` (its `.message` is prefixed with the line).
#[derive(Debug, Clone, Error)]
#[error("{}", .0)]
pub struct ParseError(pub Diagnostic);

impl ParseError {
    pub fn new(message: impl Into<String>, line: Option<u32>) -> Self {
        ParseError(Diagnostic::new(message, line))
    }
    pub fn line(&self) -> Option<u32> {
        self.0.line
    }
    pub fn into_diagnostic(self) -> Diagnostic {
        self.0
    }
}
