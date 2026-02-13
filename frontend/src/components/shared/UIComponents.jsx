import React, { useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Info, Loader2 } from 'lucide-react';

// ── Toast Notification ──────────────────────────────────────────
// Usage: <Toast message="Saved!" type="success" onClose={() => {}} />
export const Toast = ({ message, type = 'info', onClose, duration = 4000 }) => {
    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(onClose, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose]);

    const styles = {
        success: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
        error: 'bg-red-500/15 border-red-500/30 text-red-400',
        info: 'bg-blue-500/15 border-blue-500/30 text-blue-400',
        warning: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
    };
    const icons = {
        success: <CheckCircle className="w-4 h-4" />,
        error: <AlertCircle className="w-4 h-4" />,
        info: <Info className="w-4 h-4" />,
        warning: <AlertCircle className="w-4 h-4" />,
    };

    return (
        <div className={`fixed top-6 right-6 z-[2000] flex items-center gap-3 px-4 py-3 rounded-lg border ${styles[type]} shadow-lg animate-slide-in backdrop-blur-sm`}>
            {icons[type]}
            <span className="text-sm font-medium">{message}</span>
            <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100">
                <X className="w-3.5 h-3.5" />
            </button>
        </div>
    );
};


// ── Page Header ─────────────────────────────────────────────────
// Usage: <PageHeader icon={Mail} title="Inbox" subtitle="3 unread" />
export const PageHeader = ({ icon: Icon, title, subtitle, children, actions }) => (
    <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
            {Icon && (
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Icon className="w-5 h-5 text-purple-400" />
                </div>
            )}
            <div>
                <h2 className="text-xl font-bold text-white">{title}</h2>
                {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
            </div>
        </div>
        {(children || actions) && <div className="flex items-center gap-2">{children || actions}</div>}
    </div>
);

// ── Section Divider ─────────────────────────────────────────────
// Usage: <Section title="Active Tasks" count={5}>...children...</Section>
export const Section = ({ title, count, children, className = '' }) => (
    <div className={`mb-6 ${className}`}>
        <div className="flex items-center gap-2 mb-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</h3>
            {count !== undefined && (
                <span className="text-[10px] bg-white/10 text-gray-400 px-2 py-0.5 rounded-full">{count}</span>
            )}
            <div className="flex-1 h-px bg-white/5 ml-2" />
        </div>
        {children}
    </div>
);

// ── Empty State ─────────────────────────────────────────────────
// Usage: <EmptyState icon={Inbox} title="No emails" message="Check back later" />
export const EmptyState = ({ icon: Icon, title, message, description, action }) => (
    <div className="flex flex-col items-center justify-center text-center py-16 px-8 rounded-xl bg-white/5 border border-white/5">
        {Icon && (
            <div className="p-4 bg-primary/10 rounded-full mb-4 text-purple-400">
                <Icon className="w-8 h-8" />
            </div>
        )}
        <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm max-w-xs mb-6">{message || description}</p>
        {action && (
            typeof action === 'object' && action.onClick ? (
                <button
                    onClick={action.onClick}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-bold rounded-lg transition-all shadow-lg shadow-purple-500/20"
                >
                    {action.label}
                </button>
            ) : action
        )}
    </div>
);

// ── Loading Spinner ─────────────────────────────────────────────
// Usage: <Spinner label="Loading emails..." />
export const Spinner = ({ label }) => (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
        {label && <p className="text-sm text-gray-400">{label}</p>}
    </div>
);

// ── Status Badge ────────────────────────────────────────────────
// Usage: <StatusBadge status="active" /> or <StatusBadge status="completed" />
export const StatusBadge = ({ status, className = '' }) => {
    const lowerStatus = status?.toLowerCase() || 'default';
    const styles = {
        active: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        completed: 'bg-slate-500/15 text-slate-400 border-slate-500/30 line-through',
        pending: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        error: 'bg-red-500/15 text-red-400 border-red-500/30',
        draft: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
        high: 'bg-red-500/15 text-red-400 border-red-500/30',
        medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        low: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    };

    // Fallbackstyle if direct match not found
    const style = styles[lowerStatus] || styles.active;

    return (
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${style} ${className}`}>
            {status}
        </span>
    );
};
