export default function StatusBanner({ status, errorMessage }) {
  if (status === "loading") {
    return (
      <div className="status-banner status-banner--loading">
        <span className="spinner" aria-hidden="true" />
        <span>辨識中，請稍候⋯</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="status-banner status-banner--error" role="alert">
        <span>⚠ 辨識失敗：{errorMessage}</span>
      </div>
    );
  }

  return null;
}
