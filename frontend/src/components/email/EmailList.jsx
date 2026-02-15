import React, { useState, useEffect, useCallback } from 'react';
import { Mail, RefreshCw, Filter, Search, Paperclip, ChevronDown, ChevronUp, Archive, Reply, Forward, Trash, Star, Tag, CheckSquare, MailOpen } from 'lucide-react';
import api, { SYSTEM_API } from '../../services/api';
import { PageHeader, Spinner, EmptyState, Section, StatusBadge } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';

const getEmailItemStyle = (is_read, expanded) => {
    const base = "border-b border-white/5 transition-all";
    const bg = expanded ? 'bg-white/10' : 'hover:bg-white/5';
    const border = !is_read ? 'bg-purple-500/5 border-l-4 border-l-purple-500' : 'border-l-4 border-l-transparent';
    return `${base} ${bg} ${border}`;
};

const getCategoryBadgeStyle = (category) => {
    switch (category) {
        case 'urgent': return 'bg-red-500/10 text-red-400 border-red-500/20';
        case 'work': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        case 'personal': return 'bg-green-500/10 text-green-400 border-green-500/20';
        default: return 'bg-white/10 text-white/70 border-white/5';
    }
};

const EmailItem = ({ email, onClick, expanded, onAction }) => {
    return (
        <div
            className={`${getEmailItemStyle(email.is_read, expanded)} group relative`}
        >
            <div
                className="p-4 cursor-pointer flex items-start gap-4"
                onClick={onClick}
            >
                <div className={`mt-1 w-2 h-2 rounded-full ${!email.is_read ? 'bg-purple-500' : 'bg-transparent'}`} />

                <div className="flex-1 min-w-0 transition-all group-hover:pr-20">
                    <div className="flex justify-between items-start mb-1">
                        <span className={`text-sm font-medium ${!email.is_read ? 'text-white' : 'text-gray-400'}`}>
                            {email.from_name || email.from_address}
                        </span>
                        <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                            {new Date(email.date_received).toLocaleDateString()}
                        </span>
                    </div>

                    <h4 className={`text-sm mb-1 truncate ${!email.is_read ? 'text-gray-200 font-medium' : 'text-gray-500'}`}>
                        {email.category && (
                            <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold uppercase mr-2 border ${getCategoryBadgeStyle(email.category)}`}>
                                {email.category}
                            </span>
                        )}
                        {email.subject}
                    </h4>

                    {!expanded && (
                        <p className="text-xs text-gray-500 truncate">
                            {email.snippet || email.body_text?.substring(0, 100)}
                        </p>
                    )}
                </div>

                {email.has_attachments && <Paperclip className="w-4 h-4 text-gray-500" />}
            </div>

            {/* Quick Hover Actions */}
            {!expanded && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                    <button
                        onClick={(e) => onAction(e, 'archive', email)}
                        className="p-2 rounded-lg bg-slate-900/80 border border-white/5 text-gray-400 hover:text-white hover:border-white/20 shadow-xl backdrop-blur-md"
                        title="Archive"
                    >
                        <Archive className="w-4 h-4" />
                    </button>
                    <button
                        onClick={(e) => onAction(e, 'delete', email)}
                        className="p-2 rounded-lg bg-red-950/20 border border-red-500/10 text-gray-500 hover:text-red-400 hover:border-red-500/30 shadow-xl backdrop-blur-md"
                        title="Delete"
                    >
                        <Trash className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* EXPANDED VIEW */}
            {expanded && (
                <div className="px-10 pb-4 animate-slide-in">
                    <div className="bg-white/5 rounded-lg p-4 border border-white/5 text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                        {email.body_text || "No content"}
                    </div>

                    <div className="flex items-center gap-2 mt-4 pt-3 border-t border-white/5">
                        <button
                            onClick={(e) => onAction(e, 'reply', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 text-xs font-medium"
                        >
                            <Reply className="w-3.5 h-3.5" /> Reply
                        </button>
                        <button
                            onClick={(e) => onAction(e, 'forward', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white text-xs font-medium"
                        >
                            <Forward className="w-3.5 h-3.5" /> Forward
                        </button>
                        <button
                            onClick={(e) => onAction(e, 'task', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 text-xs font-medium"
                            title="Create Task from Email"
                        >
                            <CheckSquare className="w-3.5 h-3.5" /> Create Task
                        </button>
                        <div className="flex-1" />
                        <button
                            onClick={(e) => onAction(e, 'unread', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-white/5 text-gray-400 hover:text-white text-xs"
                            title="Mark as Unread"
                        >
                            <MailOpen className="w-3.5 h-3.5" /> Unread
                        </button>
                        <button
                            onClick={(e) => onAction(e, 'archive', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-white/5 text-gray-500 hover:text-white text-xs"
                        >
                            <Archive className="w-3.5 h-3.5" /> Archive
                        </button>
                        <button
                            onClick={(e) => onAction(e, 'delete', email)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-red-500/10 text-gray-500 hover:text-red-400 text-xs"
                        >
                            <Trash className="w-3.5 h-3.5" /> Delete
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

const EmailList = ({ onSelectEmail }) => {
    const { toast, toastElement } = useToast();
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [expandedId, setExpandedId] = useState(null);
    const [activeCategory, setActiveCategory] = useState('All');
    const [totalUnread, setTotalUnread] = useState(0);

    const CATEGORIES = ['All', 'UNREAD', 'work', 'personal', 'urgent', 'todo'];

    const loadEmails = useCallback(async () => {
        try {
            setLoading(true);
            const params = { limit: 50 };
            if (activeCategory === 'UNREAD') {
                params.is_read = false;
            } else if (activeCategory && activeCategory !== 'All') {
                params.category = activeCategory;
            }
            const res = await api.get('/email/list', { params });
            setEmails(res.data);

            // Also update total unread from stats
            const stats = await SYSTEM_API.getDashboardStats();
            setTotalUnread(stats.inbox_unread || 0);
        } catch (err) {
            console.error(err);
            toast("Failed to load emails", "error");
        } finally {
            setLoading(false);
        }
    }, [toast, activeCategory]);

    useEffect(() => {
        loadEmails();
    }, [loadEmails, activeCategory]);

    const handleScan = async () => {
        try {
            setIsScanning(true);
            const res = await api.post('/email/scan?limit=10');
            toast("Intelligence Bridge active: Background scan started.", "info");

            // We don't wait for completion here as per 202 Accepted logic
            // But we keep the indicator for a moment to feel "Active"
            setTimeout(() => {
                setIsScanning(false);
                loadEmails();
            }, 3000);

        } catch (err) {
            console.error("Scan failed", err);
            toast("Fail: Intelligence Bridge connection error.", "error");
            setIsScanning(false);
        }
    };

    const handleSync = async () => {
        try {
            setSyncing(true);
            const res = await api.post('/email/sync');

            if (res.data.status === 'error') {
                throw new Error(res.data.message);
            }

            toast(`Synced ${res.data.synced || 0} emails`, "success");
            setTimeout(() => {
                loadEmails();
                setSyncing(false);
            }, 1000);

        } catch (err) {
            console.error("Sync failed", err);
            let msg = "Sync failed. Check backend logs.";
            if (err.message && !err.message.includes('backend')) msg = err.message;
            toast(msg, "error");
            setSyncing(false);
        }
    };

    const handleAction = async (e, action, email) => {
        e.stopPropagation();

        try {
            switch (action) {
                case 'archive':
                    await SYSTEM_API.archiveEmail(email.email_id);
                    toast("Email archived", "success");
                    setEmails(prev => prev.filter(e => e.email_id !== email.email_id));
                    break;
                case 'delete':
                    await SYSTEM_API.deleteEmail(email.email_id);
                    toast("Email deleted", "success");
                    setEmails(prev => prev.filter(e => e.email_id !== email.email_id));
                    break;
                case 'unread':
                    await SYSTEM_API.markUnread(email.email_id);
                    toast("Marked as unread", "info");
                    setEmails(prev => prev.map(e => e.email_id === email.email_id ? { ...e, is_read: false } : e));
                    setTotalUnread(prev => prev + 1);
                    break;
                case 'task':
                    await SYSTEM_API.extractTasksFromEmail(email.email_id);
                    toast("Tasks extracted to your list", "success");
                    break;
                case 'reply':
                    // Navigate to email view which has the reply compose
                    if (onSelectEmail) onSelectEmail(email);
                    break;
                case 'forward':
                    // Navigate to email view which has the forward compose
                    if (onSelectEmail) onSelectEmail(email);
                    break;
                default:
                    toast(`${action} not implemented`, "warning");
            }
        } catch (err) {
            toast(`${action} failed: ${err.response?.data?.detail || err.message}`, "error");
        }
    };

    const toggleExpand = (id) => {
        setExpandedId(prev => prev === id ? null : id);
    };

    if (loading && emails.length === 0) return <Spinner label="Loading Inbox..." />;

    return (
        <div className="h-full flex flex-col bg-white/5 rounded-xl overflow-hidden border border-white/5 backdrop-blur-xl shadow-2xl">
            <div className="p-4 border-b border-white/5 bg-white/5">
                <PageHeader
                    icon={Mail}
                    title="Inbox"
                    subtitle={`${totalUnread} Total Unread Emails`}
                >
                    <div className="flex gap-2">
                        <button
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium border border-white/10 ${syncing ? 'bg-slate-800 text-gray-400' : 'bg-slate-800 hover:bg-slate-700 text-white'}`}
                            onClick={handleSync}
                            disabled={syncing || isScanning}
                        >
                            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                            {syncing ? 'Syncing...' : 'Sync'}
                        </button>
                        <button
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium border border-emerald-500/30 ${isScanning ? 'bg-emerald-900/20 text-emerald-400' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}`}
                            onClick={handleScan}
                            disabled={syncing || isScanning}
                        >
                            <span className={`w-3.5 h-3.5 flex items-center justify-center ${isScanning ? 'animate-pulse' : ''}`}>
                                {isScanning ? '🔥' : '🧿'}
                            </span>
                            {isScanning ? 'The Lens: Scanning...' : 'The Lens: Scan'}
                        </button>
                    </div>
                </PageHeader>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex overflow-x-auto border-b border-white/5 bg-white/[0.01] no-scrollbar">
                {CATEGORIES.map(cat => (
                    <button
                        key={cat}
                        onClick={() => setActiveCategory(cat)}
                        className={`px-4 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${activeCategory === cat
                            ? 'border-purple-500 text-purple-400 bg-purple-500/5'
                            : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {cat.toUpperCase()}
                    </button>
                ))}
            </div>

            <div className="flex-1 overflow-y-auto">
                {emails.length === 0 ? (
                    <EmptyState
                        icon={Mail}
                        title="Inbox Empty"
                        message="No emails found. Try syncing to fetch from Gmail."
                        action={
                            <button className="mt-4 text-purple-400 hover:text-purple-300 text-sm font-medium" onClick={handleSync}>
                                Sync Now
                            </button>
                        }
                    />
                ) : (
                    <div className="divide-y divide-white/5">
                        {/* Grouping could be added here (Today, Yesterday) */}
                        {emails.map(email => (
                            <EmailItem
                                key={email.email_id}
                                email={email}
                                expanded={expandedId === email.email_id}
                                onClick={() => {
                                    toggleExpand(email.email_id);
                                    if (onSelectEmail) onSelectEmail(email);
                                }}
                                onAction={handleAction}
                            />
                        ))}
                    </div>
                )}
            </div>
            {toastElement}
        </div>
    );
};

export default EmailList;
