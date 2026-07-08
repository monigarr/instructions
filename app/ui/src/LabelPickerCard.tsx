import { expectedSummaryClass, FixtureLabel } from "./types";

interface LabelPickerCardProps {
  labels: FixtureLabel[];
  selectedId: string;
  loading: boolean;
  activeId: string | null;
  onSelectId: (id: string) => void;
  onLoad: () => void;
}

function formatLabelId(id: string): string {
  return id.replace(/_/g, " ");
}

export default function LabelPickerCard({
  labels,
  selectedId,
  loading,
  activeId,
  onSelectId,
  onLoad,
}: LabelPickerCardProps) {
  const selected = labels.find((label) => label.id === selectedId);
  const active = labels.find((label) => label.id === activeId);

  return (
    <section className="label-picker-card" aria-label="Browse all fixture labels">
      <h2>Browse all label fixtures</h2>
      <p className="label-picker-desc">
        Choose any label from the fixture library to load its image and application data. Expected
        outcome is shown below when catalog metadata is available.
      </p>
      <div className="label-picker-controls">
        <label className="label-picker-field" htmlFor="fixture-label-select">
          Label image
          <select
            id="fixture-label-select"
            className="label-picker-select"
            value={selectedId}
            onChange={(e) => onSelectId(e.target.value)}
            disabled={loading || labels.length === 0}
          >
            {labels.length === 0 ? (
              <option value="">No labels available</option>
            ) : (
              <>
                <option value="">Select a label…</option>
                {labels.map((label) => (
                  <option key={label.id} value={label.id}>
                    {formatLabelId(label.id)}
                  </option>
                ))}
              </>
            )}
          </select>
        </label>
        <button
          type="button"
          className="btn-secondary label-picker-load"
          onClick={onLoad}
          disabled={loading || !selectedId}
          aria-label={selectedId ? `Load label ${formatLabelId(selectedId)}` : "Load selected label"}
        >
          {loading ? "Loading…" : "Load label"}
        </button>
      </div>
      {selected?.expected_summary && (
        <p className="label-picker-outcome">
          Expected outcome for selection:{" "}
          <span className={`outcome-chip ${expectedSummaryClass(selected.expected_summary)}`}>
            {selected.expected_summary.replace("_", " ")}
          </span>
        </p>
      )}
      {activeId && (
        <p className="label-picker-active" aria-live="polite">
          Loaded: <strong>{formatLabelId(activeId)}</strong>
          {active?.expected_summary && (
            <>
              {" "}
              —{" "}
              <span className={`outcome-chip ${expectedSummaryClass(active.expected_summary)}`}>
                {active.expected_summary.replace("_", " ")}
              </span>
            </>
          )}
        </p>
      )}
    </section>
  );
}
