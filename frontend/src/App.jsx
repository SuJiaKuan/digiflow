import { useState } from "react";
import { recognizeDocument } from "./api/client.js";
import UploadZone from "./components/UploadZone.jsx";
import StatusBanner from "./components/StatusBanner.jsx";
import ResultsPanel from "./components/ResultsPanel.jsx";

export default function App() {
  const [status, setStatus] = useState("idle"); // "idle" | "loading" | "success" | "error"
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  async function handleFile(selectedFile) {
    setFile(selectedFile);
    setStatus("loading");
    setResults(null);
    setErrorMessage(null);

    try {
      const data = await recognizeDocument(selectedFile);
      setResults(data);
      setStatus("success");
    } catch (err) {
      setErrorMessage(err.message);
      setStatus("error");
    }
  }

  function handleReset() {
    setStatus("idle");
    setFile(null);
    setResults(null);
    setErrorMessage(null);
  }

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-header__logo">DigiFlow</span>
        <span className="app-header__subtitle">數流智動辨識平台</span>
      </header>

      <main className="app-main">
        {status === "idle" && <UploadZone onFile={handleFile} />}
        {status === "loading" && <StatusBanner status="loading" />}
        {status === "error" && (
          <>
            <StatusBanner status="error" errorMessage={errorMessage} />
            <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
              <button className="btn-secondary" onClick={handleReset}>
                重新上傳
              </button>
            </div>
          </>
        )}
        {status === "success" && results && (
          <ResultsPanel file={file} results={results} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}
