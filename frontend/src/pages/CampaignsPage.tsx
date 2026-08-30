import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listCampaigns, createCampaign, deleteCampaign, listKnowledgeBases, generateApiKey } from '../api';
import type { Campaign, CampaignCreate, KnowledgeBase } from '../types';

const blank: CampaignCreate = {
  campaign_name: '',
  campaign_description: '',
  start_date: '',
  end_date: '',
  status: 'active',
  target_audience: '',
  number_of_questions: 5,
  collection_id: '',
  allowed_origins: '',
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [collections, setCollections] = useState<KnowledgeBase[]>([]);
  const [form, setForm] = useState<CampaignCreate>(blank);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const load = () => listCampaigns().then(setCampaigns).catch((e) => setError(e.message));

  useEffect(() => {
    load();
    listKnowledgeBases().then(setCollections).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...form,
        allowed_origins: form.allowed_origins
          ? form.allowed_origins.split('\n').map((o) => o.trim()).filter(Boolean)
          : [],
      };
      await createCampaign(payload);
      setForm(blank);
      setShowForm(false);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this campaign?')) return;
    try {
      await deleteCampaign(id);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function handleCopyWidget(c: Campaign) {
    try {
      let key = c.api_key;
      if (!key) {
        const updated = await generateApiKey(c.campaign_id);
        key = updated.api_key!;
        setCampaigns((prev) => prev.map((x) => x.campaign_id === c.campaign_id ? { ...x, api_key: key } : x));
      }
      const snippet = `<script\n  src="${window.location.origin}/static/widget.iife.js"\n  data-api-url="${window.location.origin}"\n  data-campaign-id="${c.campaign_id}"\n  data-api-key="${key}"\n><\/script>`;
      await navigator.clipboard.writeText(snippet);
      setCopied(c.campaign_id);
      setTimeout(() => setCopied(null), 2000);
    } catch (e: any) {
      setError(e.message);
    }
  }

  const set = (k: keyof CampaignCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'number' ? Number(e.target.value) : e.target.value }));

  return (
    <div className="page">
      <div className="page-header">
        <h1>Campaigns</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancel' : '+ New Campaign'}</button>
      </div>

      {error && <p className="error">{error}</p>}

      {showForm && (
        <form className="card form-grid" onSubmit={handleCreate}>
          <label>Name<input required value={form.campaign_name} onChange={set('campaign_name')} /></label>
          <label>Status<input required value={form.status} onChange={set('status')} /></label>
          <label className="span2">Description<textarea required value={form.campaign_description} onChange={set('campaign_description')} /></label>
          <label>Start Date<input type="datetime-local" required value={form.start_date} onChange={set('start_date')} /></label>
          <label>End Date<input type="datetime-local" required value={form.end_date} onChange={set('end_date')} /></label>
          <label>Target Audience<input required value={form.target_audience} onChange={set('target_audience')} /></label>
          <label># Questions<input type="number" min={1} required value={form.number_of_questions} onChange={set('number_of_questions')} /></label>
          <label className="span2">Knowledge Base
            <select required value={form.collection_id} onChange={(e) => setForm((f) => ({ ...f, collection_id: e.target.value }))}>
              <option value="">— select a collection —</option>
              {collections.map((c) => (
                <option key={c.collection_id} value={c.collection_id}>{c.collection_name}</option>
              ))}
            </select>
          </label>
          <label className="span2">Allowed Origins <span style={{fontWeight:400, color:'#6b7280'}}>(one per line — leave empty to allow all)</span>
            <textarea value={form.allowed_origins} onChange={set('allowed_origins')} placeholder="https://example.com" />
          </label>
          <button type="submit" disabled={loading} className="span2">{loading ? 'Creating…' : 'Create Campaign'}</button>
        </form>
      )}

      <div className="card-list">
        {campaigns.map((c) => (
          <div key={c.campaign_id} className="card campaign-card">
            <div>
              <strong>{c.campaign_name}</strong>
              <span className={`badge ${c.status}`}>{c.status}</span>
            </div>
            <p>{c.campaign_description}</p>
            <small>Audience: {c.target_audience} · {c.number_of_questions} questions</small>
            <div className="card-actions">
              <Link to={`/survey/${c.campaign_id}`} className="btn-primary">Take Survey</Link>
              <button onClick={() => handleCopyWidget(c)} className="btn-secondary">
                {copied === c.campaign_id ? '✓ Copied!' : 'Copy Widget'}
              </button>
              <button className="btn-danger" onClick={() => handleDelete(c.campaign_id)}>Delete</button>
            </div>
          </div>
        ))}
        {campaigns.length === 0 && <p className="muted">No campaigns yet.</p>}
      </div>
    </div>
  );
}
