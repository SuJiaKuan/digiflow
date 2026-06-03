import RecognitionTable from "./RecognitionTable.jsx";

export default function ResultsPanel({ file, results, onReset }) {
  const imageUrl = file ? URL.createObjectURL(file) : null;

  return (
    <div className="results-panel">
      <div className="results-panel__toolbar">
        <span className="results-panel__filename">{results.filename}</span>
        <button className="btn-secondary" onClick={onReset}>
          重新上傳
        </button>
      </div>

      <div className="results-panel__body">
        <div className="results-panel__image-col">
          <p className="col-label">原始文件</p>
          {imageUrl && (
            <img
              src={imageUrl}
              alt="原始文件"
              className="original-image"
            />
          )}
        </div>

        <div className="results-panel__data-col">
          <p className="col-label">辨識結果</p>
          <RecognitionTable
            rows={results["辨識結果"]}
            stats={results["統計表"]}
          />
        </div>
      </div>
    </div>
  );
}
