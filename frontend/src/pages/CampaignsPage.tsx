import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listCampaigns, createCampaign, deleteCampaign, listKnowledgeBases } from '../api';
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
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [collections, setCollections] = useState<KnowledgeBase[]>([]);
  const [form, setForm] = useState<CampaignCreate>(blank);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
      await createCampaign(form);
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
              <button className="btn-danger" onClick={() => handleDelete(c.campaign_id)}>Delete</button>
            </div>
          </div>
        ))}
        {campaigns.length === 0 && <p className="muted">No campaigns yet.</p>}
      </div>
    </div>
  );
}
