import { useRef, useState } from "react";

const ACCEPTED = ".jpg,.jpeg,.png,.pdf";

export default function UploadZone({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  function handleChange(e) {
    const file = e.target.files[0];
    if (file) onFile(file);
  }

  return (
    <div
      className={`upload-zone ${dragging ? "upload-zone--dragging" : ""}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
      aria-label="上傳文件區域"
    >
      <div className="upload-zone__icon">📄</div>
      <p className="upload-zone__primary">拖曳檔案至此，或點擊選擇</p>
      <p className="upload-zone__secondary">支援 JPG、PNG、PDF</p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        onChange={handleChange}
        style={{ display: "none" }}
      />
    </div>
  );
}
