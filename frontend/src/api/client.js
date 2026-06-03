/**
 * Sends an image/PDF file to the recognition API.
 * Returns the parsed JSON response.
 */
export async function recognizeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/recognize", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || `伺服器錯誤 ${res.status}`);
  }

  return data;
}
