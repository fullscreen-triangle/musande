"use client";

import React, { useRef, useCallback, useEffect } from "react";
import MonacoEditor, { type OnMount, type BeforeMount } from "@monaco-editor/react";
import { useStore } from "@/store/useStore";

// Register .smith language for Monaco
function registerSmithLanguage(monaco: any) {
  // Register the language
  monaco.languages.register({ id: "smith" });

  // Tokenizer
  monaco.languages.setMonarchTokensProvider("smith", {
    keywords: [
      "agent", "society", "purpose", "minimise", "reach", "scenes", "scene",
      "serves", "with", "self", "parts", "separations", "budget", "floor",
      "coherence", "keeps", "tie", "couple", "template", "structure", "probe", "against",
    ],
    operators: [":"],
    symbols: /[{}(),]/,

    tokenizer: {
      root: [
        // Comments
        [/\/\/.*$/, "comment"],
        // Keywords
        [/[a-zA-Z_]\w*/, {
          cases: {
            "@keywords": "keyword",
            "@default": "identifier",
          },
        }],
        // Numbers
        [/\d+\.?\d*/, "number"],
        // Symbols
        [/[{}(),:]/, "delimiter"],
        // Whitespace
        [/\s+/, "white"],
      ],
    },
  });

  // Theme
  monaco.editor.defineTheme("smith-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "d4a849", fontStyle: "bold" },
      { token: "identifier", foreground: "e8e4dd" },
      { token: "number", foreground: "5b8dd9" },
      { token: "comment", foreground: "5a5854", fontStyle: "italic" },
      { token: "delimiter", foreground: "9a9690" },
      { token: "string", foreground: "5fa85f" },
    ],
    colors: {
      "editor.background": "#111118",
      "editor.foreground": "#e8e4dd",
      "editor.lineHighlightBackground": "#1a1a24",
      "editor.selectionBackground": "#2a2a3660",
      "editorCursor.foreground": "#d4a849",
      "editorLineNumber.foreground": "#3a3a4a",
      "editorLineNumber.activeForeground": "#9a9690",
      "editorIndentGuide.background": "#1a1a24",
      "editorGutter.background": "#111118",
    },
  });

  // Completions
  monaco.languages.registerCompletionItemProvider("smith", {
    provideCompletionItems: (_model: any, position: any) => {
      const suggestions = [
        { label: "agent", kind: monaco.languages.CompletionItemKind.Keyword, insertText: "agent ${1:name} {\n  purpose minimise ${2:residual}\n  scenes {\n    scene ${3:work} serves ${2:residual} with ${4:hook}\n  }\n  self {\n    parts { ${5:a, b} }\n    separations { (${6:a, b: 2}) }\n  }\n  budget ${7:1.0}\n  floor  ${8:2.0}\n}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
        { label: "society", kind: monaco.languages.CompletionItemKind.Keyword, insertText: "society ${1:name} {\n  $0\n  couple ${2:3.0}\n}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
        { label: "scene", kind: monaco.languages.CompletionItemKind.Keyword, insertText: "scene ${1:name} serves ${2:target} with ${3:hook}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
        { label: "purpose", kind: monaco.languages.CompletionItemKind.Keyword, insertText: "purpose minimise ${1:residual}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
        { label: "tie", kind: monaco.languages.CompletionItemKind.Keyword, insertText: "tie (${1:a}, ${2:b}: ${3:2})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet },
      ];
      return { suggestions };
    },
  });
}

export function Editor() {
  const source = useStore(s => s.source);
  const setSource = useStore(s => s.setSource);
  const compileAndRun = useStore(s => s.compileAndRun);
  const compiled = useStore(s => s.compiled);
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const handleBeforeMount: BeforeMount = useCallback((monaco) => {
    monacoRef.current = monaco;
    registerSmithLanguage(monaco);
  }, []);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    // Keyboard shortcut: Ctrl/Cmd+Enter to compile
    editor.addAction({
      id: "smith-compile",
      label: "Compile and Run",
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => compileAndRun(),
    });
  }, [compileAndRun]);

  const handleChange = useCallback((value: string | undefined) => {
    if (value !== undefined) {
      setSource(value);
      // Debounced auto-compile
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => compileAndRun(), 600);
    }
  }, [setSource, compileAndRun]);

  // Update error markers
  useEffect(() => {
    if (!monacoRef.current || !editorRef.current) return;
    const monaco = monacoRef.current;
    const model = editorRef.current.getModel();
    if (!model) return;

    const markers = (compiled?.check.errors ?? []).map(err => ({
      severity: err.severity === "error" ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning,
      message: err.message,
      startLineNumber: err.line ?? 1,
      startColumn: 1,
      endLineNumber: err.line ?? 1,
      endColumn: 1000,
    }));

    monaco.editor.setModelMarkers(model, "smith", markers);
  }, [compiled]);

  return (
    <div className="h-full flex flex-col bg-bg-panel border-r border-border-subtle">
      {/* Editor header */}
      <div className="h-9 flex items-center px-3 border-b border-border-subtle flex-shrink-0 gap-2">
        <span className="text-[11px] font-semibold text-fg-secondary uppercase tracking-wider">
          Editor
        </span>
        <span className="ml-auto text-[10px] text-fg-muted font-mono">
          Ctrl+Enter to compile
        </span>
      </div>

      {/* Monaco */}
      <div className="flex-1">
        <MonacoEditor
          language="smith"
          theme="smith-dark"
          value={source}
          onChange={handleChange}
          beforeMount={handleBeforeMount}
          onMount={handleMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: true,
            lineNumbers: "on",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: "line",
            padding: { top: 8 },
            bracketPairColorization: { enabled: true },
            guides: { indentation: true, bracketPairs: true },
            tabSize: 2,
            wordWrap: "on",
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
          }}
        />
      </div>
    </div>
  );
}
