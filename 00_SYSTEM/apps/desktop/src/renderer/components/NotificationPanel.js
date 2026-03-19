import { useState, useRef, useEffect, useCallback } from 'react';
import useNotifications from '../hooks/useNotifications';

const TYPE_CONFIG = {
  error: { icon: '🔴', color: 'text-red-400', bg: 'bg-red-400/10' },
  warning: { icon: '🟡', color: 'text-amber-400', bg: 'bg-amber-400/10' },
  success: { icon: '🟢', color: 'text-green-400', bg: 'bg-green-400/10' },
  info: { icon: '🔵', color: 'text-blue-400', bg: 'bg-blue-400/10' },
};

function getRelativeTime(timestamp) {
  if (!timestamp) return '';
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function NotificationPanel() {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef(null);

  const handleClickOutside = useCallback((e) => {
    if (panelRef.current && !panelRef.current.contains(e.target)) {
      setIsOpen(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, handleClickOutside]);

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="relative p-2 rounded-lg hover:bg-omega-surface transition-colors"
        aria-label="Notifications"
      >
        <svg className="w-5 h-5 text-omega-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-omega-critical text-white text-[10px] font-bold px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-omega-card border border-omega-border rounded-xl shadow-xl shadow-black/30 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-omega-border">
            <span className="font-semibold text-sm">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-xs text-omega-accent hover:text-omega-text transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Notification list */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-omega-muted text-sm">
                No notifications
              </div>
            ) : (
              notifications.map((n) => {
                const cfg = TYPE_CONFIG[n.type] || TYPE_CONFIG.info;
                return (
                  <button
                    key={n.id}
                    onClick={() => markAsRead(n.id)}
                    className={`w-full text-left px-4 py-3 flex gap-3 hover:bg-omega-surface/50 transition-colors border-b border-omega-border/50 last:border-b-0 ${
                      n.id && !n._read ? '' : 'opacity-60'
                    }`}
                  >
                    <span className={`mt-0.5 text-sm ${cfg.color}`}>{cfg.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium truncate">{n.title || 'Notification'}</span>
                        <span className="text-[10px] text-omega-muted whitespace-nowrap">
                          {getRelativeTime(n.receivedAt)}
                        </span>
                      </div>
                      {n.message && (
                        <p className="text-xs text-omega-muted mt-0.5 line-clamp-2">{n.message}</p>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
