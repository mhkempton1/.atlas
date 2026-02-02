import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Mail,
  BookOpen,
  Settings,
  Menu,
  X,
  User,
  LogOut,
  ShieldCheck,
  FolderGit2,
  Calendar,
  Activity,
  Network,
  History as HistoryIcon,
  Navigation
} from 'lucide-react';
import EmailScanner from './components/EmailScanner';
import SystemHealthView from './components/dashboard/SystemHealthView';
import SchedulerView from './components/dashboard/SchedulerView';
import ComposeDraft from './components/email/ComposeDraft';
import EmailModule from './components/email/EmailModule';
import KnowledgeDashboard from './components/knowledge/KnowledgeDashboard';
import Dashboard from './components/dashboard/Dashboard';
import DocumentControl from './components/documents/DocumentControl';
import CalendarModule from './components/calendar/CalendarModule';
import TaskList from './components/tasks/TaskList';
import AltimeterTaskView from './components/tasks/AltimeterTaskView';
import PortcullisView from './components/gatekeeper/PortcullisView';
import HistoryView from './components/history/HistoryView';
import SystemConfig from './components/config/SystemConfig';
import ReportsDashboard from './components/reporting/ReportsDashboard';
import CommandBar from './components/shared/CommandBar';
import { SYSTEM_API } from './services/api';

// ... imports

const MODULES = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard, minStrata: 1 },
  { id: 'procedures', label: 'The Library', icon: BookOpen, minStrata: 1 }, // Consolidated Knowledge & SOPs
  { id: 'docs', label: 'Document Control', icon: FolderGit2, minStrata: 3 },
  { id: 'email', label: 'Email Control', icon: Mail, minStrata: 1 },
  { id: 'tasks', label: 'Mission Tasks', icon: ShieldCheck, minStrata: 1 },
  { id: 'alt_tasks', label: 'Altimeter Ops', icon: Network, minStrata: 1 },
  { id: 'schedule', label: 'Dept Schedule', icon: Calendar, minStrata: 1 },
  { id: 'reports', label: 'System Reports', icon: BookOpen, minStrata: 2 },
  { id: 'history', label: 'System Logs', icon: HistoryIcon, minStrata: 1 },
  { id: 'sys_health', label: 'System Health', icon: ShieldCheck, minStrata: 4 },
  { id: 'config', label: 'System Config', icon: Settings, minStrata: 4 },
];

