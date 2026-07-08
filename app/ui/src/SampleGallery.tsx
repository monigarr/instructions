import { expectedSummaryClass, SampleScenario } from "./types";

interface SampleGalleryProps {
  samples: SampleScenario[];
  loadingId: string | null;
  activeId: string | null;
  onSelect: (sample: SampleScenario) => void;
}

export default function SampleGallery({ samples, loadingId, activeId, onSelect }: SampleGalleryProps) {
  return (
    <section className="sample-gallery" aria-label="Quick-start sample labels">
      <h2>Try a sample label</h2>
      <p className="sample-gallery-desc">
        One click loads the label image and application data. Covers pass, fail, review, and imperfect-photo paths.
      </p>
      <div className="sample-grid" role="list">
        {samples.map((sample) => (
          <article
            key={sample.id}
            className={`sample-card ${activeId === sample.id ? "sample-card-active" : ""}`}
            role="listitem"
          >
            <div className="sample-thumb-wrap">
              <img
                src={sample.thumbnail_url}
                alt=""
                className="sample-thumb"
                loading="lazy"
              />
            </div>
            <div className="sample-card-body">
              <span className={`outcome-chip ${expectedSummaryClass(sample.expected_summary)}`}>
                {sample.expected_summary.replace("_", " ")}
              </span>
              <span className="category-chip">{sample.category}</span>
              <h3 className="sample-title">{sample.title}</h3>
              <p className="sample-desc">{sample.description}</p>
              <button
                type="button"
                className="btn-sample-card"
                onClick={() => onSelect(sample)}
                disabled={loadingId === sample.id}
                aria-label={`Load sample: ${sample.title}`}
              >
                {loadingId === sample.id ? "Loading…" : "Try this sample"}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
