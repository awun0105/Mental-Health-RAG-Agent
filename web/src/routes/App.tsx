import { FormEvent, useEffect, useState, useTransition } from "react";

import {
  ApiError,
  ChatSession,
  ConsentStatus,
  CurrentUserClaims,
  acceptConsent,
  closeSession,
  exchangeGoogleAuthCode,
  getConsentStatus,
  getGoogleOAuthUrl,
  getMe,
  getSession,
  listMySessions,
  login,
  logout,
  register,
  startSession,
} from "../api/client";

type AppState =
  | "checking_session"
  | "anonymous"
  | "authenticated_needs_consent"
  | "authenticated_ready"
  | "error";

type Page = "auth" | "consent" | "sessions" | "profile";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

function formatDate(value: string | null): string {
  if (!value) return "Not ended";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function App() {
  const [appState, setAppState] = useState<AppState>("checking_session");
  const [page, setPage] = useState<Page>("auth");
  const [claims, setClaims] = useState<CurrentUserClaims | null>(null);
  const [consent, setConsent] = useState<ConsentStatus | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAuthenticatedState(nextClaims?: CurrentUserClaims) {
    const currentClaims = nextClaims ?? (await getMe());
    const consentStatus = await getConsentStatus();

    setClaims(currentClaims);
    setConsent(consentStatus);

    if (consentStatus.has_valid_consent) {
      setAppState("authenticated_ready");
      setPage("sessions");
      return;
    }

    setAppState("authenticated_needs_consent");
    setPage("consent");
  }

  async function refreshSession() {
    try {
      await loadAuthenticatedState();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setClaims(null);
        setConsent(null);
        setAppState("anonymous");
        setPage("auth");
        return;
      }
      setError(errorMessage(err));
      setAppState("error");
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleError = params.get("google_error");
    const authCode = params.get("auth_code");

    async function boot() {
      setAppState("checking_session");
      try {
        if (googleError) {
          setError(googleError);
          window.history.replaceState({}, "", "/");
          setAppState("anonymous");
          setPage("auth");
          return;
        }

        if (authCode) {
          const body = await exchangeGoogleAuthCode(authCode);
          setFlash(`Signed in as ${body.user.email}`);
          window.history.replaceState({}, "", "/");
        }

        await refreshSession();
      } catch (err) {
        setError(errorMessage(err));
        setAppState("error");
      }
    }

    void boot();
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setClaims(null);
      setConsent(null);
      setAppState("anonymous");
      setPage("auth");
    }
  }

  function navigate(nextPage: Page) {
    if (!claims) {
      setPage("auth");
      return;
    }
    if (appState === "authenticated_needs_consent" && nextPage !== "consent") {
      setPage("consent");
      return;
    }
    setPage(nextPage);
  }

  return (
    <Shell
      appState={appState}
      claims={claims}
      page={page}
      onNavigate={navigate}
      onLogout={handleLogout}
    >
      {flash ? <div className="notice success">{flash}</div> : null}
      {error ? <div className="notice error">{error}</div> : null}

      {appState === "checking_session" ? <LoadingPanel /> : null}

      {appState === "anonymous" ? (
        <AuthPage
          onSignedIn={async () => {
            setError(null);
            await loadAuthenticatedState();
          }}
          onError={setError}
        />
      ) : null}

      {claims && page === "consent" ? (
        <ConsentPage
          consent={consent}
          onAccepted={async () => {
            setFlash("Consent accepted.");
            await loadAuthenticatedState(claims);
          }}
          onError={setError}
        />
      ) : null}

      {claims && appState === "authenticated_ready" && page === "sessions" ? (
        <PatientSessionsPage onError={setError} />
      ) : null}

      {claims && appState === "authenticated_ready" && page === "profile" ? (
        <ProfilePage claims={claims} consent={consent} />
      ) : null}

      {appState === "error" ? (
        <section className="panel">
          <h2>Application error</h2>
          <p>Refresh the page or log in again after fixing the backend/frontend connection.</p>
          <button onClick={() => void refreshSession()}>Retry session check</button>
        </section>
      ) : null}
    </Shell>
  );
}

