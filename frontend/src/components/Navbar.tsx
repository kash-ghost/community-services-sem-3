import React from "react";
import { Activity, Database } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  dbConnected: boolean;
  modelVersion: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  dbConnected,
  modelVersion,
}) => {
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "map", label: "Interactive Flood Map" },
    { id: "data", label: "Data Explorer" },
    { id: "model", label: "Model Lab" },
    { id: "location", label: "Location Analysis" },
    { id: "history", label: "Prediction History" },
  ];

  return (
    <header className="border-b border-dark-800 bg-dark-900 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Area Title */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-dark-800 border border-dark-700 flex items-center justify-center text-accent-cyan font-mono font-bold text-sm">
              GU
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">
                Gurugram Flood Vulnerability Framework
              </div>
              <div className="text-xs text-slate-400 font-mono">
                Haryana, India · Decision Support System
              </div>
            </div>
          </div>

          {/* Navigation items */}
          <nav className="hidden md:flex items-center gap-1">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                    isActive
                      ? "bg-dark-800 text-accent-cyan border border-dark-700"
                      : "text-slate-300 hover:text-white hover:bg-dark-850"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Status indicators */}
          <div className="flex items-center gap-3 text-xs font-mono">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-dark-850 border border-dark-800 text-slate-300">
              <Activity className="w-3 h-3 text-accent-cyan" />
              <span>{modelVersion}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-dark-850 border border-dark-800">
              <Database
                className={`w-3 h-3 ${
                  dbConnected ? "text-emerald-400" : "text-amber-400"
                }`}
              />
              <span className={dbConnected ? "text-slate-300" : "text-amber-300"}>
                {dbConnected ? "Mongo Connected" : "Local File Fallback"}
              </span>
            </div>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden overflow-x-auto py-2 gap-1 border-t border-dark-800">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`whitespace-nowrap px-2.5 py-1 text-xs font-medium rounded ${
                  isActive
                    ? "bg-dark-800 text-accent-cyan border border-dark-700"
                    : "text-slate-400"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
