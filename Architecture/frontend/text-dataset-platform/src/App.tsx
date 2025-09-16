/**
 * Main App Component
 * Root component with routing, authentication, and global providers
 */

import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';

// Layout Components
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/layout/AuthLayout';
import LoadingSpinner from './components/ui/LoadingSpinner';
import ErrorBoundary from './components/error/ErrorBoundary';

// Authentication Components
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';

// Protected Route Component
import ProtectedRoute from './components/auth/ProtectedRoute';

// Lazy-loaded Page Components
import { LazyComponents } from './utils/bundleOptimization';

// Services and Stores
import { webSocketService } from './services/webSocketService';
import { useAppStore } from './stores/appStore';
import { useRealTimeStores } from './stores/realTimeStore';
import { initializeBundleOptimizations } from './utils/bundleOptimization';

// Styles
import './styles/globals.css';
import './styles/components.css';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

// App Shell Component
const AppShell: React.FC = () => {
  const { user, isAuthenticated, initializeAuth } = useAppStore();
  const { connectionStore } = useRealTimeStores();

  useEffect(() => {
    // Initialize authentication on app start
    initializeAuth();

    // Initialize bundle optimizations
    initializeBundleOptimizations();

    // Initialize WebSocket connection if user is authenticated
    if (isAuthenticated && user?.accessToken) {
      webSocketService.connect(user.accessToken).catch(console.error);
    }

    // Cleanup on unmount
    return () => {
      webSocketService.disconnect();
    };
  }, [isAuthenticated, user?.accessToken, initializeAuth]);

  // Show loading screen during initial auth check
  if (user === undefined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Initializing application...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        {/* Public Authentication Routes */}
        <Route
          path="/auth/*"
          element={
            <AuthLayout>
              <Routes>
                <Route path="login" element={<LoginPage />} />
                <Route path="register" element={<RegisterPage />} />
                <Route path="forgot-password" element={<ForgotPasswordPage />} />
                <Route path="verify-email" element={<VerifyEmailPage />} />
                <Route path="*" element={<Navigate to="/auth/login" replace />} />
              </Routes>
            </AuthLayout>
          }
        />

        {/* Protected Application Routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingSpinner size="lg" />}>
                  <Routes>
                    {/* Dashboard - Default Route */}
                    <Route 
                      path="/" 
                      element={<Navigate to="/dashboard" replace />} 
                    />
                    <Route 
                      path="/dashboard" 
                      element={<LazyComponents.Dashboard />} 
                    />

                    {/* Document Management */}
                    <Route 
                      path="/upload" 
                      element={<LazyComponents.Upload />} 
                    />
                    <Route 
                      path="/documents" 
                      element={<LazyComponents.Dashboard />} // Reuse dashboard with documents view
                    />

                    {/* AI Chat Assistant */}
                    <Route 
                      path="/chat" 
                      element={<LazyComponents.Chat />} 
                    />
                    <Route 
                      path="/chat/:sessionId" 
                      element={<LazyComponents.Chat />} 
                    />

                    {/* Analytics and Reports */}
                    <Route 
                      path="/analytics" 
                      element={<LazyComponents.Analytics />} 
                    />

                    {/* Projects */}
                    <Route 
                      path="/projects" 
                      element={<LazyComponents.Dashboard />} // Reuse with projects view
                    />
                    <Route 
                      path="/projects/:projectId" 
                      element={<LazyComponents.Dashboard />} 
                    />

                    {/* User Settings */}
                    <Route 
                      path="/settings" 
                      element={<LazyComponents.Settings />} 
                    />
                    <Route 
                      path="/settings/:tab" 
                      element={<LazyComponents.Settings />} 
                    />

                    {/* Help and Support */}
                    <Route 
                      path="/help" 
                      element={<LazyComponents.Settings />} // Reuse with help view
                    />

                    {/* 404 Route */}
                    <Route 
                      path="*" 
                      element={
                        <div className="min-h-screen flex items-center justify-center">
                          <div className="text-center">
                            <h1 className="text-6xl font-bold text-gray-400">404</h1>
                            <p className="text-xl text-gray-600 mt-4">Page not found</p>
                            <button
                              onClick={() => window.history.back()}
                              className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                            >
                              Go Back
                            </button>
                          </div>
                        </div>
                      } 
                    />
                  </Routes>
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
};

// Main App Component with Providers
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppShell />
        
        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              style: {
                background: '#10b981',
              },
            },
            error: {
              style: {
                background: '#ef4444',
              },
            },
          }}
        />

        {/* Development Tools */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
