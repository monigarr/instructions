import { useCallback, useEffect, useState } from "react";
import LabelPickerCard from "./LabelPickerCard";
import LatencyBadge from "./LatencyBadge";
import SampleGallery from "./SampleGallery";
import { scrollToVerifyWorkspace } from "./scroll";
import VerdictTable from "./VerdictTable";
import {
  BatchProgress,
  DEFAULT_APPLICATION,
  FixtureLabel,
  SampleScenario,
  VerificationResult,
  computeP95,
  statusClass,
} from "./types";

type Tab = "single" | "batch";

const API_BASE = import.meta.env.VITE_API_URL || "";

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
  const [batchP95, setBatchP95] = useState<number | null>(null);

  const [samples, setSamples] = useState<SampleScenario[]>([]);
  const [sampleLoadingId, setSampleLoadingId] = useState<string | null>(null);
  const [activeSampleId, setActiveSampleId] = useState<string | null>(null);

  const [fixtureLabels, setFixtureLabels] = useState<FixtureLabel[]>([]);
  const [pickerLabelId, setPickerLabelId] = useState("");
  const [pickerLoading, setPickerLoading] = useState(false);
  const [activePickerLabelId, setActivePickerLabelId] = useState<string | null>(null);
  const [demoBatchTotal, setDemoBatchTotal] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/samples`)
      .then((r) => r.json())
      .then((data) => setSamples(data.samples ?? []))
      .catch(() => setSamples([]));
    fetch(`${API_BASE}/labels`)
      .then((r) => r.json())
      .then((data) => setFixtureLabels(data.labels ?? []))
      .catch(() => setFixtureLabels([]));
    fetch(`${API_BASE}/samples/batch/demo`)
      .then((r) => r.json())
      .then((data) => {
        const total = typeof data.total === "number" ? data.total : null;
        setDemoBatchTotal(total);
      })
      .catch(() => setDemoBatchTotal(null));
  }, []);

  useEffect(() => {
    if (!image) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(image);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  const loadSample = useCallback(async (sample: SampleScenario) => {
    setSampleLoadingId(sample.id);
    setError(null);
    setResult(null);
    try {
      const [imgRes, appRes] = await Promise.all([
        fetch(`${API_BASE}${sample.thumbnail_url}`),
        fetch(`${API_BASE}${sample.application_url}`),
      ]);
      if (!imgRes.ok || !appRes.ok) throw new Error("Could not load sample assets.");
      const blob = await imgRes.blob();
      const appData = await appRes.json();
      const file = new File([blob], `${sample.id}.png`, { type: "image/png" });
      setImage(file);
      setApplicationJson(JSON.stringify(appData, null, 2));
      setActiveSampleId(sample.id);
      setActivePickerLabelId(null);
      scrollToVerifyWorkspace();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sample.");
    } finally {
      setSampleLoadingId(null);
    }
  }, []);

  const loadPickerLabel = useCallback(async () => {
    if (!pickerLabelId) return;
    setPickerLoading(true);
    setError(null);
    setResult(null);
    try {
      const label = fixtureLabels.find((l) => l.id === pickerLabelId);
      if (!label) throw new Error("Selected label not found.");
      const imgRes = await fetch(`${API_BASE}${label.image_url}`);
      if (!imgRes.ok) throw new Error("Could not load label image.");
      const appRes = await fetch(`${API_BASE}${label.application_url}`);
      let appData: object;
      if (appRes.ok) {
        appData = await appRes.json();
      } else {
        appData = { ...DEFAULT_APPLICATION, label_id: pickerLabelId };
      }
      const blob = await imgRes.blob();
      const file = new File([blob], `${pickerLabelId}.png`, { type: "image/png" });
      setImage(file);
      setApplicationJson(JSON.stringify(appData, null, 2));
      setActivePickerLabelId(pickerLabelId);
      setActiveSampleId(null);
      scrollToVerifyWorkspace();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load label.");
    } finally {
      setPickerLoading(false);
    }
  }, [pickerLabelId, fixtureLabels]);

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
    const summaryRes = await fetch(`${API_BASE}/batch/${id}?summary_only=true`);
    if (!summaryRes.ok) return;
    const summary: BatchProgress = await summaryRes.json();
    setBatchProgress(summary);
    if (!summary.finished) {
      setTimeout(() => pollBatch(id), 800);
      return;
    }
    const fullRes = await fetch(`${API_BASE}/batch/${id}`);
    if (!fullRes.ok) return;
    const full: BatchProgress = await fullRes.json();
    setBatchProgress(full);
    const latencies = full.items
      .map((item) => item.result?.elapsed_ms)
      .filter((ms): ms is number => typeof ms === "number");
    setBatchP95(latencies.length ? computeP95(latencies) : null);
  }, []);

  const startBatch = useCallback(
    async (manifest: object[], images: File[]) => {
      setError(null);
      setBatchProgress(null);
      setBatchP95(null);
      setLoading(true);
      try {
        const form = new FormData();
        form.append("manifest", JSON.stringify(manifest));
        images.forEach((f) => form.append("images", f));
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
    },
    [pollBatch]
  );

  const onVerifyBatch = useCallback(async () => {
    if (!batchImages.length) {
      setError("Please select label images for batch verification.");
      return;
    }
    let manifest: object[];
    if (batchManifest) {
      const text = await batchManifest.text();
      if (batchManifest.name.endsWith(".csv")) {
        setError("CSV batch via file upload: use JSON manifest or quick-start buttons.");
        return;
      }
      manifest = JSON.parse(text);
    } else {
      manifest = batchImages.map((f) => ({
        ...DEFAULT_APPLICATION,
        label_id: f.name.replace(/\.[^.]+$/, ""),
      }));
    }
    await startBatch(manifest, batchImages);
  }, [batchImages, batchManifest, startBatch]);

  const runDemoBatch = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const meta = await fetch(`${API_BASE}/samples/batch/demo`).then((r) => r.json());
      const images: File[] = [];
      for (const id of meta.image_ids as string[]) {
        const res = await fetch(`${API_BASE}/samples/${id}/image`);
        if (!res.ok) continue;
        const blob = await res.blob();
        images.push(new File([blob], `${id}.png`, { type: "image/png" }));
      }
      await startBatch(meta.manifest, images);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo batch failed.");
      setLoading(false);
    }
  }, [startBatch]);

  const runScaleBatch = useCallback(
    async (size: 200 | 300) => {
      const confirmed = window.confirm(
        `Run ${size}-label scale test? This may take several minutes depending on server capacity.`
      );
      if (!confirmed) return;
      setError(null);
      setLoading(true);
      try {
        const meta = await fetch(`${API_BASE}/samples/batch/scale/${size}`).then((r) => r.json());
        const imageCache: Record<string, Blob> = {};
        const images: File[] = [];
        for (const entry of meta.manifest as Array<{ label_id: string }>) {
          const labelId = entry.label_id;
          const fallbackStem = labelId.replace(/_\d{3}$/, "");
          const cacheKey = fallbackStem;
          if (!imageCache[cacheKey]) {
            let res = await fetch(`${API_BASE}/labels/${labelId}/image`);
            if (!res.ok && fallbackStem !== labelId) {
              res = await fetch(`${API_BASE}/labels/${fallbackStem}/image`);
            }
            if (!res.ok) continue;
            imageCache[cacheKey] = await res.blob();
          }
          const blob = imageCache[cacheKey];
          if (blob) {
            images.push(new File([blob], `${labelId}.png`, { type: "image/png" }));
          }
        }
        await startBatch(meta.manifest, images);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Scale batch failed.");
        setLoading(false);
      }
    },
    [startBatch]
  );

  return (
    <div className="app">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <header className="header">
          <h1>LabelForge</h1>
          <p className="subtitle">TTB alcohol label verification — upload a label, compare to application data</p>
        <p className="credit-note">
          Built to spec using AI First / AI Native software architecture and engineering techniques by
          Monica Peters from{" "}
            <a
              href="https://github.com/treasurytakehome-rgb/instructions"
              target="_blank"
              rel="noopener noreferrer"
              className="usa-link"
            >
              client requirements
            </a>
            .
          </p>
        </header>

      <nav className="tabs" aria-label="Verification mode">
        <button
          type="button"
          className={tab === "single" ? "tab active" : "tab"}
          onClick={() => setTab("single")}
          aria-selected={tab === "single"}
        >
          Verify One Label
        </button>
        <button
          type="button"
          className={tab === "batch" ? "tab active" : "tab"}
          onClick={() => setTab("batch")}
          aria-selected={tab === "batch"}
        >
          Batch Verify
        </button>
      </nav>

      {error && (
        <div className="usa-alert usa-alert--error" role="alert">
          <div className="usa-alert__body">
            <p className="usa-alert__text">{error}</p>
          </div>
        </div>
      )}

      <main id="main-content">
        {tab === "single" && (
          <section className="panel">
            <div id="verify-workspace" className="grid-2">
              <div>
                <h2>1. Upload label image</h2>
                <label className="upload-zone" aria-label="Upload label image">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(e) => {
                      setImage(e.target.files?.[0] ?? null);
                      setActiveSampleId(null);
                      setActivePickerLabelId(null);
                    }}
                  />
                  {preview ? (
                    <img src={preview} alt="Label preview" className="preview" />
                  ) : (
                    <span>Click or drag a label photo (PNG / JPEG / WebP)</span>
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

                <div aria-live="polite" aria-atomic="true">
                  {result && (
                    <div className="results">
                      <div className={`summary ${statusClass(result.summary)}`}>
                        <strong>Summary:</strong> {result.summary.replace("_", " ")}
                        <LatencyBadge
                          elapsedMs={result.elapsed_ms}
                          showWarning={result.latency_warning}
                        />
                      </div>
                      {result.errors?.length > 0 && (
                        <ul className="errors-list">
                          {result.errors.map((err) => (
                            <li key={err}>{err}</li>
                          ))}
                        </ul>
                      )}
                      <VerdictTable verdicts={result.verdicts} highlightBoldReview />
                    </div>
                  )}
                </div>
              </div>
            </div>

            <SampleGallery
              samples={samples}
              loadingId={sampleLoadingId}
              activeId={activeSampleId}
              onSelect={loadSample}
            />

            <LabelPickerCard
              labels={fixtureLabels}
              selectedId={pickerLabelId}
              loading={pickerLoading}
              activeId={activePickerLabelId}
              onSelectId={setPickerLabelId}
              onLoad={loadPickerLabel}
            />
          </section>
        )}

        {tab === "batch" && (
          <section className="panel">
            <h2>Quick-start batch runs</h2>
            <p className="batch-helper">
              Run pre-built manifests with one click — no manual file selection required.
            </p>
            <div className="batch-quick-start">
              <button type="button" className="btn-secondary" onClick={runDemoBatch} disabled={loading}>
                {demoBatchTotal != null
                  ? `Run ${demoBatchTotal}-label demo batch`
                  : "Run demo batch"}
              </button>
              <button type="button" className="btn-secondary" onClick={() => runScaleBatch(200)} disabled={loading}>
                Run 200-label scale test
              </button>
              <button type="button" className="btn-secondary" onClick={() => runScaleBatch(300)} disabled={loading}>
                Run 300-label scale test
              </button>
            </div>

            <h2>Or upload manually</h2>
            <label className="upload-zone" aria-label="Upload multiple label images">
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

            <h2>Optional manifest (JSON)</h2>
            <label className="upload-zone small" aria-label="Upload batch manifest JSON">
              <input
                type="file"
                accept=".json"
                onChange={(e) => setBatchManifest(e.target.files?.[0] ?? null)}
              />
              <span>
                {batchManifest ? batchManifest.name : "Optional — defaults match filename to label_id"}
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

            <div aria-live="polite" aria-atomic="true">
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
                  {batchP95 !== null && batchProgress.finished && (
                    <p className="batch-latency">
                      Batch P95 latency: <LatencyBadge elapsedMs={batchP95} />
                    </p>
                  )}
                  {!batchProgress.finished && <p className="progress-note">Processing…</p>}
                  {batchProgress.items.length > 0 && (
                    <ul className="batch-list">
                      {batchProgress.items.map((item) => (
                        <li key={item.label_id} className={statusClass(item.status)}>
                          <strong>{item.label_id}</strong> — {item.status}
                          {item.error && <em> {item.error}</em>}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Standalone prototype — no COLA integration. Human agents retain final judgment.</p>
      </footer>
    </div>
  );
}
