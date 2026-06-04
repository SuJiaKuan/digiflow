export async function recognizeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/recognize", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `伺服器錯誤 ${res.status}`);
  return data;
}

export async function cropDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/crop", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `伺服器錯誤 ${res.status}`);
  return data.cropped_image; // data URL string
}
