import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { answerClarification, startResearch, type RunReportResult } from "./api";
import "./App.css";

const EXAMPLES = [
  "Investment thesis for NVIDIA over the next 12 months",
  "Compare Shopify vs Amazon as long-term e-commerce plays",
  "Risks and opportunities for TSMC given US-China tensions",
];

type QA = { question: string; answer: string };
type Phase =
  | { kind: "idle" }
  | { kind: "loading"; label: string }
  | { kind: "clarify"; session_id: string; question: string }
  | { kind: "error"; message: string }
  | { kind: "report"; report_markdown: string; pdf_base64?: string; pdf_filename?: string };

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [history, setHistory] = useState<QA[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const promptRef = useRef<HTMLTextAreaElement>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (phase.kind === "clarify") answerRef.current?.focus();
    else promptRef.current?.focus();
  }, [phase.kind]);

  const pdfHref = useMemo(
    () => (phase.kind === "report" && phase.pdf_base64 ? `data:application/pdf;base64,${phase.pdf_base64}` : null),
    [phase],
  );

  function applyResult(res: RunReportResult) {
    if (res.ok === false) {
    return setPhase({ kind: "error", message: res.error });
    };
    if (res.status === "needs_clarification") {
      setPhase({ kind: "clarify", session_id: res.session_id, question: res.clarification_question });
      return;
    }
    setPhase({
      kind: "report",
      report_markdown: res.report_markdown,
      pdf_base64: res.pdf_base64,
      pdf_filename: res.pdf_filename,
    });
  }

  async function onSubmitPrompt(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || phase.kind === "loading") return;
    setHistory([]);
    setCurrentAnswer("");
    setPhase({ kind: "loading", label: "Planning your research" });
    applyResult(await startResearch(prompt.trim()));
  }

  async function onSubmitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (phase.kind !== "clarify" || !currentAnswer.trim()) return;
    const answered = { question: phase.question, answer: currentAnswer.trim() };
    setHistory((h) => [...h, answered]);
    const sid = phase.session_id;
    setCurrentAnswer("");
    setPhase({ kind: "loading", label: "Continuing research" });
    applyResult(await answerClarification(sid, answered.answer));
  }

  const isLoading = phase.kind === "loading";
  const disabled = isLoading || phase.kind === "clarify";

  return (
    <div className="app">
      <header>
        <h1>InvestMind</h1>
        <p className="sub">Multi-agent investment research</p>
      </header>

      <main>
        <form onSubmit={onSubmitPrompt}>
          <textarea
            ref={promptRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Investment thesis for NVIDIA over the next 12 months"
            rows={4}
            disabled={disabled}
          />
          <button type="submit" disabled={!prompt.trim() || disabled}>
            {isLoading ? "Working…" : phase.kind === "clarify" ? "Waiting for answer" : "Generate report"}
          </button>
        </form>

        {phase.kind === "idle" && (
          <div className="examples">
            {EXAMPLES.map((ex) => (
              <button key={ex} type="button" onClick={() => setPrompt(ex)}>{ex}</button>
            ))}
          </div>
        )}

        {history.map((qa, i) => (
          <div key={i} className="card">
            <div className="label">Clarification {i + 1}</div>
            <div><b>{qa.question}</b></div>
            <div className="muted">{qa.answer}</div>
          </div>
        ))}

        {phase.kind === "clarify" && (
          <form onSubmit={onSubmitAnswer} className="card highlight">
            <div className="label">Planner needs a bit more</div>
            <div><b>{phase.question}</b></div>
            <textarea
              ref={answerRef}
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              rows={3}
              placeholder="Type your answer…"
            />
            <button type="submit" disabled={!currentAnswer.trim()}>Send answer</button>
          </form>
        )}

        {phase.kind === "loading" && <div className="card">{phase.label}…</div>}

        {phase.kind === "error" && (
          <div className="card error">
            <b>Something went wrong</b>
            <p>{phase.message}</p>
          </div>
        )}

        {phase.kind === "report" && (
          <div className="card">
            <div className="row">
              <h2>Report</h2>
              {pdfHref && (
                <a href={pdfHref} download={phase.pdf_filename ?? "investmind-report.pdf"}>
                  Download PDF
                </a>
              )}
            </div>
            <article className="prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{phase.report_markdown}</ReactMarkdown>
            </article>
          </div>
        )}
      </main>
    </div>
  );
}
