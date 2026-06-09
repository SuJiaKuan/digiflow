import { useRef, useState } from "react";
import { cropDocument, recognizeDocument } from "./api/client.js";
import ResultsPanel from "./components/ResultsPanel.jsx";
import UploadZone from "./components/UploadZone.jsx";

const MODES = [
  { id: "all",       label: "所有模組" },
  { id: "crop",      label: "只跑裁切" },
  { id: "recognize", label: "只跑辨識" },
];

let _id = 0;

export default function App() {
  const [mode, setMode] = useState("all");
  const [items, setItems] = useState([]);

  function patch(id, delta) {
    setItems(prev => prev.map(it => it.id === id ? { ...it, ...delta } : it));
  }

  function handleFiles(fileList) {
    const newItems = Array.from(fileList).map(file => ({
      id: _id++,
      file,
      cropStatus: (mode === "all" || mode === "crop") ? "loading" : "idle",
      cropUrl: null,
      cropError: null,
      recognizeResult: null,
      recognizeError: null,
    }));

    setItems(prev => [...prev, ...newItems]);

    newItems.forEach(({ id, file }) => {
      if (mode === "all" || mode === "crop") {
        cropDocument(file)
          .then(url => patch(id, { cropUrl: url, cropStatus: "success" }))
          .catch(err => patch(id, { cropError: err.message, cropStatus: "error" }));
      }
      if (mode === "all" || mode === "recognize") {
        recognizeDocument(file)
          .then(data => patch(id, { recognizeResult: data }))
          .catch(err => patch(id, { recognizeError: err.message }));
      }
    });
  }

  if (items.length === 0) {
    return (
      <div className="app">
        <AppHeader />
        <main className="app-main">
          <div className="upload-wrapper">
            <ModeSelector mode={mode} onChange={setMode} />
            <UploadZone onFiles={handleFiles} />
          </div>
        </main>
      </div>
    );
  }

  const showCrop = mode === "all" || mode === "crop";
  const showRecognize = mode === "all" || mode === "recognize";

  function isBusy(item) {
    return (showCrop && item.cropStatus === "loading") ||
           (showRecognize && !item.recognizeResult && !item.recognizeError);
  }

  const busyItems = items.filter(isBusy);
  const doneCount = items.length - busyItems.length;

  return (
    <div className="app">
      <AppHeader />
      <div className="multi-toolbar">
        <ModeSelector mode={mode} onChange={setMode} />
        <div className="multi-toolbar__right">
          {busyItems.length > 0 ? (
            <div className="progress-banner">
              <span className="spinner spinner--sm" />
              <span>
                正在處理：<strong>{busyItems[0].file.name}</strong>
                {items.length > 1 && `（${doneCount} / ${items.length} 完成）`}
              </span>
            </div>
          ) : (
            <span className="done-badge">✓ 全部完成（{items.length} 個檔案）</span>
          )}
          <AddFilesButton onFiles={handleFiles} />
          <button className="btn-secondary" onClick={() => setItems([])}>清除全部</button>
        </div>
      </div>
      <main className="app-main app-main--multi">
        {items.map(item => (
          <ResultsPanel
            key={item.id}
            file={item.file}
            results={item.recognizeResult}
            recognizeError={item.recognizeError}
            cropStatus={item.cropStatus}
            cropUrl={item.cropUrl}
            cropError={item.cropError}
            mode={mode}
            onReset={() => setItems(prev => prev.filter(it => it.id !== item.id))}
          />
        ))}
      </main>
    </div>
  );
}

function AddFilesButton({ onFiles }) {
  const inputRef = useRef(null);
  return (
    <>
      <button className="btn-primary" onClick={() => inputRef.current.click()}>
        + 新增檔案
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.pdf"
        multiple
        onChange={e => {
          const files = Array.from(e.target.files);
          if (files.length) onFiles(files);
          e.target.value = "";
        }}
        style={{ display: "none" }}
      />
    </>
  );
}

function ModeSelector({ mode, onChange }) {
  return (
    <div className="mode-selector">
      {MODES.map(({ id, label }) => (
        <button
          key={id}
          className={`mode-btn${mode === id ? " mode-btn--active" : ""}`}
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function AppHeader() {
  return (
    <header className="app-header">
      <span className="app-header__logo">DigiFlow</span>
      <span className="app-header__subtitle">數流智動辨識平台</span>
    </header>
  );
}