function Shell({
  appState,
  claims,
  page,
  children,
  onNavigate,
  onLogout,
}: {
  appState: AppState;
  claims: CurrentUserClaims | null;
  page: Page;
  children: React.ReactNode;
  onNavigate: (page: Page) => void;
  onLogout: () => void;
}) {
  const canUseApp = appState === "authenticated_ready";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="brand-kicker">Mental Health AI</p>
          <h1>Sovereign clinical support</h1>
        </div>
        <nav>
          {!claims ? (
            <button className={page === "auth" ? "active" : ""} onClick={() => onNavigate("auth")}>
              Log in or sign up
            </button>
          ) : null}
          {claims ? (
            <button
              className={page === "consent" ? "active" : ""}
              onClick={() => onNavigate("consent")}
            >
              Consent
            </button>
          ) : null}
          {canUseApp ? (
            <button
              className={page === "sessions" ? "active" : ""}
              onClick={() => onNavigate("sessions")}
            >
              Patient sessions
            </button>
          ) : null}
          {canUseApp ? (
            <button
              className={page === "profile" ? "active" : ""}
              onClick={() => onNavigate("profile")}
            >
              Profile
            </button>
          ) : null}
        </nav>
        <div className="account-card">
          {claims ? (
            <>
              <span>{claims.email}</span>
              <strong>{claims.role}</strong>
              <small>{appState.replaceAll("_", " ")}</small>
              <button className="secondary" onClick={onLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <span>Not signed in</span>
              <small>{appState.replaceAll("_", " ")}</small>
            </>
          )}
        </div>
      </aside>
      <main>{children}</main>
    </div>
  );
}

function LoadingPanel() {
  return (
    <section className="hero">
      <div>
        <p className="brand-kicker">Checking session</p>
        <h2>Restoring your secure browser session.</h2>
        <p>React is asking FastAPI for `/auth/me` through the HTTP-only cookie.</p>
      </div>
      <div className="status-panel">
        <span>Auth mode</span>
        <strong>HTTP-only cookie</strong>
        <span>Status</span>
        <strong>Loading</strong>
      </div>
    </section>
  );
}

