/**
 * NotFound Page (404)
 * Displayed when user navigates to invalid route
 */

import { useNavigate } from 'react-router-dom';
import { Button } from '../components';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-2xl w-full text-center">
        <div className="text-9xl mb-6">🎬</div>
        <h1 className="text-6xl font-bold text-gray-800 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">
          Page Not Found
        </h2>
        <p className="text-gray-600 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-4 justify-center">
          <Button onClick={() => navigate(-1)} variant="secondary">
            Go Back
          </Button>
          <Button onClick={() => navigate('/')}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
