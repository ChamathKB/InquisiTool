import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { postSurvey } from '../api';
import { useAuth } from '../AuthProvider';

interface Message {
  role: 'agent' | 'user';
  text: string;
}

export default function SurveyPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { userId } = useAuth();

  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [ended, setEnded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Start survey on mount
  useEffect(() => {
    if (!campaignId) return;
    setLoading(true);
    postSurvey({ user_id: userId, campaign_id: campaignId })
      .then((res) => {
        setSessionId(res.session_id);
        setMessages([{ role: 'agent', text: res.question }]);
        if (res.survey_ended) setEnded(true);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [campaignId, userId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !sessionId || ended) return;
    const answer = input.trim();
    setInput('');
    setMessages((m) => [...m, { role: 'user', text: answer }]);
    setLoading(true);
    setError('');
    try {
      const res = await postSurvey({ user_id: userId, campaign_id: campaignId!, session_id: sessionId, answer });
      setMessages((m) => [...m, { role: 'agent', text: res.question }]);
      if (res.survey_ended) setEnded(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="survey-layout">
      <div className="survey-header">
        <h2>Survey</h2>
        <small className="muted">Campaign: {campaignId}</small>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
        {loading && <div className="bubble agent typing">…</div>}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input" onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={ended ? 'Survey complete' : 'Type your answer…'}
          disabled={ended || loading}
        />
        <button type="submit" disabled={ended || loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}
