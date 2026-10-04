import keycloak from './keycloak';
import type { AnalysisReport, Campaign, CampaignCreate, DesignerMessage, DesignerResponse, KnowledgeBase, RAGMessage, RAGResponse, SurveyRequest, SurveyResponse } from './types';

async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  // Refresh token if it expires within 30 s
  await keycloak.updateToken(30).catch(() => keycloak.login());
  return fetch(input, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${keycloak.token}`,
    },
  });
}

// ── Campaigns ────────────────────────────────────────────────────────────────

export async function listCampaigns(): Promise<Campaign[]> {
  const res = await authFetch('/campaigns/list_campaigns');
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createCampaign(data: Omit<CampaignCreate, 'allowed_origins'> & { allowed_origins: string[] }): Promise<Campaign> {
  const res = await authFetch('/campaigns/create_campaign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteCampaign(id: string): Promise<void> {
  const res = await authFetch(`/campaigns/delete_campaign/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function generateApiKey(id: string): Promise<Campaign> {
  const res = await authFetch(`/campaigns/${id}/generate_key`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeCampaign(id: string): Promise<AnalysisReport> {
  const res = await authFetch(`/campaigns/${id}/analyze`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalysis(id: string): Promise<AnalysisReport> {
  const res = await authFetch(`/campaigns/${id}/analysis`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function campaignAssist(
  message: string,
  history: DesignerMessage[],
): Promise<DesignerResponse> {
  const res = await authFetch('/campaigns/assist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Knowledge bases ───────────────────────────────────────────────────────────

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const res = await authFetch('/knowledgebases/');
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createCollection(name: string): Promise<{ message: string; collection_id: string }> {
  const res = await authFetch(`/knowledgebases/create_collection?collection_name=${encodeURIComponent(name)}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadDocs(
  file: File,
  collectionId: string,
  chunkSize = 1000,
  chunkOverlap = 50,
): Promise<{ message: string }> {
  const form = new FormData();
  form.append('file', file);
  form.append('collection_id', collectionId);
  form.append('chunk_size', String(chunkSize));
  form.append('chunk_overlap', String(chunkOverlap));
  const res = await authFetch('/knowledgebases/upload_docs', { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteCollection(collectionId: string): Promise<{ message: string }> {
  const res = await authFetch(`/knowledgebases/delete_collection?collection_id=${encodeURIComponent(collectionId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function ragChat(
  collection_id: string,
  question: string,
  history: RAGMessage[],
): Promise<RAGResponse> {
  const res = await authFetch('/knowledgebases/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ collection_id, question, history }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Survey ────────────────────────────────────────────────────────────────────

export async function postSurvey(body: SurveyRequest): Promise<SurveyResponse> {
  const res = await authFetch('/query/survey', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
