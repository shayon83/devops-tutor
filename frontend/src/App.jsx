import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import VoiceControlPanel from './components/VoiceControlPanel';
import VisualWorkspace from './components/VisualWorkspace';
import FeedbackModal from './components/FeedbackModal';

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState("Kubernetes & Container Orchestration");
  const [sessionId, setSessionId] = useState("");
  const [visualPayloads, setVisualPayloads] = useState([]);
  const [transcripts, setTranscripts] = useState([]);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);

  const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  const handleStartSession = async () => {
    setIsConnecting(true);
    const newSessionId = `devops-room-${Date.now().toString().slice(-6)}`;
    setSessionId(newSessionId);

    try {
      const res = await fetch(`${API_BASE}/api/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: newSessionId,
          participant_identity: `student-${Math.floor(Math.random() * 1000)}`,
          subject: selectedSubject
        })
      });

      if (!res.ok) throw new Error('Token generation failed');
      const data = await res.json();
      console.log('Obtained LiveKit token:', data);

      setIsConnected(true);
      setTranscripts([
        { role: 'tutor', text: `Welcome! Let's explore ${selectedSubject}. What aspect would you like to start with?` }
      ]);
    } catch (e) {
      console.error("Connection error:", e);
      alert("Could not connect to voice backend API. Ensure backend is running.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleEndSession = () => {
    setIsConnected(false);
    setIsFeedbackOpen(true);
  };

  const handleSubmitFeedback = async (feedbackData) => {
    try {
      await fetch(`${API_BASE}/api/session/${sessionId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
      });
      console.log("Feedback submitted successfully");
    } catch (e) {
      console.error("Feedback submit error:", e);
    }
  };

  return (
    <div className="app-container">
      <Header 
        isConnected={isConnected} 
        selectedSubject={selectedSubject} 
        setSelectedSubject={setSelectedSubject} 
      />

      <main className="main-workspace">
        <VoiceControlPanel 
          isConnected={isConnected}
          isMuted={isMuted}
          setIsMuted={setIsMuted}
          onStartSession={handleStartSession}
          onEndSession={handleEndSession}
          isConnecting={isConnecting}
        />

        <VisualWorkspace 
          visualPayloads={visualPayloads} 
          transcripts={transcripts} 
        />
      </main>

      <FeedbackModal 
        isOpen={isFeedbackOpen}
        onClose={() => setIsFeedbackOpen(false)}
        onSubmitFeedback={handleSubmitFeedback}
        sessionId={sessionId}
      />
    </div>
  );
}
