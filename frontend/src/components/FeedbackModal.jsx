import React, { useState } from 'react';
import { Star, Check, X } from 'lucide-react';

export default function FeedbackModal({ isOpen, onClose, onSubmitFeedback, sessionId }) {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [selectedTags, setSelectedTags] = useState(["Clear Explanations", "Great Pacing"]);
  const [comment, setComment] = useState("");

  if (!isOpen) return null;

  const availableTags = [
    "Clear Explanations",
    "Great Pacing",
    "Helpful Diagrams",
    "Good Socratic Questions",
    "Too Fast",
    "Tutor Interrupted Me"
  ];

  const toggleTag = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const handleSubmit = () => {
    onSubmitFeedback({
      sessionId,
      rating_stars: rating,
      tags: selectedTags,
      comment
    });
    onClose();
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
      <div className="glass-panel" style={{ width: '90%', maxWidth: '500px', padding: '2rem', position: 'relative' }}>
        <button onClick={onClose} style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
          <X size={20} />
        </button>

        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem', textAlign: 'center' }}>How was your tutoring session?</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '1.5rem' }}>
          Your feedback helps optimize latency, pacing, and Socratic quality metrics.
        </p>

        {/* Star Rating Bar */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              onClick={() => setRating(star)}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <Star 
                size={32} 
                fill={(hoverRating || rating) >= star ? "#f59e0b" : "none"} 
                color={(hoverRating || rating) >= star ? "#f59e0b" : "#4b5563"} 
              />
            </button>
          ))}
        </div>

        {/* Quick Tag Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
          {availableTags.map((tag) => {
            const isSelected = selectedTags.includes(tag);
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                style={{
                  background: isSelected ? 'rgba(0, 242, 254, 0.2)' : 'rgba(255,255,255,0.05)',
                  color: isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--bg-card-border)',
                  borderRadius: '20px',
                  padding: '0.4rem 0.8rem',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem'
                }}
              >
                {isSelected && <Check size={12} />} {tag}
              </button>
            );
          })}
        </div>

        {/* Optional Comment */}
        <textarea
          placeholder="Optional notes or observations..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          style={{
            width: '100%',
            background: 'rgba(0,0,0,0.4)',
            border: '1px solid var(--bg-card-border)',
            borderRadius: '8px',
            padding: '0.75rem',
            color: '#fff',
            fontFamily: 'inherit',
            fontSize: '0.85rem',
            marginBottom: '1.5rem'
          }}
        />

        <button className="glow-button" style={{ width: '100%', justifyContent: 'center' }} onClick={handleSubmit}>
          Submit Session Feedback
        </button>
      </div>
    </div>
  );
}
