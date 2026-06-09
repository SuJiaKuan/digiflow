import CropPanel from "./CropPanel.jsx";
import EvaluationPanel from "./EvaluationPanel.jsx";
import RecognitionTable from "./RecognitionTable.jsx";

export default function ResultsPanel({
  file, results, recognizeError,
  cropStatus, cropUrl, cropError,
  mode, onReset,
}) {
  const imageUrl = file ? URL.createObjectURL(file) : null;
  const showCrop = mode === "all" || mode === "crop";
  const showRecognize = mode === "all" || mode === "recognize";
  const twoCol = !(showCrop && showRecognize);

  return (
    <div className="results-panel">
      <div className="results-panel__toolbar">
        <span className="results-panel__filename">{file?.name}</span>
        <button className="btn-secondary" onClick={onReset}>移除</button>
      </div>

      <div className={`results-panel__body${twoCol ? " results-panel__body--2col" : ""}`}>
        <div className="results-panel__image-col">
          <p className="col-label">原始文件</p>
          {imageUrl && <img src={imageUrl} alt="原始文件" className="original-image" />}
        </div>

        {showCrop && (
          <CropPanel status={cropStatus} dataUrl={cropUrl} error={cropError} />
        )}

        {showRecognize && (
          <div className="results-panel__data-col">
            <p className="col-label">辨識結果</p>
            {results ? (
              <>
                <RecognitionTable rows={results["辨識結果"]} stats={results["統計表"]} />
                <EvaluationPanel evaluation={results["evaluation"]} />
              </>
            ) : recognizeError ? (
              <div className="crop-panel__placeholder crop-panel__placeholder--error">
                辨識失敗：{recognizeError}
              </div>
            ) : (
              <div className="crop-panel__placeholder">
                <span className="spinner" />
                <span className="crop-panel__hint">Gemini 辨識中…</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
