import { createBrowserRouter } from 'react-router-dom';
import { RootLayout } from '@/components/layout/RootLayout';
import { HomePage } from '@/pages/HomePage';
import { ModelManagementPage } from '@/pages/ModelManagementPage';
import { MetricsPage } from '@/pages/MetricsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { AdminPage } from '@/pages/AdminPage/AdminPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import WebTUITest from '@/examples/WebTUITest';
import { CSSTestPage } from '@/pages/CSSTestPage';
import { SpinnerTestPage } from '@/pages/SpinnerTestPage';
import { DotMatrixTestPage } from '@/pages/DotMatrixTestPage';
import CRTEffectsTestPage from '@/pages/CRTEffectsTestPage';
import { OrchestratorTestPage } from '@/pages/OrchestratorTestPage';
import LiveEventFeedTestPage from '@/pages/LiveEventFeedTestPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'model-management',
        element: <ModelManagementPage />,
      },
      {
        path: 'metrics',
        element: <MetricsPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: 'admin',
        element: <AdminPage />,
      },
      {
        path: 'webtui-test',
        element: <WebTUITest />,
      },
      {
        path: 'css-test',
        element: <CSSTestPage />,
      },
      {
        path: 'spinner-test',
        element: <SpinnerTestPage />,
      },
      {
        path: 'dot-matrix-test',
        element: <DotMatrixTestPage />,
      },
      {
        path: 'crt-effects-test',
        element: <CRTEffectsTestPage />,
      },
      {
        path: 'orchestrator-test',
        element: <OrchestratorTestPage />,
      },
      {
        path: 'live-event-feed-test',
        element: <LiveEventFeedTestPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
