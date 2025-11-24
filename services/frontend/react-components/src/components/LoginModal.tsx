import React, { useState } from "react";
import { X, LogIn, LogOut, User, Lock, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export type LoginResult = { success: boolean; message?: string };

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin?: (username: string, password: string) => Promise<LoginResult>;
  onLogout?: () => Promise<void>;
}

type ViewState = "login" | "loggedIn";
type NotificationType = "success" | "error" | null;

interface Notification {
  type: NotificationType;
  message: string;
}

const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLogin, onLogout }) => {
  const [viewState, setViewState] = useState<ViewState>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [notification, setNotification] = useState<Notification | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loggedInUsername, setLoggedInUsername] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setNotification({ type: "error", message: "Please fill in both username and password" });
      return;
    }
    setIsLoading(true);
    setNotification(null);
    try {
      const res = onLogin ? await onLogin(username, password) : { success: true, message: "Login successful!" };
      if (res.success) {
        setNotification({ type: "success", message: res.message || "Login successful!" });
        setLoggedInUsername(username);
        setTimeout(() => {
          setViewState("loggedIn");
          setNotification(null);
          setPassword("");
          window.dispatchEvent(new CustomEvent("mapai:authChanged", { detail: { isAuthenticated: true, username } }));
        }, 800);
      } else {
        setNotification({ type: "error", message: res.message || "Invalid username or password" });
      }
    } catch {
      setNotification({ type: "error", message: "An error occurred. Please try again." });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    setIsLoading(true);
    try {
      if (onLogout) await onLogout();
      setNotification({ type: "success", message: "Logged out successfully" });
      setTimeout(() => {
        setViewState("login");
        setUsername("");
        setPassword("");
        setLoggedInUsername("");
        setNotification(null);
        window.dispatchEvent(new CustomEvent("mapai:authChanged", { detail: { isAuthenticated: false } }));
        onClose();
      }, 500);
    } catch {
      setNotification({ type: "error", message: "Logout failed. Please try again." });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      setTimeout(() => setNotification(null), 300);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        />
        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={handleClose}
        >
          <div onClick={(e) => e.stopPropagation()} className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            {/* Header */}
            <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 p-6">
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all duration-200 hover:scale-110 disabled:opacity-50"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-blue-500/20 text-blue-400">
                  {viewState === "login" ? <LogIn className="w-6 h-6" /> : <User className="w-6 h-6" />}
                </div>
                <div>
                  <h2 className="text-2xl font-light text-white">{viewState === "login" ? "Login" : "Account"}</h2>
                  <p className="text-slate-400 text-sm mt-1">
                    {viewState === "login" ? "Enter your analyst credentials" : "Manage your session"}
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <AnimatePresence mode="wait">
                {viewState === "login" ? (
                  <motion.div key="login" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                    <form onSubmit={handleLogin} className="space-y-4">
                      <div>
                        <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-2">Username</label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                          <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={isLoading}
                            placeholder="Enter your username"
                            className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                          />
                        </div>
                      </div>
                      <div>
                        <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">Password</label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                          <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                            placeholder="Enter your password"
                            className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                          />
                        </div>
                      </div>

                      <AnimatePresence>
                        {notification && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className={`flex items-center gap-2 p-3 rounded-xl ${
                              notification.type === "success"
                                ? "bg-green-50 text-green-700 border border-green-200"
                                : "bg-red-50 text-red-700 border border-red-200"
                            }`}
                          >
                            {notification.type === "success" ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                            <p className="text-sm font-medium">{notification.message}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 transition-all hover:shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {isLoading ? (<><Loader2 className="w-5 h-5 animate-spin" /><span>Logging in...</span></>) : (<><LogIn className="w-5 h-5" /><span>Login</span></>)}
                      </button>
                    </form>
                  </motion.div>
                ) : (
                  <motion.div key="loggedIn" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-6">
                    <div className="text-center py-8">
                      <div className="inline-flex p-4 rounded-full bg-green-100 mb-4">
                        <CheckCircle className="w-12 h-12 text-green-600" />
                      </div>
                      <h3 className="text-2xl font-medium text-slate-800 mb-2">Welcome back!</h3>
                      <p className="text-slate-600">You are logged in as <span className="font-semibold text-blue-600">{loggedInUsername}</span></p>
                    </div>

                    {notification && (
                      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                        className={`flex items-center gap-2 p-3 rounded-xl ${
                          notification.type === "success"
                            ? "bg-green-50 text-green-700 border border-green-200"
                            : "bg-red-50 text-red-700 border border-red-200"
                        }`}>
                        {notification.type === "success" ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                        <p className="text-sm font-medium">{notification.message}</p>
                      </motion.div>
                    )}

                    <button
                      onClick={handleLogout}
                      disabled={isLoading}
                      className="w-full py-3 px-4 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl font-medium hover:from-red-600 hover:to-red-700 transition-all hover:shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {isLoading ? (<><Loader2 className="w-5 h-5 animate-spin" /><span>Logging out...</span></>) : (<><LogOut className="w-5 h-5" /><span>Logout</span></>)}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default LoginModal;
