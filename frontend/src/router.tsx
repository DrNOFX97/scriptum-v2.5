/**
 * React Router Configuration
 * Defines all application routes
 */

import { createBrowserRouter } from 'react-router-dom';
import App from './App';

// Pages
import Dashboard from './pages/Dashboard';
import SubtitleSearch from './pages/SubtitleSearch';
import TranslationPage from './pages/TranslationPage';
import SyncPage from './pages/SyncPage';
import NotFound from './pages/NotFound';

/**
 * Application Router
 * Based on the sitemap architecture
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <NotFound />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: '/subtitles/search',
        element: <SubtitleSearch />,
      },
      {
        path: '/translate',
        element: <TranslationPage />,
      },
      {
        path: '/sync',
        element: <SyncPage />,
      },
      // Future routes will be added here following the sitemap:
      // - /project/:id
      // - /project/:id/video
      // - /project/:id/subtitles/*
      // - /project/:id/translate
      // - /project/:id/sync
      // - /project/:id/player
      // - /project/:id/metadata
      // - /project/:id/export
    ],
  },
]);
