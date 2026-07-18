import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import keycloak from './keycloak';

interface AuthCtx {
  token: string;
  userId: string;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    keycloak
      .init({ onLoad: 'login-required', pkceMethod: 'S256' })
      .then(() => setReady(true))
      .catch(console.error);
  }, []);

  if (!ready) return <div className="loading">Authenticating…</div>;

  const ctx: AuthCtx = {
    token: keycloak.token ?? '',
    userId: keycloak.tokenParsed?.sub ?? '',
    logout: () => keycloak.logout(),
  };

  return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
