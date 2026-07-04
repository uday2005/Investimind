const BASE = import.meta.env.VITE_INVESTMIND_API_URL as string;

export type RunReportResult =
  | { ok: false; error: string }
  | { ok: true; status: "needs_clarification"; session_id: string; clarification_question: string }
  | { ok: true; status: "report"; report_markdown: string; pdf_base64?: string; pdf_filename?: string };

function renderAnalysis(a: unknown): string {
  if (typeof a === "string") return a;
  if (a && typeof a === "object") {
    const o = a as { content?: string; cited_note_ids?: unknown[] };
    const cites =
      Array.isArray(o.cited_note_ids) && o.cited_note_ids.length
        ? ` _(sources: ${o.cited_note_ids.map((n) => `N${n}`).join(", ")})_`
        : "";
    return `${o.content ?? ""}${cites}`;
  }
  return "";
}

function reportToMarkdown(r: unknown): string {
  if (typeof r === "string") return r;
  if (!r || typeof r !== "object") return "";
  const rep = r as {
    title?: string;
    executive_summary?: unknown;
    sections?: Array<{ requirement?: string; heading?: string; analysis?: unknown }>;
    evidence_limitations?: unknown[];
  };
  const parts: string[] = [];
  if (rep.title) parts.push(`# ${rep.title}`);
  if (rep.executive_summary) parts.push(`## Executive Summary\n\n${renderAnalysis(rep.executive_summary)}`);
  if (Array.isArray(rep.sections)) {
    for (const s of rep.sections) {
      parts.push(`## ${s.heading ?? s.requirement ?? "Section"}\n\n${renderAnalysis(s.analysis)}`);
    }
  }
  if (Array.isArray(rep.evidence_limitations) && rep.evidence_limitations.length) {
    parts.push(
      `## Evidence & Limitations\n\n${rep.evidence_limitations
        .map((l) => `- ${typeof l === "string" ? l : JSON.stringify(l)}`)
        .join("\n")}`,
    );
  }
  return parts.join("\n\n");
}

async function parseResponse(res: Response): Promise<RunReportResult> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return { ok: false, error: `Backend error ${res.status}: ${text.slice(0, 400) || res.statusText}` };
  }
  const json = await res.json();
  if (json.status === "needs_clarification" && json.session_id && json.clarification_question) {
    return {
      ok: true,
      status: "needs_clarification",
      session_id: json.session_id,
      clarification_question: json.clarification_question,
    };
  }
  if (json.status === "report") {
    return {
      ok: true,
      status: "report",
      report_markdown: reportToMarkdown(json.report_markdown),
      pdf_base64: json.pdf_base64,
      pdf_filename: json.pdf_filename ?? "investmind-report.pdf",
    };
  }
  return { ok: false, error: "Unexpected response shape from backend." };
}

export async function startResearch(prompt: string): Promise<RunReportResult> {
  try {
    const res = await fetch(`${BASE}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    return await parseResponse(res);
  } catch (err) {
    return { ok: false, error: `Could not reach backend: ${(err as Error).message}` };
  }
}

export async function answerClarification(session_id: string, answer: string): Promise<RunReportResult> {
  try {
    const res = await fetch(`${BASE}/research/${encodeURIComponent(session_id)}/clarify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    return await parseResponse(res);
  } catch (err) {
    return { ok: false, error: `Could not reach backend: ${(err as Error).message}` };
  }
}
