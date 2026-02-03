# Synapse Engine Frontend

React + TypeScript WebUI for Multi-Model Orchestration.

## Quick Start

### Development

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173

### Production Build

```bash
npm run build
npm run preview
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm test` | Run tests (Vitest) |
| `npm run lint` | Run ESLint |
| `npm run type-check` | TypeScript type checking |

## Project Structure

```
src/
├── animations/       # Animation utilities and effects
├── api/              # API client and endpoints
├── components/       # React components
│   ├── dashboard/    # Dashboard panels (metrics, status)
│   ├── terminal/     # Terminal-style components
│   └── ...
├── contexts/         # React contexts
├── hooks/            # Custom React hooks
├── pages/            # Page components
├── router/           # React Router configuration
├── stores/           # State management
├── types/            # TypeScript type definitions
└── utils/            # Utility functions
```

## Key Features

- **Dashboard** - Real-time model status and metrics
- **Query Interface** - Multi-mode query submission
- **Model Management** - Enable/disable models, tier assignment
- **Settings** - Runtime configuration UI
- **CGRAG Management** - Document indexing controls

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Chart.js** - Metrics visualization
- **React Flow** - Pipeline visualization

## Configuration

The frontend connects to the backend at `http://localhost:8000` by default.

For Docker deployment, nginx proxies API requests to the backend container.

## Development Notes

### Adding Components

1. Create component in `src/components/`
2. Add types to `src/types/` if needed
3. Export from component index if shared

### API Integration

Use hooks from `src/hooks/` for data fetching:

```tsx
import { useModels } from '../hooks/useModels';

function MyComponent() {
  const { models, loading, error } = useModels();
  // ...
}
```

### Styling

The UI uses a terminal-inspired aesthetic. See [WebTUI Style Guide](../docs/reference/WEBTUI_STYLE_GUIDE.md) for conventions.

## Related Documentation

- [WebTUI Style Guide](../docs/reference/WEBTUI_STYLE_GUIDE.md)
- [WebTUI Integration Guide](../docs/reference/WEBTUI_INTEGRATION_GUIDE.md)
- [API Reference](../docs/API.md)
