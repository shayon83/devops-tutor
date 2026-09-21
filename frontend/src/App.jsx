import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';
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

  const roomRef = useRef(null);
  const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    if (roomRef.current && isConnected) {
      roomRef.current.localParticipant.setMicrophoneEnabled(!isMuted);
    }
  }, [isMuted, isConnected]);

  const handleStartSession = async () => {
    setIsConnecting(true);
    const newSessionId = `devops-room-${Date.now().toString().slice(-6)}`;
    setSessionId(newSessionId);
    setVisualPayloads([]);

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

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      roomRef.current = room;

      room.on(RoomEvent.DataReceived, (payload) => {
        try {
          const str = new TextDecoder().decode(payload);
          const dataPayload = JSON.parse(str);
          console.log('DataTrack received:', dataPayload);
          setVisualPayloads(prev => [...prev, dataPayload]);
        } catch (e) {
          console.warn('DataTrack parse error:', e);
        }
      });

      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          const audioEl = track.attach();
          document.body.appendChild(audioEl);
          audioEl.play().catch(e => console.warn('Audio autoplay warning:', e));
        }
      });

      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          track.detach().forEach(el => el.remove());
        }
      });

      room.on(RoomEvent.TranscriptionReceived, (transcriptions, participant) => {
        transcriptions.forEach(t => {
          const rawText = t.text || '';
          
          // Strip out visual tags like [DIAGRAM: ...], [YAML: ...], [CARD: ...] from display transcript
          let cleanedText = rawText;
          let i = 0;
          while (i < cleanedText.length) {
            if (
              cleanedText.slice(i, i + 9) === '[DIAGRAM:' ||
              cleanedText.slice(i, i + 6) === '[YAML:' ||
              cleanedText.slice(i, i + 6) === '[CARD:'
            ) {
              let depth = 0;
              let j = i;
              while (j < cleanedText.length) {
                if (cleanedText[j] === '[') depth++;
                else if (cleanedText[j] === ']') {
                  depth--;
                  if (depth === 0) {
                    cleanedText = cleanedText.slice(0, i) + cleanedText.slice(j + 1);
                    break;
                  }
                }
                j++;
              }
              if (depth > 0) {
                // Truncate unclosed tag at end of streaming buffer
                cleanedText = cleanedText.slice(0, i);
                break;
              }
            } else {
              i++;
            }
          }
          cleanedText = cleanedText.trim();
          if (!cleanedText) return;

          const role = participant?.identity?.startsWith('student') ? 'user' : 'tutor';
          
          setTranscripts(prev => {
            if (prev.length === 0) {
              return [{ id: `turn-${Date.now()}`, role, text: cleanedText }];
            }

            const lastItem = prev[prev.length - 1];

            // If the last entry belongs to the SAME speaker role, update its text in-place
            if (lastItem.role === role) {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...lastItem,
                text: cleanedText
              };
              return updated;
            }

            // Otherwise, speaker role has changed: start a new speech turn line
            return [...prev, { id: `turn-${Date.now()}`, role, text: cleanedText }];
          });
        });
      });

      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
      });

      await room.connect(data.livekit_url, data.token);
      await room.localParticipant.setMicrophoneEnabled(true);

      setIsConnected(true);
      setTranscripts([
        { id: 'tutor-welcome', role: 'tutor', text: `Welcome! Let's explore ${selectedSubject}. What aspect would you like to start with?`, final: true }
      ]);
    } catch (e) {
      console.error("Connection error:", e);
      alert("Could not connect to LiveKit voice server. Please verify your LiveKit credentials in .env.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleEndSession = async () => {
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
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
