"use client";

import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileText,
  GitBranch,
  Loader2,
  MessageSquareText,
  Search,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

type RetrievedChunk = {
  text: string;
  source: string;
  page: number;
  chunk_index: number;
  score: number | null;
};

type QueryResponse = {
  answer: string;
  citations: RetrievedChunk[];
  rewritten_question: string | null;
  attempts: number;
  evidence_supported: boolean;
  flow: string[];
};

type ApiState = "checking" | "online" | "offline";

const sampleQuestions = [
  "Can someone get urgent protection before the tribunal exists?",
  "What does this document say about Indian tax law?",
];

const flowSteps = [
  {
    id: "retrieve",
    label: "Retrieve",
    detail: "Search the indexed legal chunks",
    icon: Search,
  },
  {
    id: "grade_evidence",
    label: "Grade",
    detail: "Check if excerpts support the question",
    icon: ShieldCheck,
  },
  {
    id: "rewrite_query",
    label: "Rewrite",
    detail: "Retry with legal search language if weak",
    icon: GitBranch,
  },
  {
    id: "generate_answer",
    label: "Generate",
    detail: "Answer from cited context only",
    icon: Sparkles,
  },
  {
    id: "refuse",
    label: "Refuse",
    detail: "Return no citations when unsupported",
    icon: XCircle,
  },
];

function truncate(text: string, maxLength: number) {
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength).trim()}...`;
}

function formatScore(score: number | null) {
  if (score === null) {
    return "n/a";
  }

  return score.toFixed(3);
}

export default function Home() {
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [question, setQuestion] = useState(sampleQuestions[0]);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function checkHealth() {
    try {
      const response = await fetch("/api/health");
      setApiState(response.ok ? "online" : "offline");
    } catch {
      setApiState("offline");
    }
  }

  async function runQuery(nextQuestion = question) {
    const trimmedQuestion = nextQuestion.trim();

    if (trimmedQuestion.length < 3) {
      return;
    }

    setQuestion(trimmedQuestion);
    setIsQuerying(true);
    setError(null);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setResult(await response.json());
    } catch (queryError) {
      setError(queryError instanceof Error ? queryError.message : "Query failed.");
    } finally {
      setIsQuerying(false);
    }
  }

  useEffect(() => {
    checkHealth();
  }, []);

  const isRefusal = Boolean(result?.flow.includes("refuse"));
  const activeFlow = new Set(result?.flow ?? []);

  return (
    <main className="workspace">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <BookOpen size={22} />
          </span>
          <div>
            <p>Legal RAG Workbench</p>
            <h1>ICC Arbitration Rules Inspector</h1>
          </div>
        </div>

        <div className="topbar-actions">
          <span className={`status ${apiState}`}>
            {apiState === "online" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            API {apiState}
          </span>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
          <a href="http://127.0.0.1:8000/document" target="_blank" rel="noreferrer">
            PDF
          </a>
        </div>
      </header>

      <section className="content-grid">
        <aside className="query-column">
          <section className="panel query-panel">
            <div className="panel-kicker">
              <MessageSquareText size={18} />
              Query
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                runQuery();
              }}
            >
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                spellCheck
                aria-label="Legal question"
              />
              <div className="button-row">
                <button type="submit" disabled={isQuerying}>
                  {isQuerying ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
                  Run query
                </button>
                <button
                  type="button"
                  className="button-secondary"
                  disabled={isQuerying}
                  onClick={() => runQuery(sampleQuestions[3])}
                >
                  <ShieldCheck size={18} />
                  Test refusal
                </button>
              </div>
            </form>
          </section>

          <section className="panel flow-panel">
            <div className="panel-kicker">
              <GitBranch size={18} />
              LangGraph path
            </div>
            <div className="flow-list">
              {flowSteps.map((step, index) => {
                const Icon = step.icon;
                const isActive = activeFlow.has(step.id);
                const isWarn = step.id === "refuse" && isActive;

                return (
                  <div
                    className={`flow-item ${isActive ? "active" : ""} ${isWarn ? "warn" : ""}`}
                    key={step.id}
                  >
                    <span className="flow-index">{index + 1}</span>
                    <Icon size={18} />
                    <div>
                      <strong>{step.label}</strong>
                      <small>{step.detail}</small>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </aside>

        <section className="main-column">
          <section className={`answer-hero ${isRefusal ? "refusal" : ""}`}>
            <div className="answer-header">
              <div>
                <p>Grounded response</p>
                <h2>{result ? "Answer generated" : "Ready to inspect"}</h2>
              </div>
              <div className="answer-state">
                {isQuerying ? (
                  <>
                    <Loader2 className="spin" size={18} />
                    Running
                  </>
                ) : result?.evidence_supported ? (
                  <>
                    <CheckCircle2 size={18} />
                    Supported
                  </>
                ) : result ? (
                  <>
                    <AlertTriangle size={18} />
                    Weak evidence
                  </>
                ) : (
                  <>
                    <ArrowRight size={18} />
                    Awaiting query
                  </>
                )}
              </div>
            </div>

            <p className="answer-text">
              {error ??
                result?.answer ??
                "Ask a question to see the retrieval trace, the generated legal answer, and the exact chunks used as citations."}
            </p>

            <div className="metric-strip">
              <div>
                <span>Attempts</span>
                <strong>{result?.attempts ?? 0}</strong>
              </div>
              <div>
                <span>Citations</span>
                <strong>{result?.citations.length ?? 0}</strong>
              </div>
              <div>
                <span>Rewritten query</span>
                <strong>{result?.rewritten_question ?? "None"}</strong>
              </div>
            </div>
          </section>

          <section className="panel citations-panel">
            <div className="panel-title-row">
              <div className="panel-kicker">
                <FileText size={18} />
                Cited chunks
              </div>
              <span>{result?.citations.length ?? 0} returned</span>
            </div>

            <div className="citation-grid">
              {result?.citations.length ? (
                result.citations.map((citation) => (
                  <article className="citation-card" key={`${citation.source}-${citation.page}-${citation.chunk_index}`}>
                    <div className="citation-topline">
                      <span>{citation.source}</span>
                      <span>p. {citation.page}</span>
                      <span>chunk {citation.chunk_index}</span>
                      <span>distance {formatScore(citation.score)}</span>
                    </div>
                    <p>{truncate(citation.text, 680)}</p>
                  </article>
                ))
              ) : (
                <div className="empty-state">
                  {result ? "No citations returned for this answer." : "Run a query to populate citations."}
                </div>
              )}
            </div>
          </section>
        </section>

        <aside className="inspector-column">
          <section className="panel document-panel">
            <div className="panel-kicker">
              <FileText size={18} />
              Indexed PDF
            </div>
            <iframe src="/api/document" title="Indexed legal PDF" />
          </section>
        </aside>
      </section>
    </main>
  );
}