function App() {
  const [currentModule, setCurrentModule] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCommandBarOpen, setIsCommandBarOpen] = useState(false);

  // Permissions Logic
  // In a real app, this comes from the backend/auth context
  const currentUser = {
    name: "Michael Kempton",
    role: "Administrator",
    strata: 5 // 4+ = Admin/System Access
  };

  // Global keyboard shortcut for Command Bar (Alt+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.altKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandBarOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Preload critical data on mount
  useEffect(() => {
    const preloadData = async () => {
      try {
        // Preload dashboard stats and health in background
        await Promise.all([
          SYSTEM_API.getDashboardStats().catch(() => null),
          SYSTEM_API.checkHealth().catch(() => null),
        ]);
      } catch {
        console.log('Preload completed with some errors');
      }
    };
    preloadData();
  }, []);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  const navigateTo = (moduleId, params = {}) => {
    setCurrentModule(moduleId);
    setIsSidebarOpen(false);

    const url = new URL(window.location.href);
    url.searchParams.set('module', moduleId);

    // Clear other params except module initially, unless specified
    // Actually better to just set provided params
    Object.keys(params).forEach(key => url.searchParams.set(key, params[key]));

    window.history.pushState({ moduleId, params }, "", url.toString());
  };

  // Sync state with back button and URL on mount
  React.useEffect(() => {
    // Initial sync from URL
    const params = new URLSearchParams(window.location.search);
    const moduleFromUrl = params.get('module');
    if (moduleFromUrl && MODULES.some(m => m.id === moduleFromUrl)) {
      setCurrentModule(moduleFromUrl);
    }

    const handlePopState = (event) => {
      if (event.state && event.state.moduleId) {
        setCurrentModule(event.state.moduleId);
      } else {
        // Double check URL on popstate if no state object
        const p = new URLSearchParams(window.location.search);
        const m = p.get('module');
        if (m && MODULES.some(mod => mod.id === m)) {
          setCurrentModule(m);
        } else {
          setCurrentModule('dashboard');
        }
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Filter Modules by Access
  const accessibleModules = MODULES.filter(m => currentUser.strata >= m.minStrata);

  const renderContent = () => {
    switch (currentModule) {
      case 'dashboard':
        return <Dashboard onNavigate={navigateTo} />;
      case 'email':
        return (
          <div className="max-w-7xl mx-auto h-full">
            <EmailModule />
          </div>
        );
      case 'calendar_google':
        return <CalendarModule />;
      case 'schedule':
        return <SchedulerView />;
      case 'tasks':
        return <TaskList />;
      case 'alt_tasks':
        return <AltimeterTaskView />;
      case 'history':
        return <HistoryView />;
      case 'sys_health':
        return <SystemHealthView />;
      case 'config':
        return <SystemConfig />;
      case 'procedures':
        return <KnowledgeDashboard />;
      case 'docs':
        return <DocumentControl />;
      case 'portcullis':
        return <PortcullisView />;
      case 'reports':
        return <ReportsDashboard />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-[60vh] text-text-muted">
            <Settings className="w-16 h-16 mb-4 animate-spin-slow opacity-50" />
            <h2 className="text-xl font-semibold">System Module: {currentModule}</h2>
            <p>Configuration panel initialization pending.</p>
          </div>
        );
    }
  };

  return (
    <div className="app-container">
      {/* --- Top Navigation --- */}
      <nav className="top-nav">
        <div className="brand text-yellow-300 font-black tracking-widest text-2xl" style={{ color: '#fbbf24', textShadow: '0 0 20px rgba(251, 191, 36, 0.4)', cursor: 'pointer' }} onClick={() => navigateTo('dashboard')}>
          ATLAS
        </div>

        <div className="nav-controls">
          <div className="user-badge" onClick={() => navigateTo('config')}>
            <div className="badge-initials">MK</div>
            <div className="badge-details">
              <span className="user-name">{currentUser.name}</span>
              <span className="user-role">{currentUser.role} (Strata {currentUser.strata})</span>
            </div>
          </div>
          <div className="hamburger" onClick={toggleSidebar}>
            <Menu className="w-6 h-6" />
          </div>
        </div>
      </nav>

      {/* --- Sidebar Overlay --- */}
      {isSidebarOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar}>
          <div className="menu-sidebar animate-slide-in-right" onClick={e => e.stopPropagation()}>
            <div className="menu-header">SYSTEM NAVIGATION</div>

            <div className="flex-1">
              {accessibleModules.map(module => (
                <div
                  key={module.id}
                  className={`nav-item ${currentModule === module.id ? 'active' : ''}`}
                  onClick={() => navigateTo(module.id)}
                >
                  <module.icon className="w-5 h-5" />
                  {module.label}
                </div>
              ))}
            </div>

            <div className="mt-auto pt-4 border-t border-border">
              <div className="nav-item text-red-400 hover:bg-red-500/10 hover:border-red-500/30">
                <LogOut className="w-5 h-5" />
                Disconnect Session
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- Main Content Area --- */}
      <main className="main-content">
        {renderContent()}
      </main>

      {/* --- Global Command Bar --- */}
      <CommandBar
        isOpen={isCommandBarOpen}
        onClose={() => setIsCommandBarOpen(false)}
        onNavigate={navigateTo}
        modules={accessibleModules}
      />
    </div>
  );
}

export default App;
