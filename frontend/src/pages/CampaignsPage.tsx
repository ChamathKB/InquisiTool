import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listCampaigns, createCampaign, deleteCampaign, listKnowledgeBases, generateApiKey, analyzeCampaign, getAnalysis } from '../api';
import type { Campaign, CampaignCreate, KnowledgeBase, AnalysisReport } from '../types';

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
  const [analysisMap, setAnalysisMap] = useState<Record<string, AnalysisReport>>({});
  const [analysisLoading, setAnalysisLoading] = useState<string | null>(null);
  const [openAnalysis, setOpenAnalysis] = useState<string | null>(null);

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

  async function handleAnalyze(id: string) {
    setAnalysisLoading(id);
    setError('');
    try {
      const report = await analyzeCampaign(id);
      setAnalysisMap((prev) => ({ ...prev, [id]: report }));
      setOpenAnalysis(id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAnalysisLoading(null);
    }
  }

  async function handleViewAnalysis(id: string) {
    if (openAnalysis === id) { setOpenAnalysis(null); return; }
    if (analysisMap[id]) { setOpenAnalysis(id); return; }
    setAnalysisLoading(id);
    setError('');
    try {
      const report = await getAnalysis(id);
      setAnalysisMap((prev) => ({ ...prev, [id]: report }));
      setOpenAnalysis(id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAnalysisLoading(null);
    }
  }

  const sentimentColor: Record<string, string> = {
    positive: '#16a34a',
    neutral: '#d97706',
    negative: '#ef4444',
  };

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
              <button onClick={() => handleAnalyze(c.campaign_id)} className="btn-secondary" disabled={analysisLoading === c.campaign_id}>
                {analysisLoading === c.campaign_id ? 'Analyzing…' : '⚡ Analyze'}
              </button>
              <button onClick={() => handleViewAnalysis(c.campaign_id)} className="btn-ghost" disabled={analysisLoading === c.campaign_id}>
                {openAnalysis === c.campaign_id ? 'Hide Report' : 'View Report'}
              </button>
              <button onClick={() => handleCopyWidget(c)} className="btn-secondary">
                {copied === c.campaign_id ? '✓ Copied!' : 'Copy Widget'}
              </button>
              <button className="btn-danger" onClick={() => handleDelete(c.campaign_id)}>Delete</button>
            </div>
            {openAnalysis === c.campaign_id && analysisMap[c.campaign_id] && (() => {
              const r = analysisMap[c.campaign_id];
              return (
                <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{r.total_responses} response{r.total_responses !== 1 ? 's' : ''}</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: sentimentColor[r.sentiment] ?? 'var(--muted)', textTransform: 'capitalize' }}>● {r.sentiment}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--muted)', marginLeft: 'auto' }}>Generated {new Date(r.generated_at).toLocaleString()}</span>
                  </div>
                  {r.themes.length > 0 && (
                    <div>
                      <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>THEMES</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {r.themes.map((t, i) => <span key={i} className="badge">{t}</span>)}
                      </div>
                    </div>
                  )}
                  {r.question_summaries.length > 0 && (
                    <div>
                      <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>QUESTION SUMMARIES</p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {r.question_summaries.map((qs, i) => (
                          <div key={i} style={{ background: 'var(--bg)', borderRadius: 'var(--radius)', padding: '8px 12px' }}>
                            <p style={{ fontSize: '0.85rem', fontWeight: 500 }}>{qs.question}</p>
                            <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: 2 }}>{qs.summary}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {r.insights.length > 0 && (
                    <div>
                      <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>INSIGHTS</p>
                      <ol style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {r.insights.map((ins, i) => <li key={i} style={{ fontSize: '0.9rem' }}>{ins}</li>)}
                      </ol>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        ))}
        {campaigns.length === 0 && <p className="muted">No campaigns yet.</p>}
      </div>
    </div>
  );
}
