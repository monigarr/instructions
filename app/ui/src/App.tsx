import { useCallback, useEffect, useState } from "react";
import {
  BatchProgress,
  DEFAULT_APPLICATION,
  FIELD_LABELS,
  VerificationResult,
} from "./types";

type Tab = "single" | "batch";

const API_BASE = import.meta.env.VITE_API_URL || "";

function statusClass(status: string): string {
  if (status === "match" || status === "passed") return "status-pass";
  if (status === "mismatch" || status === "failed") return "status-fail";
  return "status-review";
}

export default function App() {
  const [tab, setTab] = useState<Tab>("single");
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [applicationJson, setApplicationJson] = useState(
    JSON.stringify(DEFAULT_APPLICATION, null, 2)
  );
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [batchImages, setBatchImages] = useState<File[]>([]);
  const [batchManifest, setBatchManifest] = useState<File | null>(null);
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);

  useEffect(() => {
    if (!image) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(image);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  const onVerifySingle = useCallback(async () => {
    setError(null);
    setResult(null);
    if (!image) {
      setError("Please upload a label image first.");
      return;
    }
    let appData: object;
    try {
      appData = JSON.parse(applicationJson);
    } catch {
      setError("Application data must be valid JSON.");
      return;
    }
    setLoading(true);
    try {
      const form = new FormData();
      form.append("image", image);
      form.append("application", JSON.stringify(appData));
      const res = await fetch(`${API_BASE}/verify`, { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || res.statusText);
      }
      const data: VerificationResult = await res.json();
      setResult(data);
      if (data.errors?.length && !data.verdicts?.length) {
        setError(data.errors.join(" "));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  }, [image, applicationJson]);

  const pollBatch = useCallback(async (id: string) => {
    const res = await fetch(`${API_BASE}/batch/${id}`);
    if (!res.ok) return;
    const data: BatchProgress = await res.json();
    setBatchProgress(data);
    if (!data.finished) {
      setTimeout(() => pollBatch(id), 800);
    }
  }, []);

  const onVerifyBatch = useCallback(async () => {
    setError(null);
    setBatchProgress(null);
    if (!batchImages.length) {
      setError("Please select label images for batch verification.");
      return;
    }
    setLoading(true);
    try {
      const form = new FormData();
      let manifest: object[];
      if (batchManifest) {
        const text = await batchManifest.text();
        if (batchManifest.name.endsWith(".csv")) {
          form.append("manifest_csv", batchManifest);
          batchImages.forEach((f) => form.append("images", f));
          form.append("async_mode", "true");
          const res = await fetch(`${API_BASE}/batch/verify-csv`, { method: "POST", body: form });
          if (!res.ok) throw new Error(await res.text());
          const { batch_id } = await res.json();
          setBatchId(batch_id);
          pollBatch(batch_id);
          return;
        }
        manifest = JSON.parse(text);
      } else {
        manifest = batchImages.map((f) => ({
          ...DEFAULT_APPLICATION,
          label_id: f.name.replace(/\.[^.]+$/, ""),
        }));
      }
      form.append("manifest", JSON.stringify(manifest));
      batchImages.forEach((f) => form.append("images", f));
      form.append("async_mode", "true");
      const res = await fetch(`${API_BASE}/batch/verify`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const { batch_id } = await res.json();
      setBatchId(batch_id);
      pollBatch(batch_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Batch verification failed.");
    } finally {
      setLoading(false);
    }
  }, [batchImages, batchManifest, pollBatch]);

  return (
    <div className="app">
      <header className="header">
        <h1>LabelForge</h1>
        <p className="subtitle">TTB Alcohol Label Verification — upload a label, compare to application data</p>
      </header>

      <nav className="tabs">
        <button
          type="button"
          className={tab === "single" ? "tab active" : "tab"}
          onClick={() => setTab("single")}
        >
          Verify One Label
        </button>
        <button
          type="button"
          className={tab === "batch" ? "tab active" : "tab"}
          onClick={() => setTab("batch")}
        >
          Batch Verify
        </button>
      </nav>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {tab === "single" && (
        <section className="panel">
          <div className="grid-2">
            <div>
              <h2>1. Upload label image</h2>
              <label className="upload-zone">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => setImage(e.target.files?.[0] ?? null)}
                />
                {preview ? (
                  <img src={preview} alt="Label preview" className="preview" />
                ) : (
                  <span>Click or drag a label photo (PNG / JPEG)</span>
                )}
              </label>

              <h2>2. Application data</h2>
              <textarea
                className="json-input"
                rows={14}
                value={applicationJson}
                onChange={(e) => setApplicationJson(e.target.value)}
                aria-label="Application JSON"
              />
            </div>

            <div>
              <button
                type="button"
                className="btn-primary"
                onClick={onVerifySingle}
                disabled={loading}
              >
                {loading ? "Verifying…" : "Verify Label"}
              </button>

              {result && (
                <div className="results">
                  <div className={`summary ${statusClass(result.summary)}`}>
                    <strong>Summary:</strong> {result.summary.replace("_", " ")} —{" "}
                    {result.elapsed_ms.toFixed(0)} ms
                  </div>
                  {result.errors?.length > 0 && (
                    <ul className="errors-list">
                      {result.errors.map((err) => (
                        <li key={err}>{err}</li>
                      ))}
                    </ul>
                  )}
                  <table className="verdict-table">
                    <thead>
                      <tr>
                        <th>Field</th>
                        <th>Application</th>
                        <th>Label</th>
                        <th>Verdict</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.verdicts.map((v) => (
                        <tr key={v.field} className={statusClass(v.status)}>
                          <td>{FIELD_LABELS[v.field] || v.field}</td>
                          <td>{v.application_value ?? "—"}</td>
                          <td>{v.label_value ?? "—"}</td>
                          <td>
                            <span className={`badge ${statusClass(v.status)}`}>{v.status}</span>
                            <small>{v.reason}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {tab === "batch" && (
        <section className="panel">
          <h2>1. Upload multiple labels</h2>
          <label className="upload-zone">
            <input
              type="file"
              accept="image/png,image/jpeg"
              multiple
              onChange={(e) => setBatchImages(Array.from(e.target.files ?? []))}
            />
            <span>
              {batchImages.length
                ? `${batchImages.length} image(s) selected`
                : "Select multiple label images"}
            </span>
          </label>

          <h2>2. Optional manifest (JSON or CSV)</h2>
          <label className="upload-zone small">
            <input
              type="file"
              accept=".json,.csv"
              onChange={(e) => setBatchManifest(e.target.files?.[0] ?? null)}
            />
            <span>
              {batchManifest
                ? batchManifest.name
                : "Optional — defaults match filename to label_id"}
            </span>
          </label>

          <button
            type="button"
            className="btn-primary"
            onClick={onVerifyBatch}
            disabled={loading}
          >
            {loading ? "Starting batch…" : "Start Batch Verification"}
          </button>

          {batchProgress && (
            <div className="batch-results">
              <h3>
                Batch {batchId} — {batchProgress.completed}/{batchProgress.total} complete
              </h3>
              <div className="batch-stats">
                <span className="status-pass">Passed: {batchProgress.passed}</span>
                <span className="status-fail">Failed: {batchProgress.failed}</span>
                <span className="status-review">Needs review: {batchProgress.needs_review}</span>
                <span>Errors: {batchProgress.errors}</span>
              </div>
              {!batchProgress.finished && <p className="progress-note">Processing…</p>}
              <ul className="batch-list">
                {batchProgress.items.map((item) => (
                  <li key={item.label_id} className={statusClass(item.status)}>
                    <strong>{item.label_id}</strong> — {item.status}
                    {item.error && <em> {item.error}</em>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <footer className="footer">
        <p>Standalone prototype — no COLA integration. Human agents retain final judgment.</p>
      </footer>
    </div>
  );
}
