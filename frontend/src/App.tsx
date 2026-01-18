import { ChatKit, useChatKit } from '@openai/chatkit-react';
import { useState, useEffect, CSSProperties } from 'react';
import './App.css';

// Branding configuration type
interface Branding {
  name: string;
  tagline: string;
  logoUrl: string;
  primaryColor: string;
  faviconUrl: string;
}

// Helper to adjust color brightness
function adjustColor(color: string, amount: number): string {
  const hex = color.replace('#', '');
  const num = parseInt(hex, 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount));
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount));
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

function App() {
  const [branding, setBranding] = useState<Branding | null>(null);

  // Load branding from backend
  useEffect(() => {
    fetch('/api/branding')
      .then(res => res.json())
      .then(data => setBranding(data))
      .catch(err => console.error('Failed to load branding:', err));
  }, []);

  // ChatKit hook - connects to our self-hosted backend
  const { control } = useChatKit({
    api: {
      // For self-hosted ChatKit, we use url and domainKey
      url: '/chatkit',
      domainKey: 'localhost', // Local development
    },
    // Start screen customization
    startScreen: {
      greeting: branding?.tagline || 'Your AI-powered task management assistant',
      prompts: [
        { label: '📋 Show my todos', prompt: 'Show me my todos' },
        { label: '🛒 Add buy groceries', prompt: 'Add buy groceries to my todo list' },
        { label: '📝 Add multiple tasks', prompt: 'Add three tasks: call mom, finish report, and exercise' },
        { label: '❓ What can you do?', prompt: 'What can you help me with?' },
      ],
    },
    // Header configuration
    header: {
      title: {
        text: branding?.name || 'ChatKit Todo',
      },
    },
    // Composer configuration
    composer: {
      placeholder: "Try: 'Show me my todos' to see interactive widgets...",
    },
  });

  // Dynamic header styles
  const headerStyle: CSSProperties = {
    background: branding?.primaryColor
      ? `linear-gradient(135deg, ${branding.primaryColor}, ${adjustColor(branding.primaryColor, -20)})`
      : 'linear-gradient(135deg, #0078d4, #005a9e)',
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header" style={headerStyle}>
        <div className="header-logo">
          {branding?.logoUrl ? (
            <img src={branding.logoUrl} alt="Logo" />
          ) : (
            <span>✅</span>
          )}
        </div>
        <h1 className="header-title">{branding?.name || 'ChatKit Todo'}</h1>
        <span className="header-tagline">{branding?.tagline || 'AI-Powered Task Management'}</span>
      </header>

      {/* Main content with sidebar and ChatKit */}
      <div className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          <section>
            <h2>📖 How to Use</h2>
            <ul>
              <li>💬 Ask me to add tasks to your todo list</li>
              <li>📋 Say "show my todos" to see the interactive widget</li>
              <li>✅ Click checkboxes or buttons to manage tasks</li>
              <li>🗑️ Delete tasks you no longer need</li>
            </ul>
          </section>

          <section>
            <h2>✨ Features</h2>
            <ul>
              <li>🎨 Official ChatKit React UI</li>
              <li>📝 Interactive widget forms</li>
              <li>☑️ Checkbox to toggle completion</li>
              <li>🔘 Action buttons (complete, delete)</li>
              <li>💾 Persistent storage</li>
              <li>☁️ Azure OpenAI powered</li>
            </ul>
          </section>
        </aside>

        {/* ChatKit Component - Official OpenAI ChatKit UI */}
        <div className="chat-container">
          <ChatKit control={control} className="chatkit-widget" />
        </div>
      </div>
    </div>
  );
}

export default App;
