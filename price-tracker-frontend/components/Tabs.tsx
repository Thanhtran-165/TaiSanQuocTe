/**
 * Tabs Component
 * Tab navigation with liquid glass styling
 */

import React from 'react';

interface TabsProps {
  tabs: { id: string; label: string; icon: string }[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`
            px-6 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap
            ${
              activeTab === tab.id
                ? 'glass-card text-white border-white/30'
                : 'glass-panel text-white/60 hover:text-white hover:border-white/20'
            }
          `}
        >
          <span className="mr-2">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  );
}
