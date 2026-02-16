import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Mail,
  BookOpen,
  Settings,
  Menu,
  LogOut,
  ShieldCheck,
  FolderGit2,
  Calendar,
  Activity,
  Network,
  History as HistoryIcon,
} from 'lucide-react';
import SystemHealthView from './components/dashboard/SystemHealthView';
import SchedulerView from './components/dashboard/SchedulerView';
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
import SystemStatusView from './components/system/SystemStatusView';
import { SYSTEM_API } from './services/api';
import NotificationCenter from './components/system/NotificationCenter';
import ErrorBoundary from './components/ErrorBoundary';

const MODULES = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard, minStrata: 1 },
  { id: 'procedures', label: 'The Library', icon: BookOpen, minStrata: 1 },
  { id: 'docs', label: 'Document Control', icon: FolderGit2, minStrata: 3 },
  { id: 'email', label: 'Email Control', icon: Mail, minStrata: 1 },
  { id: 'tasks', label: 'Mission Tasks', icon: ShieldCheck, minStrata: 1 },
  { id: 'alt_tasks', label: 'Altimeter Ops', icon: Network, minStrata: 1 },
  { id: 'schedule', label: 'Dept Schedule', icon: Calendar, minStrata: 1 },
  { id: 'reports', label: 'System Reports', icon: BookOpen, minStrata: 2 },
  { id: 'history', label: 'System Logs', icon: HistoryIcon, minStrata: 1 },
  { id: 'system_status', label: 'System Status', icon: Activity, minStrata: 1 },
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

  // Global State for Ubiquity
  const [globalHealth, setGlobalHealth] = useState(() => JSON.parse(localStorage.getItem('system_health')) || { status: 'online', health_percentage: 100 });
  const [notifications, setNotifications] = useState([]);
  const unreadCount = notifications.filter(n => !n.is_read).length;

  const fetchNotifications = async () => {
    try {
      const data = await SYSTEM_API.getNotifications(false);
      setNotifications(data);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await SYSTEM_API.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm("Clear all notifications?")) return;
    try {
      await SYSTEM_API.clearNotifications();
      setNotifications([]);
    } catch (err) {
      console.error("Failed to clear notifications:", err);
    }
  };

  // Preload and Sync Data
  useEffect(() => {
    const syncData = async () => {
      try {
        const health = await SYSTEM_API.checkHealth().catch(() => ({ status: 'offline' }));
        setGlobalHealth(health);
        localStorage.setItem('system_health', JSON.stringify(health));

        fetchNotifications();
        // Warm up stats/weather in background
        SYSTEM_API.getDashboardStats().catch(() => null);
      } catch {
        // Silent fail
      }
    };
    syncData();

    // Polling every 30s for notifications/health
    const interval = setInterval(syncData, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  const navigateTo = (moduleId, params = {}) => {
    setCurrentModule(moduleId);
    setIsSidebarOpen(false);

    const url = new URL(window.location.href);
    url.searchParams.set('module', moduleId);

    // Clear other params except module initially, unless specified
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

    const handleAppNavigate = (e) => {
      if (e.detail && e.detail.moduleId) {
        navigateTo(e.detail.moduleId, e.detail.params || {});
      }
    };
    window.addEventListener('app-navigate', handleAppNavigate);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('app-navigate', handleAppNavigate);
    };
  }, []);

  // Filter Modules by Access
  const accessibleModules = MODULES.filter(m => currentUser.strata >= m.minStrata);

  const renderContent = () => {
    switch (currentModule) {
      case 'dashboard':
        return (
          <ErrorBoundary name="Command Center">
            <Dashboard onNavigate={navigateTo} globalHealth={globalHealth} />
          </ErrorBoundary>
        );
      case 'email':
        return (
          <ErrorBoundary name="Email Control">
            <div className="max-w-7xl mx-auto h-full">
              <EmailModule />
            </div>
          </ErrorBoundary>
        );
      case 'calendar_google':
        return (
          <ErrorBoundary name="Calendar">
            <CalendarModule />
          </ErrorBoundary>
        );
      case 'schedule':
        return (
          <ErrorBoundary name="Dept Schedule">
            <SchedulerView />
          </ErrorBoundary>
        );
      case 'tasks':
        return (
          <ErrorBoundary name="Mission Tasks">
            <TaskList />
          </ErrorBoundary>
        );
      case 'alt_tasks':
        return (
          <ErrorBoundary name="Altimeter Ops">
            <AltimeterTaskView />
          </ErrorBoundary>
        );
      case 'history':
        return (
          <ErrorBoundary name="System Logs">
            <HistoryView />
          </ErrorBoundary>
        );
      case 'sys_health':
        return (
          <ErrorBoundary name="System Health">
            <SystemHealthView />
          </ErrorBoundary>
        );
      case 'config':
        return (
          <ErrorBoundary name="System Config">
            <SystemConfig />
          </ErrorBoundary>
        );
      case 'procedures':
        return (
          <ErrorBoundary name="The Library">
            <KnowledgeDashboard />
          </ErrorBoundary>
        );
      case 'docs':
        return (
          <ErrorBoundary name="Document Control">
            <DocumentControl />
          </ErrorBoundary>
        );
      case 'portcullis':
        return (
          <ErrorBoundary name="Gatekeeper">
            <PortcullisView />
          </ErrorBoundary>
        );
      case 'reports':
        return (
          <ErrorBoundary name="System Reports">
            <ReportsDashboard />
          </ErrorBoundary>
        );
      case 'system_status':
        return (
          <ErrorBoundary name="System Status">
            <SystemStatusView onNavigate={navigateTo} />
          </ErrorBoundary>
        );
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
      <nav className="top-nav bg-white/[0.02] backdrop-blur-2xl border-b border-white/5">
        <div className="brand text-yellow-300 font-black tracking-widest text-2xl" style={{ color: '#fbbf24', textShadow: '0 0 20px rgba(251, 191, 36, 0.4)', cursor: 'pointer' }} onClick={() => navigateTo('dashboard')}>
          ATLAS
        </div>

        <div className="nav-controls">
          <button
            onClick={() => navigateTo('system_status')}
            className="px-4 py-2 rounded-xl border transition-all flex items-center gap-2 font-mono text-sm font-bold uppercase tracking-wider hover:scale-105"
            style={{
              borderColor: `rgb(${Math.round(252 + (16 - 252) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(211 + (185 - 211) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(77 + (139 - 77) * ((globalHealth?.health_percentage || 0) / 100))})`,
              color: `rgb(${Math.round(252 + (16 - 252) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(211 + (185 - 211) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(77 + (139 - 77) * ((globalHealth?.health_percentage || 0) / 100))})`,
              backgroundColor: `rgba(${Math.round(252 + (16 - 252) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(211 + (185 - 211) * ((globalHealth?.health_percentage || 0) / 100))}, ${Math.round(77 + (129 - 77) * ((globalHealth?.health_percentage || 0) / 100))}, 0.1)`
            }}
          >
            <Activity className="w-4 h-4" />
            ONLINE [{globalHealth?.health_percentage || 0}%]
          </button>

          <NotificationCenter
            notifications={notifications}
            onMarkRead={handleMarkRead}
            onClearAll={handleClearAll}
          />

          <div className="user-badge relative group" onClick={() => navigateTo('config')}>
            <div className="badge-initials relative">
              MK
              {unreadCount > 0 && (
                <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-[10px] font-black rounded-full flex items-center justify-center border-2 border-black group-hover:scale-110 transition-transform">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
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
      <div className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`} onClick={toggleSidebar}>
        <div className="menu-sidebar bg-black/60 backdrop-blur-3xl border-l border-white/10 shadow-2xl" onClick={e => e.stopPropagation()}>
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
