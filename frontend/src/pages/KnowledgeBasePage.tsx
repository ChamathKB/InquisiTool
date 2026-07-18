import { useState } from 'react';
import { createCollection, uploadDocs, deleteCollection } from '../api';

export default function KnowledgeBasePage() {
  const [collectionName, setCollectionName] = useState('');
  const [collectionMsg, setCollectionMsg] = useState('');
  const [lastCollectionId, setLastCollectionId] = useState('');

  const [file, setFile] = useState<File | null>(null);
  const [uploadCollectionId, setUploadCollectionId] = useState('');
  const [uploadMsg, setUploadMsg] = useState('');
  const [uploading, setUploading] = useState(false);

  const [deleteId, setDeleteId] = useState('');
  const [deleteMsg, setDeleteMsg] = useState('');

  const [error, setError] = useState('');

  async function handleCreateCollection(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setCollectionMsg('');
    try {
      const res = await createCollection(collectionName);
      setCollectionMsg(res.message);
      // extract the id from the message: "... collection id <id>!"
      const match = res.message.match(/collection id ([a-f0-9]+)/i);
      if (match) setLastCollectionId(match[1]);
      setCollectionName('');
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError('');
    setUploadMsg('');
    setUploading(true);
    try {
      const res = await uploadDocs(file, uploadCollectionId);
      setUploadMsg(res.message);
      setFile(null);
      setUploadCollectionId('');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    if (!confirm(`Delete collection "${deleteId}"?`)) return;
    setError('');
    setDeleteMsg('');
    try {
      const res = await deleteCollection(deleteId);
      setDeleteMsg(res.message);
      setDeleteId('');
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header"><h1>Knowledge Bases</h1></div>
      {error && <p className="error">{error}</p>}

      <div className="card-list">
        <div className="card">
          <h2>Create Collection</h2>
          <form onSubmit={handleCreateCollection} className="inline-form">
            <input
              required
              placeholder="Collection name"
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
            />
            <button type="submit">Create</button>
          </form>
          {collectionMsg && <p className="success">{collectionMsg}</p>}
          {lastCollectionId && (
            <div className="collection-id-box">
              <span>Collection ID:</span>
              <code
                className="collection-id"
                title="Click to copy"
                onClick={() => navigator.clipboard.writeText(lastCollectionId)}
              >
                {lastCollectionId}
              </code>
              <span className="muted">(click to copy)</span>
            </div>
          )}
        </div>

        <div className="card">
          <h2>Upload Documents</h2>
          <form onSubmit={handleUpload} className="form-grid">
            <label className="span2">
              PDF File
              <input
                type="file"
                accept=".pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <label className="span2">
              Collection ID
              <input
                required
                placeholder="e.g. 507f1f77bcf86cd799439011"
                value={uploadCollectionId}
                onChange={(e) => setUploadCollectionId(e.target.value)}
              />
            </label>
            <button type="submit" disabled={uploading} className="span2">
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          </form>
          {uploadMsg && <p className="success">{uploadMsg}</p>}
        </div>

        <div className="card">
          <h2>Delete Collection</h2>
          <form onSubmit={handleDelete} className="inline-form">
            <input
              required
              placeholder="Collection ID"
              value={deleteId}
              onChange={(e) => setDeleteId(e.target.value)}
            />
            <button type="submit" className="btn-danger">Delete</button>
          </form>
          {deleteMsg && <p className="success">{deleteMsg}</p>}
        </div>
      </div>
    </div>
  );
}
