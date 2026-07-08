import { FIELD_LABELS, FieldVerdict, statusClass } from "./types";

interface VerdictTableProps {
  verdicts: FieldVerdict[];
  highlightBoldReview?: boolean;
}

export default function VerdictTable({ verdicts, highlightBoldReview }: VerdictTableProps) {
  return (
    <table className="verdict-table">
      <thead>
        <tr>
          <th scope="col">Field</th>
          <th scope="col">Application</th>
          <th scope="col">Label</th>
          <th scope="col">Verdict</th>
        </tr>
      </thead>
      <tbody>
        {verdicts.map((v) => {
          const isBoldReview =
            highlightBoldReview &&
            v.field === "government_warning" &&
            v.status === "needs_review" &&
            v.reason.toLowerCase().includes("bold");
          return (
            <tr key={v.field} className={statusClass(v.status)}>
              <td>{FIELD_LABELS[v.field] || v.field}</td>
              <td>{v.application_value ?? "—"}</td>
              <td>{v.label_value ?? "—"}</td>
              <td>
                <span className={`badge ${statusClass(v.status)}`}>{v.status.replace("_", " ")}</span>
                <small>{v.reason}</small>
                {isBoldReview && (
                  <span className="visual-check-badge" role="note">
                    Visual check — confirm bold header on label image
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
