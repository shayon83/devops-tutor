import React from 'react';
import { Terminal, Shield, Cpu } from 'lucide-react';

export default function Header({ isConnected, selectedSubject, setSelectedSubject }) {
  const subjects = [
    "Kubernetes & Container Orchestration",
    "CI/CD & GitOps Workflows",
    "Observability, Prometheus & Grafana",
    "Infrastructure as Code (Terraform)",
    "Linux Systems & SRE Incident Response"
  ];

  return (
    <header className="glass-panel" style={{ padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ padding: '0.5rem', background: 'rgba(0, 242, 254, 0.1)', borderRadius: '10px', border: '1px solid rgba(0, 242, 254, 0.2)' }}>
          <Terminal size={24} color="#00f2fe" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.025em' }}>DevOps Voice Tutor</h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real-Time Socratic AI Learning Platform</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <select 
          value={selectedSubject} 
          onChange={(e) => setSelectedSubject(e.target.value)}
          disabled={isConnected}
          style={{
            background: 'rgba(0,0,0,0.4)',
            color: 'var(--text-main)',
            border: '1px solid var(--bg-card-border)',
            borderRadius: '8px',
            padding: '0.5rem 1rem',
            fontFamily: 'inherit',
            fontSize: '0.85rem'
          }}
        >
          {subjects.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '0.4rem 0.8rem', borderRadius: '20px' }}>
          <div className={isConnected ? "pulse-circle" : ""} style={!isConnected ? { width: 10, height: 10, borderRadius: '50%', background: '#6b7280' } : {}} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isConnected ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
            {isConnected ? 'LIVE SESSION' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
}
