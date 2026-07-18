import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import CampaignsPage from './pages/CampaignsPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import SurveyPage from './pages/SurveyPage';

function Nav() {
  const { logout } = useAuth();
  return (
    <nav className="navbar">
      <span className="brand">InquisiTool</span>
      <div className="nav-links">
        <NavLink to="/">Campaigns</NavLink>
        <NavLink to="/knowledgebases">Knowledge Bases</NavLink>
      </div>
      <button className="btn-ghost" onClick={logout}>Logout</button>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<CampaignsPage />} />
          <Route path="/knowledgebases" element={<KnowledgeBasePage />} />
          <Route path="/survey/:campaignId" element={<SurveyPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
