import React, { useState, useEffect } from 'react';
import { History, Play, X, Clock, MessageSquare, BookOpen } from 'lucide-react';

export default function PastSessionsModal({ isOpen, onClose, onResumeSession, userId, apiBase }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !userId) return;

    const fetchSessions = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/api/sessions?user_id=${encodeURIComponent(userId)}`);
        if (!res.ok) throw new Error('Failed to load past sessions');
        const data = await res.json();
        setSessions(data.sessions || []);
      } catch (err) {
        console.error('Error fetching sessions:', err);
        setError('Could not load past sessions. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [isOpen, userId, apiBase]);

  if (!isOpen) return null;

  const formatDate = (epochSec) => {
    if (!epochSec) return '';
    const date = new Date(epochSec * 1000);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div className="glass-panel" style={{
        width: '90%',
        maxWidth: '650px',
        maxHeight: '80vh',
        padding: '2rem',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer'
          }}
          aria-label="Close past sessions"
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            padding: '0.5rem',
            background: 'rgba(0, 242, 254, 0.1)',
            borderRadius: '8px',
            border: '1px solid rgba(0, 242, 254, 0.2)'
          }}>
            <History size={22} color="#00f2fe" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Past Tutoring Sessions</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Resume a previous conversation from where you left off.
            </p>
          </div>
        </div>

        <div style={{
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
          paddingRight: '0.25rem'
        }}>
          {loading && (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem 0' }}>
              Loading your previous sessions...
            </p>
          )}

          {error && (
            <p style={{ textAlign: 'center', color: '#ef4444', padding: '1rem 0' }}>
              {error}
            </p>
          )}

          {!loading && !error && sessions.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
              <MessageSquare size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.5 }} />
              <p style={{ fontSize: '0.95rem', fontWeight: 600 }}>No past sessions found</p>
              <p style={{ fontSize: '0.8rem' }}>Start a voice lesson to create your first session history.</p>
            </div>
          )}

          {!loading && sessions.map((sess) => (
            <div
              key={sess.session_id}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--bg-card-border)',
                borderRadius: '10px',
                padding: '1rem 1.25rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '1rem',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <h4 style={{
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  marginBottom: '0.35rem',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {sess.summary || `Discussion on ${sess.subject}`}
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    background: 'rgba(0, 242, 254, 0.1)',
                    color: '#00f2fe',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px'
                  }}>
                    <BookOpen size={12} /> {sess.subject}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Clock size={12} /> {formatDate(sess.created_at)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <MessageSquare size={12} /> {sess.turns_count || 0} turns
                  </span>
                </div>
              </div>

              <button
                className="glow-button"
                onClick={() => onResumeSession(sess.session_id)}
                style={{
                  padding: '0.5rem 1rem',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  whiteSpace: 'nowrap'
                }}
              >
                <Play size={14} /> Resume
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
