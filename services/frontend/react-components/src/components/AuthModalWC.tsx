// AuthModalWC.tsx
import React, { useEffect, useState } from "react";
import LoginModal from "./LoginModal";

// Keep API_BASE
const API_BASE =
  (typeof window !== "undefined" && (window as any).__API_BASE__) || "";

const api = {
  login: async (username: string, password: string) => {
    const r = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    const ok = r.ok;
    let msg = "Login successful!";
    try {
      const j = await r.json();
      if (j?.message) msg = j.message;
    } catch {}
    return { success: ok, message: ok ? msg : "Invalid credentials" };
  },
  logout: async () => {
    await fetch(`${API_BASE}/api/logout`, {
      method: "POST",
      credentials: "include",
    });
  },
};

const AuthModalWC: React.FC = () => {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const openHandler = () => setOpen(true);
    const closeHandler = () => setOpen(false);
    window.addEventListener("mapai:openAuth", openHandler as EventListener);
    window.addEventListener("mapai:closeAuth", closeHandler as EventListener);
    return () => {
      window.removeEventListener("mapai:openAuth", openHandler as EventListener);
      window.removeEventListener("mapai:closeAuth", closeHandler as EventListener);
    };
  }, []);

  // ✅ wrappers that dispatch the global auth event
  const handleLogin = async (username: string, password: string) => {
    const res = await api.login(username, password);
    if (res.success) {
      window.dispatchEvent(
        new CustomEvent("mapai:authChanged", {
          detail: { isAuthenticated: true, username },
        })
      );
    }
    return res; // must return { success, message } to LoginModal
  };

  const handleLogout = async () => {
    await api.logout();
    window.dispatchEvent(
      new CustomEvent("mapai:authChanged", {
        detail: { isAuthenticated: false },
      })
    );
  };

  return (
    <LoginModal
      isOpen={open}
      onClose={() => setOpen(false)}
      onLogin={handleLogin}   // ✅ use wrappers
      onLogout={handleLogout} // ✅ use wrappers
    />
  );
};

export default AuthModalWC;
