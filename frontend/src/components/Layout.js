import React, { useState } from 'react';
import Navigation from './Navigation';
import AICompanion from './AICompanion';
import { Toaster } from 'react-hot-toast';

const Layout = ({ children }) => {
  const [isAICompanionOpen, setIsAICompanionOpen] = useState(false);

  const toggleAICompanion = () => {
    setIsAICompanionOpen(!isAICompanionOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
      
      {/* AI Learning Companion */}
      <AICompanion 
        isOpen={isAICompanionOpen} 
        onToggle={toggleAICompanion}
      />
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#ffffff',
            color: '#374151',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            border: '1px solid #e5e7eb',
          },
        }}
      />
    </div>
  );
};

export default Layout;