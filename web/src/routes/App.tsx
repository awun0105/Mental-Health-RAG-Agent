import { FormEvent, useEffect, useState, useTransition } from "react";

import {
  ApiError,
  ConsentStatus,
  CurrentUserClaims,
  acceptConsent,
  exchangeGoogleAuthCode,
  getConsentStatus,
  getGoogleOAuthUrl,
  getMe,
  login,
  logout,
  register,
} from "../api/client";

type Page = "home" | "auth" | "consent" | "profile";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

export function App() {
  const [page, setPage] = useState<Page>("home");
  const [claims, setClaims] = useState<CurrentUserClaims | null>(null);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshSession() {
    try {
      const me = await getMe();
      setClaims(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setClaims(null);
        return;
      }
      setError(errorMessage(err));
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleError = params.get("google_error");
    const authCode = params.get("auth_code");

    async function boot() {
      setLoading(true);
      try {
        if (googleError) {
          setError(googleError);
          window.history.replaceState({}, "", "/");
          setPage("auth");
          return;
        }
        if (authCode) {
          const body = await exchangeGoogleAuthCode(authCode);
          setFlash(`Signed in as ${body.user.email}`);
          window.history.replaceState({}, "", "/");
          setPage("consent");
        }
        await refreshSession();
      } finally {
        setLoading(false);
      }
    }

    void boot();
  }, []);

  async function handleLogout() {
    await logout();
    setClaims(null);
    setPage("auth");
  }

  if (loading) {
    return <Shell claims={claims}>Loading session...</Shell>;
  }

  return (
    <Shell claims={claims} onNavigate={setPage} onLogout={handleLogout}>
      {flash ? <div className="notice success">{flash}</div> : null}
      {error ? <div className="notice error">{error}</div> : null}
      {page === "home" ? <Home claims={claims} onNavigate={setPage} /> : null}
      {page === "auth" ? (
        <AuthPage
          onSignedIn={async () => {
            await refreshSession();
            setPage("consent");
          }}
          onError={setError}
        />
      ) : null}
      {page === "consent" ? <Protected claims={claims} page={<ConsentPage />} /> : null}
      {page === "profile" ? <Protected claims={claims} page={<ProfilePage claims={claims} />} /> : null}
    </Shell>
  );
}

function Shell({
  claims,
  children,
  onNavigate,
  onLogout,
}: {
  claims: CurrentUserClaims | null;
  children: React.ReactNode;
  onNavigate?: (page: Page) => void;
  onLogout?: () => void;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="brand-kicker">Mental Health AI</p>
          <h1>Sovereign clinical support</h1>
        </div>
        <nav>
          <button onClick={() => onNavigate?.("home")}>Home</button>
          {!claims ? <button onClick={() => onNavigate?.("auth")}>Log in or sign up</button> : null}
          {claims ? <button onClick={() => onNavigate?.("consent")}>Consent</button> : null}
          {claims ? <button onClick={() => onNavigate?.("profile")}>Profile</button> : null}
        </nav>
        <div className="account-card">
          {claims ? (
            <>
              <span>{claims.email}</span>
              <strong>{claims.role}</strong>
              <button className="secondary" onClick={onLogout}>
                Log out
              </button>
            </>
          ) : (
            <span>Not signed in</span>
          )}
        </div>
      </aside>
      <main>{children}</main>
    </div>
  );
}

function Home({
  claims,
  onNavigate,
}: {
  claims: CurrentUserClaims | null;
  onNavigate: (page: Page) => void;
}) {
  return (
    <section className="hero">
      <div>
        <h2>Private mental-health workflows, ready for a real browser app.</h2>
        <p>
          This React shell uses FastAPI cookie sessions and keeps Supabase behind
          the backend boundary.
        </p>
        <button onClick={() => onNavigate(claims ? "consent" : "auth")}>
          {claims ? "Continue to consent" : "Log in or sign up"}
        </button>
      </div>
      <div className="status-panel">
        <span>Auth mode</span>
        <strong>HTTP-only cookie</strong>
        <span>Backend</span>
        <strong>FastAPI</strong>
        <span>Session</span>
        <strong>{claims ? "Active" : "Anonymous"}</strong>
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
    <section className="card-grid">
      <article className="auth-card">
        <h2>Log in or sign up</h2>
        <p>Use Google OAuth first. Password auth remains available for development.</p>
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

function Protected({ claims, page }: { claims: CurrentUserClaims | null; page: React.ReactNode }) {
  if (!claims) {
    return <div className="notice error">You need to log in first.</div>;
  }
  return page;
}

function ConsentPage() {
  const [status, setStatus] = useState<ConsentStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void getConsentStatus().then(setStatus);
  }, []);

  async function submitConsent() {
    if (!status) return;
    await acceptConsent(status.current_policy_version);
    setMessage("Consent accepted.");
    setStatus(await getConsentStatus());
  }

  return (
    <section className="panel">
      <h2>Consent</h2>
      {status ? (
        <>
          <p>Current policy: {status.current_policy_version}</p>
          <p>Status: {status.has_valid_consent ? "Accepted" : "Missing"}</p>
          <button onClick={submitConsent}>Accept current policy</button>
        </>
      ) : (
        <p>Loading consent status...</p>
      )}
      {message ? <div className="notice success">{message}</div> : null}
    </section>
  );
}

function ProfilePage({ claims }: { claims: CurrentUserClaims | null }) {
  return (
    <section className="panel">
      <h2>Profile claims</h2>
      <pre>{JSON.stringify(claims, null, 2)}</pre>
    </section>
  );
}
