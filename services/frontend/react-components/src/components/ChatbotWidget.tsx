import React, { useEffect, useRef, useState } from "react";
import { X, Send, MessageCircle } from "lucide-react";

function getApiBase(): string {
  if (typeof window === "undefined") return "";
  const w = window as any;

  // Honor injected base first
  if (w.__API_BASE__) return w.__API_BASE__;

  const host = window.location.hostname;                // ✅ use window.location
  const isLocalhost = host === "localhost" || host === "127.0.0.1";
  return isLocalhost ? "http://localhost:8000" : "";
}
type Msg = { role: "user" | "assistant"; content: string };

const ChatbotWidget: React.FC = () => {
  const [visible, setVisible] = useState(false);        // overall availability (logged or not)
  const [open, setOpen] = useState(false);              // drawer open/closed
  const [lang, setLang] = useState<"ca"|"en">("en");
  const [apiBase] = useState<string>(() => getApiBase());// default Catalan
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "assistant", content: "Hola! Pregunta’m sobre les dades de l’enquesta (o si ho prefereixes, en anglès)." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onAuth = (e: any) => {
      const ok = !!(e?.detail?.isAuthenticated);
      setVisible(ok);
      if (!ok) { setOpen(false); }
    };
    window.addEventListener("mapai:authChanged", onAuth as EventListener);
    return () => window.removeEventListener("mapai:authChanged", onAuth as EventListener);
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, open]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setMsgs(m => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const r = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // send session cookie
        body: JSON.stringify({ message: q, lang })
      });
      if (!r.ok) {
        const detail = (await r.json().catch(() => ({})))?.detail || "Error";
        setMsgs(m => [...m, { role: "assistant", content: `No he pogut respondre (${detail}).` }]);
      } else {
        const j = await r.json();
        setMsgs(m => [...m, { role: "assistant", content: j.answer }]);
      }
    } catch (e: any) {
      setMsgs(m => [...m, { role: "assistant", content: "Error de connexió amb el backend." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="mapai-chat-fab"
          aria-label="Open chatbot"
          title="Ask the dataset"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {open && (
        <div className="mapai-chat-drawer">
          <div className="mapai-chat-header">
            <div className="mapai-chat-title">MapAI Assistant</div>
            <div className="mapai-chat-controls">
              <select
                className="mapai-chat-lang"
                value={lang}
                onChange={e => setLang(e.target.value as any)}
                aria-label="Language"
              >
                <option value="ca">Català</option>
                <option value="en">English</option>
              </select>
              <button className="mapai-chat-close" onClick={() => setOpen(false)} aria-label="Close">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="mapai-chat-body">
            {msgs.map((m, i) => (
              <div key={i} className={`mapai-chat-bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {loading && <div className="mapai-chat-bubble assistant">…thinking…</div>}
            <div ref={endRef} />
          </div>

          <div className="mapai-chat-inputrow">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder={lang === "ca" ? "Escriu la teva pregunta…" : "Type your question…"}
              rows={2}
            />
            <button onClick={send} disabled={loading || !input.trim()} className="mapai-chat-send">
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotWidget;
