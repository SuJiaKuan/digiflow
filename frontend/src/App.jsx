import { useState } from "react";
import { cropDocument, recognizeDocument } from "./api/client.js";
import ResultsPanel from "./components/ResultsPanel.jsx";
import UploadZone from "./components/UploadZone.jsx";

const MODES = [
  { id: "all",       label: "所有模組" },
  { id: "crop",      label: "只跑裁切" },
  { id: "recognize", label: "只跑辨識" },
];

export default function App() {
  const [mode, setMode] = useState("all");
  const [file, setFile] = useState(null);
  const [recognizeResult, setRecognizeResult] = useState(null);
  const [recognizeError, setRecognizeError] = useState(null);
  const [cropStatus, setCropStatus] = useState("idle");
  const [cropUrl, setCropUrl] = useState(null);
  const [cropError, setCropError] = useState(null);

  function handleFile(selectedFile) {
    setFile(selectedFile);
    setRecognizeResult(null);
    setRecognizeError(null);
    setCropStatus("idle");
    setCropUrl(null);
    setCropError(null);

    if (mode === "all" || mode === "crop") {
      setCropStatus("loading");
      cropDocument(selectedFile)
        .then((dataUrl) => { setCropUrl(dataUrl); setCropStatus("success"); })
        .catch((err) => { setCropError(err.message); setCropStatus("error"); });
    }

    if (mode === "all" || mode === "recognize") {
      recognizeDocument(selectedFile)
        .then((data) => setRecognizeResult(data))
        .catch((err) => setRecognizeError(err.message));
    }
  }

  function handleReset() {
    setFile(null);
    setRecognizeResult(null);
    setRecognizeError(null);
    setCropStatus("idle");
    setCropUrl(null);
    setCropError(null);
  }

  if (!file) {
    return (
      <div className="app">
        <AppHeader />
        <main className="app-main">
          <div className="upload-wrapper">
            <ModeSelector mode={mode} onChange={setMode} />
            <UploadZone onFile={handleFile} />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <AppHeader />
      <main className="app-main app-main--results">
        <ResultsPanel
          file={file}
          results={recognizeResult}
          recognizeError={recognizeError}
          cropStatus={cropStatus}
          cropUrl={cropUrl}
          cropError={cropError}
          mode={mode}
          onReset={handleReset}
        />
      </main>
    </div>
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
