import React, { useState, useEffect } from 'react';
import { ArrowLeft, Star, Reply, Forward, Trash2, Paperclip, Archive, MailOpen, Send, X, Loader2, Sparkles, CheckSquare, Tag, Brain, Wand2, ClipboardCheck } from 'lucide-react';
import { Menu } from '@headlessui/react';
import { SYSTEM_API } from '../../services/api';
import { useToast } from '../../hooks/useToast';
import { PageHeader, Section, Spinner, EmptyState, StatusBadge } from '../shared/UIComponents';

const EmailView = ({ email, onBack, onEmailAction }) => {
    const { toast, toastElement } = useToast();
    const [replyMode, setReplyMode] = useState(null); // null, 'reply', 'forward'
    const [replyBody, setReplyBody] = useState('');
    const [forwardTo, setForwardTo] = useState('');
    const [forwardNote, setForwardNote] = useState('');
    const [sending, setSending] = useState(false);
    const [extracting, setExtracting] = useState(false);
    const [drafting, setDrafting] = useState(false);

    const CATEGORIES = ['work', 'personal', 'urgent', 'todo', 'finance', 'archive', 'drafts'];

    useEffect(() => {
        if (email && !email.is_read) {
            SYSTEM_API.markEmailRead(email.email_id)
                .then(() => {
                    if (onEmailAction) onEmailAction('update', email.email_id, { is_read: true });
                })
                .catch(err => console.error("Failed to mark email as read:", err));
        }
    }, [email?.email_id, email?.is_read, onEmailAction]);

    if (!email) return <div className="h-full flex items-center justify-center text-text-muted">Select an email to read</div>;

    const handleDelete = async () => {
        try {
            await SYSTEM_API.deleteEmail(email.email_id);
            toast("Email moved to trash", "success");
            if (onEmailAction) onEmailAction('deleted', email.email_id);
        } catch (err) {
            toast(`Delete failed: ${err.message}`, "error");
        }
    };

    const handleArchive = async () => {
        try {
            await SYSTEM_API.archiveEmail(email.email_id);
            toast("Email archived", "success");
            if (onEmailAction) onEmailAction('archived', email.email_id);
        } catch (err) {
            toast(`Archive failed: ${err.message}`, "error");
        }
    };

    const handleMarkUnread = async () => {
        try {
            await SYSTEM_API.markUnread(email.email_id);
            toast("Marked as unread", "info");
            if (onEmailAction) onEmailAction('unread', email.email_id);
        } catch (err) {
            toast(`Failed: ${err.message}`, "error");
        }
    };

    const handleSendReply = async () => {
        if (!replyBody.trim()) return;
        setSending(true);
        try {
            await SYSTEM_API.replyToEmail(email.email_id, replyBody);
            toast("Reply sent", "success");
            setReplyMode(null);
            setReplyBody('');
        } catch (err) {
            toast(`Reply failed: ${err.message}`, "error");
        } finally {
            setSending(false);
        }
    };

    const handleSendForward = async () => {
        if (!forwardTo.trim()) return;
        setSending(true);
        try {
            await SYSTEM_API.forwardEmail(email.email_id, forwardTo, forwardNote);
            toast("Email forwarded", "success");
            setReplyMode(null);
            setForwardTo('');
            setForwardNote('');
        } catch (err) {
            toast(`Forward failed: ${err.message}`, "error");
        } finally {
            setSending(false);
        }
    };

    const handleExtractTasks = async () => {
        setExtracting(true);
        try {
            const result = await SYSTEM_API.extractTasksFromEmail(email.email_id);
            if (result.tasks_found > 0) {
                toast(`Extracted ${result.tasks_found} task${result.tasks_found > 1 ? 's' : ''} from this email`, "success");
            } else {
                toast("No actionable tasks found in this email", "info");
            }
        } catch (err) {
            toast(`Task extraction failed: ${err.message}`, "error");
        } finally {
            setExtracting(false);
        }
    };

    const handleAIDraft = async () => {
        setReplyMode('reply');
        setDrafting(true);
        try {
            const result = await SYSTEM_API.generateDraft(
                email.from_address,
                email.subject,
                email.body_text || '',
                'Reply professionally and helpfully'
            );
            if (result.draft_text) {
                setReplyBody(result.draft_text);
                toast("AI draft generated - review and send", "success");
            }
        } catch (err) {
            toast(`Draft generation failed: ${err.message}`, "error");
        } finally {
            setDrafting(false);
        }
    };

    const handleCategoryChange = async (newCat) => {
        try {
            await SYSTEM_API.updateEmailCategory(email.email_id, newCat);
            toast(`Category updated to ${newCat}`, "success");
            if (onEmailAction) onEmailAction('update', email.email_id, { category: newCat });
        } catch (err) {
            toast(`Update failed: ${err.message}`, "error");
        }
    };

    return (
        <div className="email-view h-full flex flex-col bg-white/5 border-l border-white/10 backdrop-blur-2xl">
            {/* Header */}
            <div className="header p-4 border-b border-border">
                <div className="flex justify-between items-center mb-4">
                    <button className="btn btn-ghost md:hidden" onClick={onBack}>
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex gap-2 items-center">
                        {/* Quick Category Selector */}
                        <div className="flex gap-1 mr-2">
                            {['work', 'personal', 'urgent'].map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => handleCategoryChange(cat)}
                                    className={`px-2 py-1 text-[9px] uppercase font-bold rounded border transition-all ${email.category === cat
                                        ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                                        : 'text-gray-500 border-transparent hover:border-white/10 hover:text-white'
                                        }`}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>

                        {/* Move to Folder Dropdown */}
                        <div className="relative group">
                            <button className="flex items-center gap-1.5 px-2 py-1 text-[9px] uppercase font-bold rounded border border-white/10 text-gray-400 hover:text-white hover:border-white/30 transition-all">
                                <Tag className="w-3 h-3" />
                                {email.category || 'FOLDER'}
                            </button>
                            <div className="absolute right-0 top-full mt-2 w-40 bg-slate-900 border border-white/10 rounded-lg shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                                {CATEGORIES.map(cat => (
                                    <button
                                        key={cat}
                                        onClick={() => handleCategoryChange(cat)}
                                        className="w-full text-left px-4 py-2 text-[10px] uppercase font-mono text-gray-400 hover:text-white hover:bg-white/5 first:rounded-t-lg last:rounded-b-lg"
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            className="btn btn-icon bg-purple-500/10 hover:bg-purple-500/20 text-purple-400"
                            onClick={handleExtractTasks}
                            disabled={extracting}
                            title="AI: Extract Tasks"
                        >
                            {extracting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                        </button>

                        <div className="h-4 w-px bg-white/10 mx-1"></div>

                        <button className="btn btn-icon" onClick={handleMarkUnread} title="Mark unread">
                            <MailOpen className="w-4 h-4" />
                        </button>
                        <button className="btn btn-icon" onClick={handleArchive} title="Archive">
                            <Archive className="w-4 h-4" />
                        </button>
                        <button className="btn btn-icon" onClick={handleDelete} title="Delete">
                            <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                    </div>
                </div>

                <h2 className="text-xl font-bold text-text-bright mb-2">{email.subject}</h2>

                <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                            {email.from_name?.[0] || email.from_address?.[0]}
                        </div>
                        <div>
                            <div className="text-text-bright font-medium">{email.from_name || email.from_address}</div>
                            <div className="text-xs text-text-muted">{email.from_address}</div>
                        </div>
                    </div>
                    <div className="text-xs text-text-muted">
                        {new Date(email.date_received).toLocaleString()}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="content flex-1 overflow-auto p-6 bg-transparent">
                <div className="prose prose-invert max-w-none">
                    {email.body_html ? (
                        <div dangerouslySetInnerHTML={{ __html: email.body_html }} />
                    ) : (
                        <div className="whitespace-pre-wrap font-sans text-text-bright">{email.body_text}</div>
                    )}
                </div>

                {email.attachments && email.attachments.length > 0 && (
                    <div className="attachments mt-8 border-t border-border pt-4">
                        <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                            <Paperclip className="w-4 h-4" /> Attachments
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {email.attachments.map(att => (
                                <div key={att.id} className="p-2 bg-surface-dark border border-border rounded flex items-center gap-2 text-sm">
                                    <span>{att.filename}</span>
                                    <span className="text-xs text-text-muted">({Math.round(att.size / 1024)}KB)</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Reply/Forward Compose Area */}
            {replyMode && (
                <div className="border-t border-border p-4 bg-white/5 space-y-3">
                    <div className="flex justify-between items-center">
                        <h4 className="text-sm font-semibold text-text-bright">
                            {replyMode === 'reply' ? 'Reply' : 'Forward'}
                        </h4>
                        <button onClick={() => setReplyMode(null)} className="text-text-muted hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {replyMode === 'forward' && (
                        <input
                            type="email"
                            placeholder="Forward to email address..."
                            value={forwardTo}
                            onChange={(e) => setForwardTo(e.target.value)}
                            className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
                        />
                    )}

                    {drafting && (
                        <div className="flex items-center gap-2 text-xs text-purple-400 p-2 bg-purple-500/10 rounded animate-pulse">
                            <Sparkles className="w-3.5 h-3.5" />
                            AI is writing a draft...
                        </div>
                    )}

                    <textarea
                        placeholder={replyMode === 'reply' ? 'Type your reply...' : 'Add a note (optional)...'}
                        value={replyMode === 'reply' ? replyBody : forwardNote}
                        onChange={(e) => replyMode === 'reply' ? setReplyBody(e.target.value) : setForwardNote(e.target.value)}
                        rows={4}
                        className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none"
                    />

                    <div className="flex justify-end">
                        <button
                            onClick={replyMode === 'reply' ? handleSendReply : handleSendForward}
                            disabled={sending || (replyMode === 'reply' && !replyBody.trim()) || (replyMode === 'forward' && !forwardTo.trim())}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            {sending ? 'Sending...' : 'Send'}
                        </button>
                    </div>
                </div>
            )}

            {/* Actions Footer */}
            {!replyMode && (
                <div className="footer p-4 border-t border-white/10 bg-white/5 flex gap-3">
                    <button className="btn btn-primary flex items-center gap-2" onClick={() => setReplyMode('reply')}>
                        <Reply className="w-4 h-4" /> Reply
                    </button>
                    <button
                        className="btn btn-secondary flex items-center gap-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400"
                        onClick={handleAIDraft}
                        disabled={drafting}
                    >
                        {drafting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        AI Draft
                    </button>
                    <button className="btn btn-secondary flex items-center gap-2" onClick={() => setReplyMode('forward')}>
                        <Forward className="w-4 h-4" /> Forward
                    </button>
                    <button
                        className="btn btn-secondary flex items-center gap-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400"
                        onClick={handleExtractTasks}
                        disabled={extracting}
                    >
                        {extracting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ClipboardCheck className="w-4 h-4" />}
                        Create Task
                    </button>
                </div>
            )}
            {toastElement}
        </div>
    );
};

export default EmailView;
