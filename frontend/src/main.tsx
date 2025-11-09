import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import log from './utils/logger';

// Import global styles (CSS layer system)
import './assets/styles/main.css';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

log.info('S.Y.N.A.P.S.E. INTERFACE initializing...');

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
