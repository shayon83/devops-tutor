import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { Code, FileText, Layout } from 'lucide-react';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif'
});

export default function VisualWorkspace({ visualPayloads, transcripts }) {
  const mermaidRef = useRef(null);
  const transcriptEndRef = useRef(null);
  const [activeDiagramIdx, setActiveDiagramIdx] = React.useState(null);

  const diagramPayloads = visualPayloads.filter(p => p.type === 'diagram');
  const yamlPayload = [...visualPayloads].reverse().find(p => p.type === 'yaml');
  const cardPayload = [...visualPayloads].reverse().find(p => p.type === 'card');

  // Auto-switch to the latest diagram whenever a new diagram arrives
  useEffect(() => {
    if (diagramPayloads.length > 0) {
      setActiveDiagramIdx(diagramPayloads.length - 1);
    }
  }, [diagramPayloads.length]);

  const activeDiagram = (activeDiagramIdx !== null && diagramPayloads[activeDiagramIdx])
    ? diagramPayloads[activeDiagramIdx]
    : [...visualPayloads].reverse().find(p => p.type === 'diagram');

  useEffect(() => {
    const renderDiagram = async () => {
      if (activeDiagram && mermaidRef.current) {
        try {
          mermaidRef.current.removeAttribute('data-processed');
          const id = `mermaid-svg-${Date.now()}`;
          const { svg } = await mermaid.render(id, activeDiagram.content);
          mermaidRef.current.innerHTML = svg;
        } catch (e) {
          console.warn("Mermaid render error:", e);
        }
      }
    };
    renderDiagram();
  }, [activeDiagram]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts]);

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Layout size={18} color="#00f2fe" /> Interactive DevOps Workspace
      </h2>

      {cardPayload && (
        <div style={{ background: 'rgba(0, 242, 254, 0.08)', border: '1px solid rgba(0, 242, 254, 0.2)', padding: '1rem', borderRadius: '10px' }}>
          <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: '0.25rem' }}>{cardPayload.title || 'Key Concept'}</h4>
          <p style={{ fontSize: '0.85rem' }}>{cardPayload.message || cardPayload.content}</p>
        </div>
      )}

      {/* Mermaid Diagram Rendering Area */}
      <div style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--bg-card-border)', borderRadius: '10px', padding: '1rem', minHeight: '180px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Layout size={14} /> LIVE ARCHITECTURE DIAGRAM
          </div>

          {/* Multi-diagram history tabs */}
          {diagramPayloads.length > 1 && (
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {diagramPayloads.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveDiagramIdx(idx)}
                  style={{
                    fontSize: '0.7rem',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--bg-card-border)',
                    background: activeDiagramIdx === idx ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.05)',
                    color: activeDiagramIdx === idx ? '#000' : '#fff',
                    fontWeight: activeDiagramIdx === idx ? 700 : 400,
                    cursor: 'pointer'
                  }}
                >
                  Diagram {idx + 1}
                </button>
              ))}
            </div>
          )}
        </div>

        <div ref={mermaidRef} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', overflowX: 'auto' }}>
          {!activeDiagram && (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Architectural diagrams rendered automatically during voice conversation...
            </p>
          )}
        </div>
      </div>

      {/* YAML / Code Preview Area */}
      {yamlPayload && (
        <div style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid var(--bg-card-border)', borderRadius: '10px', padding: '1rem', fontFamily: 'var(--font-mono)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-emerald)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Code size={14} /> MANIFEST PREVIEW
          </div>
          <pre style={{ fontSize: '0.8rem', color: '#e5e7eb', overflowX: 'auto', margin: 0 }}>
            {yamlPayload.content}
          </pre>
        </div>
      )}

      {/* Live Transcript Stream */}
      <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--bg-card-border)', borderRadius: '10px', padding: '1rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <FileText size={14} /> LIVE TRANSCRIPT & NOTES
        </div>
        {transcripts.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No transcripts recorded yet.</p>
        ) : (
          transcripts.map((t, idx) => (
            <div key={t.id || idx} style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <strong style={{ color: t.role === 'tutor' ? 'var(--accent-cyan)' : 'var(--accent-emerald)' }}>
                {t.role === 'tutor' ? 'Tutor' : 'You'}:
              </strong> {t.text}
            </div>
          ))
        )}
        <div ref={transcriptEndRef} />
      </div>
    </div>
  );
}
