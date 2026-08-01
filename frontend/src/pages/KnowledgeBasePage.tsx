import { useEffect, useState } from 'react';
import { listKnowledgeBases, createCollection, uploadDocs, deleteCollection } from '../api';
import type { KnowledgeBase } from '../types';

export default function KnowledgeBasePage() {
  const [collections, setCollections] = useState<KnowledgeBase[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [collectionName, setCollectionName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // upload state per collection
  const [uploadingId, setUploadingId] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const load = () => listKnowledgeBases().then(setCollections).catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

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
      await load();
    } catch (e: any) {
      setError(e.message);
    }
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
              <button className="btn-danger" onClick={() => handleDelete(c.collection_id, c.collection_name)}>Delete</button>
            </div>
          </div>
        ))}
        {collections.length === 0 && <p className="muted">No collections yet.</p>}
      </div>
    </div>
  );
}
