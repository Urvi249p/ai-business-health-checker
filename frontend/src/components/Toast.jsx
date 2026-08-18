import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((t) => t.map((x) => (x.id === id ? { ...x, visible: false } : x)));
    // remove after animation
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 300);
  }, []);

  const showToast = useCallback((message, type = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const toast = { id, message, type, visible: true };
    setToasts((t) => [toast, ...t]);

    // auto-dismiss after 4s
    setTimeout(() => {
      setToasts((t) => t.map((x) => (x.id === id ? { ...x, visible: false } : x)));
      setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 300);
    }, 4000);

    return id;
  }, []);

  // cleanup on unmount
  useEffect(() => {
    return () => setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`toast toast--${t.type} ${t.visible ? '' : 'toast--hide'}`}
            onClick={() => removeToast(t.id)}
            role="status"
            aria-live="polite"
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export default ToastProvider;
