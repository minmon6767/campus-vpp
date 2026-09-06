export default function RecommendationPanel({ recommendation }) {
  if (!recommendation) return null;
  const { action, magnitude_kw, reason, confidence } = recommendation;

  return (
    <div className="panel">
      <h2>
        Dispatch Recommendation
        <span className={`confidence-pill ${confidence}`}>{confidence} CONFIDENCE</span>
      </h2>
      <div className="rec-card">
        <div className={`rec-action ${action}`}>
          {action}
          {magnitude_kw > 0 ? ` ${magnitude_kw} kW` : ""}
        </div>
        <div className="rec-details">
          <div className="reason">{reason}</div>
        </div>
      </div>
    </div>
  );
}
