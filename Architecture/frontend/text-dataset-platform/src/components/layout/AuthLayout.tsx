/**
 * Auth Layout Component
 * Layout wrapper for authentication pages
 */

import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-100 -z-10" />
      
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden -z-10">
        <div className="absolute -top-40 -right-32 w-96 h-96 rounded-full bg-blue-200 opacity-20 blur-3xl" />
        <div className="absolute -bottom-40 -left-32 w-96 h-96 rounded-full bg-purple-200 opacity-20 blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default AuthLayout;