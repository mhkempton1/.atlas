import React, { useState, useEffect } from 'react';
import { ArrowLeft, Star, Reply, Forward, Trash2, Paperclip, Archive, MailOpen, Send, X, Loader2, Sparkles, CheckSquare, Tag, Brain, Wand2, ClipboardCheck, User, Building, Phone, Briefcase, Calendar, ExternalLink } from 'lucide-react';
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

    // Contact Info State
    const [contact, setContact] = useState(null);
    const [loadingContact, setLoadingContact] = useState(false);

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

    // Fetch Contact Info
    useEffect(() => {
        if (email?.from_address) {
            setLoadingContact(true);
            SYSTEM_API.searchContacts(email.from_address)
                .then(data => setContact(data))
                .catch(err => {
                    console.error("Failed to fetch contact:", err);
                    setContact(null);
                })
                .finally(() => setLoadingContact(false));
        } else {
            setContact(null);
        }
    }, [email?.from_address]);

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
        <div className="email-view h-full flex flex-row bg-white/5 border-l border-white/10 backdrop-blur-2xl">
            {/* Main Email Content */}
            <div className="flex-1 flex flex-col min-w-0">
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
            </div>

            {/* Contact Sidebar */}
            <div className="w-80 border-l border-white/10 bg-black/20 p-4 flex flex-col gap-4 overflow-y-auto hidden md:flex">
                <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-2">Sender Profile</h3>

                {loadingContact ? (
                    <div className="flex items-center justify-center py-8 text-text-muted">
                        <Loader2 className="w-5 h-5 animate-spin mr-2" />
                        <span className="text-xs">Scanning contacts...</span>
                    </div>
                ) : contact ? (
                    <div className="space-y-4">
                        {/* Profile Card */}
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl shadow-lg backdrop-blur-sm">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500/30 to-blue-500/30 flex items-center justify-center text-lg font-bold text-white border border-white/10">
                                    {contact.name?.[0] || contact.email_address[0]}
                                </div>
                                <div>
                                    <div className="font-bold text-text-bright line-clamp-1">{contact.name || "Unknown Name"}</div>
                                    <div className="text-xs text-text-muted line-clamp-1">{contact.title || "No Title"}</div>
                                </div>
                            </div>

                            <div className="space-y-2 mt-4">
                                <div className="flex items-center gap-2 text-xs text-text-bright">
                                    <Building className="w-3.5 h-3.5 text-text-muted" />
                                    <span>{contact.company || "No Company"}</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-text-bright">
                                    <User className="w-3.5 h-3.5 text-text-muted" />
                                    <span className="truncate" title={contact.email_address}>{contact.email_address}</span>
                                </div>
                                {contact.phone && (
                                    <div className="flex items-center gap-2 text-xs text-text-bright">
                                        <Phone className="w-3.5 h-3.5 text-text-muted" />
                                        <span>{contact.phone}</span>
                                    </div>
                                )}
                            </div>

                            {contact.relationship_type && (
                                <div className="mt-4">
                                    <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold tracking-wide border ${
                                        contact.relationship_type === 'customer' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                        contact.relationship_type === 'vendor' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                                        'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                    }`}>
                                        {contact.relationship_type}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Stats Card */}
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                            <h4 className="text-xs font-semibold text-text-muted uppercase mb-3">Interaction Stats</h4>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="p-2 bg-black/20 rounded border border-white/5 text-center">
                                    <div className="text-lg font-mono font-bold text-white">{contact.email_count || 0}</div>
                                    <div className="text-[10px] text-text-muted uppercase">Emails</div>
                                </div>
                                <div className="p-2 bg-black/20 rounded border border-white/5 text-center">
                                    <div className="text-lg font-mono font-bold text-white">
                                        {contact.last_contact_date ? new Date(contact.last_contact_date).toLocaleDateString(undefined, {month: 'numeric', day: 'numeric'}) : '-'}
                                    </div>
                                    <div className="text-[10px] text-text-muted uppercase">Last Contact</div>
                                </div>
                            </div>
                        </div>

                        {/* Altimeter Links */}
                        {(contact.altimeter_customer_id || contact.altimeter_vendor_id) && (
                            <div className="p-4 bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-white/10 rounded-xl">
                                <h4 className="text-xs font-semibold text-blue-300 uppercase mb-2 flex items-center gap-1">
                                    <Briefcase className="w-3 h-3" /> Altimeter Linked
                                </h4>
                                <div className="space-y-1">
                                    {contact.altimeter_customer_id && (
                                        <a href={`/altimeter/customer/${contact.altimeter_customer_id}`} className="flex items-center justify-between text-xs text-white hover:text-blue-300 transition-colors p-1.5 hover:bg-white/5 rounded">
                                            <span>Customer Profile</span>
                                            <ExternalLink className="w-3 h-3 opacity-50" />
                                        </a>
                                    )}
                                    {contact.altimeter_vendor_id && (
                                        <a href={`/altimeter/vendor/${contact.altimeter_vendor_id}`} className="flex items-center justify-between text-xs text-white hover:text-blue-300 transition-colors p-1.5 hover:bg-white/5 rounded">
                                            <span>Vendor Profile</span>
                                            <ExternalLink className="w-3 h-3 opacity-50" />
                                        </a>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Tags */}
                        {contact.tags && contact.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                                {contact.tags.map(tag => (
                                    <span key={tag} className="px-2 py-0.5 text-[10px] bg-white/5 text-text-muted border border-white/10 rounded-full">
                                        #{tag}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="p-6 text-center border-2 border-dashed border-white/10 rounded-xl">
                        <div className="w-10 h-10 mx-auto bg-white/5 rounded-full flex items-center justify-center text-text-muted mb-3">
                            <User className="w-5 h-5" />
                        </div>
                        <h4 className="text-sm font-semibold text-text-bright mb-1">Unknown Contact</h4>
                        <p className="text-xs text-text-muted mb-4">No profile found for this sender.</p>
                        <button className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs rounded transition-colors w-full">
                            Create Contact
                        </button>
                    </div>
                )}
            </div>

            {toastElement}
        </div>
    );
};

export default EmailView;
