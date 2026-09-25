/**
 * LexPilot Frontend API Service
 */

const API_BASE = "http://127.0.0.1:8000/api";

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE}/samples`);
  return res.json();
}

export async function loadSample(sampleId) {
  const res = await fetch(`${API_BASE}/sample/${sampleId}`);
  if (!res.ok) throw new Error("Failed to load sample");
  return res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Document upload and processing failed");
  return res.json();
}

export async function askQuestion(question, documentId, jurisdiction) {
  const res = await fetch(`${API_BASE}/qa`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      document_id: documentId,
      jurisdiction: jurisdiction || "General / Unspecified",
    }),
  });
  if (!res.ok) throw new Error("Q&A request failed");
  return res.json();
}

export async function compareContracts(docAId, docBId, fileA, fileB) {
  const formData = new FormData();
  if (docAId) formData.append("doc_a_id", docAId);
  if (docBId) formData.append("doc_b_id", docBId);
  if (fileA) formData.append("file_a", fileA);
  if (fileB) formData.append("file_b", fileB);

  const res = await fetch(`${API_BASE}/compare`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Contract comparison failed");
  return res.json();
}

export async function fetchReferenceCorpus() {
  const res = await fetch(`${API_BASE}/corpus`);
  return res.json();
}

export async function updateApiKey(apiKey) {
  const res = await fetch(`${API_BASE}/settings/key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
  return res.json();
}
