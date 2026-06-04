export default function CropPanel({ status, dataUrl, error }) {
  return (
    <div className="crop-panel">
      <p className="col-label">表格偵測</p>

      {status === "loading" && (
        <div className="crop-panel__placeholder">
          <span className="spinner" />
          <span className="crop-panel__hint">Gemma 4 偵測中…</span>
        </div>
      )}

      {status === "error" && (
        <div className="crop-panel__placeholder crop-panel__placeholder--error">
          裁切失敗：{error}
        </div>
      )}

      {status === "success" && dataUrl && (
        <img src={dataUrl} alt="裁切維修明細" className="crop-image" />
      )}
    </div>
  );
}