function AuthPage({
  onSignedIn,
  onError,
}: {
  onSignedIn: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isPending, startTransition] = useTransition();

  async function continueWithGoogle() {
    try {
      const url = await getGoogleOAuthUrl();
      window.location.assign(url);
    } catch (err) {
      onError(errorMessage(err));
    }
  }

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await login(email, password);
        await onSignedIn();
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  function submitSignup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(async () => {
      try {
        await register(email, password, fullName);
        await login(email, password);
        await onSignedIn();
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  return (
    <section className="auth-layout">
      <article className="auth-card primary-auth">
        <p className="brand-kicker">Browser auth</p>
        <h2>Log in or sign up</h2>
        <p>
          Continue with Google to use the production browser flow. Password auth
          remains available for local development accounts.
        </p>
        <button className="google" onClick={continueWithGoogle} disabled={isPending}>
          Continue with Google
        </button>
      </article>
      <article className="auth-card">
        <form onSubmit={submitLogin}>
          <h3>Password login</h3>
          <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            type="password"
          />
          <button disabled={isPending}>Log in</button>
        </form>
      </article>
      <article className="auth-card">
        <form onSubmit={submitSignup}>
          <h3>Create patient account</h3>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Full name"
          />
          <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            type="password"
          />
          <button disabled={isPending}>Create and sign in</button>
        </form>
      </article>
    </section>
  );
}

function ConsentPage({
  consent,
  onAccepted,
  onError,
}: {
  consent: ConsentStatus | null;
  onAccepted: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [isPending, startTransition] = useTransition();

  function submitConsent() {
    if (!consent) return;
    startTransition(async () => {
      try {
        await acceptConsent(consent.current_policy_version);
        await onAccepted();
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  return (
    <section className="panel">
      <p className="brand-kicker">Consent gate</p>
      <h2>Consent required before patient sessions</h2>
      {consent ? (
        <div className="consent-status">
          <span>Current policy</span>
          <strong>{consent.current_policy_version}</strong>
          <span>Status</span>
          <strong>{consent.has_valid_consent ? "Accepted" : "Missing"}</strong>
          <span>Latest accepted</span>
          <strong>{consent.latest_accepted_policy_version ?? "None"}</strong>
        </div>
      ) : (
        <p>Loading consent status...</p>
      )}
      <button onClick={submitConsent} disabled={!consent || isPending || consent.has_valid_consent}>
        {consent?.has_valid_consent ? "Consent already accepted" : "Accept current policy"}
      </button>
    </section>
  );
}

function PatientSessionsPage({ onError }: { onError: (message: string) => void }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selected, setSelected] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  async function loadSessions(nextSelectedId?: string) {
    setLoading(true);
    try {
      const body = await listMySessions();
      setSessions(body.items);

      if (nextSelectedId) {
        const nextSelected = body.items.find((session) => session.id === nextSelectedId);
        setSelected(nextSelected ?? body.items[0] ?? null);
        return;
      }

      setSelected((current) => {
        if (!current) return body.items[0] ?? null;
        return body.items.find((session) => session.id === current.id) ?? body.items[0] ?? null;
      });
    } catch (err) {
      onError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSessions();
  }, []);

  function handleStartSession() {
    startTransition(async () => {
      try {
        const session = await startSession();
        await loadSessions(session.id);
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  function handleSelectSession(sessionId: string) {
    startTransition(async () => {
      try {
        const session = await getSession(sessionId);
        setSelected(session);
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  function handleCloseSession(sessionId: string) {
    startTransition(async () => {
      try {
        const session = await closeSession(sessionId);
        await loadSessions(session.id);
      } catch (err) {
        onError(errorMessage(err));
      }
    });
  }

  return (
    <section className="session-workspace">
      <div className="workspace-header">
        <div>
          <p className="brand-kicker">Patient workspace</p>
          <h2>Sessions</h2>
          <p>Start, inspect, and close your own patient support sessions.</p>
        </div>
        <button onClick={handleStartSession} disabled={isPending}>
          Start new session
        </button>
      </div>

      <div className="session-grid">
        <article className="panel">
          <h3>Your sessions</h3>
          {loading ? <p>Loading sessions...</p> : null}
          {!loading && sessions.length === 0 ? (
            <div className="empty-state">
              <strong>No sessions yet.</strong>
              <span>Start your first session after accepting consent.</span>
            </div>
          ) : null}
          <div className="session-list">
            {sessions.map((session) => (
              <button
                className={`session-row ${selected?.id === session.id ? "selected" : ""}`}
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
              >
                <span>{session.id.slice(0, 8)}</span>
                <strong className={`status-pill ${session.status}`}>{session.status}</strong>
                <small>{formatDate(session.started_at)}</small>
              </button>
            ))}
          </div>
        </article>

        <article className="panel session-detail">
          <h3>Session detail</h3>
          {selected ? (
            <>
              <div className="detail-grid">
                <span>ID</span>
                <strong>{selected.id}</strong>
                <span>Status</span>
                <strong className={`status-pill ${selected.status}`}>{selected.status}</strong>
                <span>Started</span>
                <strong>{formatDate(selected.started_at)}</strong>
                <span>Ended</span>
                <strong>{formatDate(selected.ended_at)}</strong>
              </div>
              <h4>Metadata</h4>
              <pre>{JSON.stringify(selected.metadata, null, 2)}</pre>
              <button
                className="danger"
                onClick={() => handleCloseSession(selected.id)}
                disabled={isPending || selected.status !== "active"}
              >
                {selected.status === "active" ? "Close session" : "Session closed"}
              </button>
            </>
          ) : (
            <div className="empty-state">
              <strong>No session selected.</strong>
              <span>Select a session or start a new one.</span>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function ProfilePage({
  claims,
  consent,
}: {
  claims: CurrentUserClaims;
  consent: ConsentStatus | null;
}) {
  return (
    <section className="panel">
      <p className="brand-kicker">Current account</p>
      <h2>Profile claims</h2>
      <pre>{JSON.stringify({ claims, consent }, null, 2)}</pre>
    </section>
  );
}
