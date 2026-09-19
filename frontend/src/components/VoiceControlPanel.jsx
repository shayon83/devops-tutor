import React from 'react';
import { Mic, MicOff, PhoneOff, Play, Volume2 } from 'lucide-react';

export default function VoiceControlPanel({ isConnected, isMuted, setIsMuted, onStartSession, onEndSession, isConnecting }) {
  return (
    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Volume2 size={18} color="#00f2fe" /> Voice Interaction Engine
        </h2>
      </div>

      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        background: 'rgba(0,0,0,0.3)', 
        borderRadius: '12px',
        border: '1px dashed var(--bg-card-border)',
        padding: '2rem',
        textAlign: 'center'
      }}>
        {!isConnected ? (
          <div>
            <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(0, 242, 254, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto' }}>
              <Mic size={40} color="#00f2fe" />
            </div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Ready to Learn DevOps?</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: 300, marginBottom: '1.5rem' }}>
              Connect with your AI Socratic SRE tutor for voice-based problem solving and live visual diagrams.
            </p>
            <button className="glow-button" onClick={onStartSession} disabled={isConnecting}>
              <Play size={18} /> {isConnecting ? 'Connecting...' : 'Start Voice Lesson'}
            </button>
          </div>
        ) : (
          <div>
            <div style={{ width: 90, height: 90, borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', border: '2px solid var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto' }} className="pulse-circle">
              <Mic size={44} color="#10b981" />
            </div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Tutor Session Active</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Speak naturally into your microphone. Say "stop" or cut in anytime to interrupt.
            </p>
            
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                onClick={() => setIsMuted(!isMuted)}
                style={{
                  background: isMuted ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.1)',
                  color: isMuted ? '#ef4444' : '#fff',
                  border: '1px solid var(--bg-card-border)',
                  borderRadius: '10px',
                  padding: '0.75rem 1.25rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: 600
                }}
              >
                {isMuted ? <MicOff size={18} /> : <Mic size={18} />} {isMuted ? 'Unmute' : 'Mute Mic'}
              </button>

              <button 
                onClick={onEndSession}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  color: '#ef4444',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '10px',
                  padding: '0.75rem 1.25rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: 600
                }}
              >
                <PhoneOff size={18} /> End Lesson
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
