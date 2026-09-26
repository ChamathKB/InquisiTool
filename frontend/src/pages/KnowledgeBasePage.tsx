import { useEffect, useRef, useState } from 'react';
import { listKnowledgeBases, createCollection, uploadDocs, deleteCollection, ragChat } from '../api';
import type { KnowledgeBase, RAGMessage, RAGSource } from '../types';

interface ChatEntry {
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGSource[];
}

export default function KnowledgeBasePage() {
  const [collections, setCollections] = useState<KnowledgeBase[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [collectionName, setCollectionName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const [openChat, setOpenChat] = useState<string | null>(null);
  const [chatHistories, setChatHistories] = useState<Record<string, ChatEntry[]>>({});
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const load = () => listKnowledgeBases().then(setCollections).catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistories, openChat]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await createCollection(collectionName);
      setCollectionName('');
      setShowForm(false);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.FormEvent, collectionId: string) {
    e.preventDefault();
    if (!uploadFile) return;
    setError('');
    setUploadingId(collectionId);
    try {
      await uploadDocs(uploadFile, collectionId);
      setUploadFile(null);
      setUploadingId(null);
    } catch (e: any) {
      setError(e.message);
      setUploadingId(null);
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete collection "${name}"?`)) return;
    setError('');
    try {
      await deleteCollection(id);
      if (openChat === id) setOpenChat(null);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  function toggleChat(id: string) {
    setOpenChat((prev) => (prev === id ? null : id));
    setChatInput('');
  }

  async function handleChatSubmit(e: React.FormEvent, collectionId: string) {
    e.preventDefault();
    const question = chatInput.trim();
    if (!question) return;

    const prev = chatHistories[collectionId] ?? [];
    const userEntry: ChatEntry = { role: 'user', content: question };
    setChatHistories((h) => ({ ...h, [collectionId]: [...prev, userEntry] }));
    setChatInput('');
    setChatLoading(true);

    try {
      const history: RAGMessage[] = prev.map((m) => ({ role: m.role, content: m.content }));
      const res = await ragChat(collectionId, question, history);
      const assistantEntry: ChatEntry = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
      };
      setChatHistories((h) => ({
        ...h,
        [collectionId]: [...(h[collectionId] ?? []), assistantEntry],
      }));
    } catch (e: any) {
      setChatHistories((h) => ({
        ...h,
        [collectionId]: [
          ...(h[collectionId] ?? []),
          { role: 'assistant', content: `Error: ${e.message}` },
        ],
      }));
    } finally {
      setChatLoading(false);
    }
  }

  function toggleSources(key: string) {
    setExpandedSources((s) => ({ ...s, [key]: !s[key] }));
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Knowledge Bases</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancel' : '+ New Collection'}</button>
      </div>

      {error && <p className="error">{error}</p>}

      {showForm && (
        <form className="card inline-form" onSubmit={handleCreate}>
          <input
            required
            placeholder="Collection name"
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
          />
          <button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create'}</button>
        </form>
      )}

      <div className="card-list">
        {collections.map((c) => (
          <div key={c.collection_id} className="card campaign-card">
            <div>
              <strong>{c.collection_name}</strong>
            </div>
            <small className="muted">
              ID: <code className="collection-id" title="Click to copy" onClick={() => navigator.clipboard.writeText(c.collection_id)}>{c.collection_id}</code>
              &nbsp;· Created: {new Date(c.uploaded_at).toLocaleDateString()}
            </small>

            <form className="upload-row" onSubmit={(e) => handleUpload(e, c.collection_id)}>
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
              />
              <button type="submit" disabled={uploadingId === c.collection_id}>
                {uploadingId === c.collection_id ? 'Uploading…' : 'Upload PDF'}
              </button>
            </form>

            <div className="card-actions">
              <button className="btn-secondary" onClick={() => toggleChat(c.collection_id)}>
                {openChat === c.collection_id ? 'Close Chat' : '💬 Chat'}
              </button>
              <button className="btn-danger" onClick={() => handleDelete(c.collection_id, c.collection_name)}>Delete</button>
            </div>

            {openChat === c.collection_id && (
              <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ maxHeight: 360, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 0' }}>
                  {(chatHistories[c.collection_id] ?? []).length === 0 && (
                    <p className="muted" style={{ fontSize: '0.85rem' }}>Ask anything about the documents in this collection.</p>
                  )}
                  {(chatHistories[c.collection_id] ?? []).map((entry, i) => (
                    <div key={i}>
                      <div className={`bubble ${entry.role === 'user' ? 'user' : 'agent'}`}>
                        {entry.content}
                      </div>
                      {entry.role === 'assistant' && entry.sources && entry.sources.length > 0 && (
                        <div style={{ marginTop: 4, paddingLeft: 4 }}>
                          <button
                            className="btn-ghost"
                            style={{ fontSize: '0.75rem', padding: '2px 8px' }}
                            onClick={() => toggleSources(`${c.collection_id}-${i}`)}
                          >
                            {expandedSources[`${c.collection_id}-${i}`] ? '▲ Hide sources' : `▼ ${entry.sources.length} source${entry.sources.length > 1 ? 's' : ''}`}
                          </button>
                          {expandedSources[`${c.collection_id}-${i}`] && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
                              {entry.sources.map((s, si) => (
                                <div key={si} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '6px 10px' }}>
                                  <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: 2 }}>Source {si + 1} · score {s.score}</p>
                                  <p style={{ fontSize: '0.82rem', whiteSpace: 'pre-wrap' }}>{s.text}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="bubble agent typing">Thinking…</div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                <form className="chat-input" onSubmit={(e) => handleChatSubmit(e, c.collection_id)}>
                  <input
                    placeholder="Ask a question…"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={chatLoading}
                  />
                  <button type="submit" disabled={chatLoading || !chatInput.trim()}>Send</button>
                </form>
              </div>
            )}
          </div>
        ))}
        {collections.length === 0 && <p className="muted">No collections yet.</p>}
      </div>
    </div>
  );
}
