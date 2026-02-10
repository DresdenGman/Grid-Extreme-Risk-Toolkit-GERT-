import React from 'react';
import { createRoot } from 'react-dom/client';
import { Activity } from 'lucide-react';

const App = () => {
  return (
    <div style={{ textAlign: 'center', padding: '2rem', maxWidth: '600px' }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
        <div style={{ color: '#6366f1', background: 'rgba(99, 102, 241, 0.1)', padding: '12px', borderRadius: '12px' }}>
           <Activity size={48} />
        </div>
      </div>
      
      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#fff' }}>
        Grid Extreme Risk Toolkit
      </h1>
      
      <p style={{ color: '#94a3b8', lineHeight: '1.6', marginBottom: '2rem' }}>
        The system backend is initializing. <br/>
        If you are seeing this screen, the environment is loading the static entry point.
      </p>

      <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '1rem', borderRadius: '8px', textAlign: 'left' }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#cbd5e1' }}>
          <strong>Status:</strong> <span style={{ color: '#10b981' }}>● System Active</span>
        </p>
        <p style={{ margin: '8px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
          Please wait for the Next.js server to takeover, or ensure you are viewing the application on port 3000.
        </p>
      </div>
    </div>
  );
};

const root = createRoot(document.getElementById('root') as HTMLElement);
root.render(<App />);