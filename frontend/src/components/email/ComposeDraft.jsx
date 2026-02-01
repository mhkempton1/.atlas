import React, { useState } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles, X, Copy, Check, MessageSquare, Loader2, Mail, ArrowRight, User, FileText } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

const ComposeDraft = () => {
    // Input state
    const [formData, setFormData] = useState({
        sender: '',
        subject: '',
        body: '',
        instructions: ''
    });

    // Output/Preview state
    const [draftResult, setDraftResult] = useState(null);
    const [reviewData, setReviewData] = useState({
        to: '',
        subject: '',
        body: ''
    });

    // UI state
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [sendStatus, setSendStatus] = useState(null); // { success: boolean, message: string }
    const [copied, setCopied] = useState(false);

    // Animations
    const containerVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5, staggerChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, x: -20 },
        visible: { opacity: 1, x: 0 }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleReviewChange = (e) => {
        setReviewData({ ...reviewData, [e.target.name]: e.target.value });
    };

    // Helper to extract email from "Name <email@domain.com>" format
    const extractEmail = (text) => {
        const match = text.match(/<([^>]+)>/);
        return match ? match[1] : text;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsGenerating(true);
        setDraftResult(null);
        setSendStatus(null);

        try {
            const result = await SYSTEM_API.generateDraft(
                formData.sender,
                formData.subject,
                formData.body,
                formData.instructions
            );

            if (result && result.draft_text) {
                setDraftResult({
                    text: result.draft_text,
                    detected_context: result.detected_context
                });
                // Pre-fill review data
                setReviewData({
                    to: extractEmail(formData.sender),
                    subject: `Re: ${formData.subject}`,
                    body: result.draft_text
                });
            } else {
                setDraftResult("Error: No draft returned.");
            }
        } catch (error) {
            setDraftResult(`Error: ${error.message || "Failed to generate draft."}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSend = async () => {
        setIsSending(true);
        setSendStatus(null);
        try {
            const result = await SYSTEM_API.sendEmail(
                reviewData.to,
                reviewData.subject,
                reviewData.body
            );

            if (result.success) {
                setSendStatus({
                    success: true,
                    message: `Sent successfully! (Via: ${result.sent_from || 'Outlook'})`
                });
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            setSendStatus({
                success: false,
                message: error.message || "Failed to send email."
            });
        } finally {
            setIsSending(false);
        }
    };

    const handleCopy = () => {
        if (reviewData.body) {
            navigator.clipboard.writeText(reviewData.body);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <Motion.div
            className="w-full"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
        >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-140px)]">
                {/* Input Section */}
                <Motion.div className="glass-panel p-6 flex flex-col h-full overflow-y-auto" variants={itemVariants}>
                    <h3 className="text-lg font-semibold flex items-center gap-2 mb-6">
                        <Mail className="w-5 h-5 text-primary" />
                        Incoming Context
                    </h3>

                    <form onSubmit={handleSubmit} className="space-y-5 flex-1 flex flex-col">
                        <div>
                            <label className="label text-slate-300">From (Sender)</label>
                            <input
                                type="text"
                                name="sender"
                                placeholder="e.g. Client Name <client@example.com>"
                                className="input-field bg-slate-800/80 border-slate-600 focus:bg-slate-700 text-white placeholder-slate-500"
                                value={formData.sender}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div>
                            <label className="label text-slate-300">Original Subject</label>
                            <input
                                type="text"
                                name="subject"
                                placeholder="Re: Project Timeline"
                                className="input-field bg-slate-800/80 border-slate-600 focus:bg-slate-700 text-white placeholder-slate-500"
                                value={formData.subject}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="flex-1">
                            <label className="label text-slate-300">Email Body / Context</label>
                            <textarea
                                name="body"
                                placeholder="Paste the email you received or describe the situation..."
                                className="input-field resize-none h-[200px] bg-slate-800/80 border-slate-600 focus:bg-slate-700 text-white placeholder-slate-500"
                                value={formData.body}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div>
                            <label className="label text-slate-300">Instructions (Optional)</label>
                            <div className="relative">
                                <textarea
                                    name="instructions"
                                    rows={3}
                                    placeholder="e.g. Be polite, accept the meeting, but ask to move it to 2 PM."
                                    className="input-field resize-none border-indigo-500/50 bg-indigo-500/10 focus:bg-indigo-500/20 text-indigo-100 placeholder-indigo-300/50"
                                    value={formData.instructions}
                                    onChange={handleChange}
                                />
                                <Sparkles className="absolute right-3 top-3 w-4 h-4 text-primary opacity-50" />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="btn-primary w-full flex items-center justify-center gap-2"
                            disabled={isGenerating}
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Drafting Response...
                                </>
                            ) : (
                                <>
                                    <ArrowRight className="w-5 h-5" />
                                    Generate Draft
                                </>
                            )}
                        </button>
                    </form>
                </Motion.div>

                {/* Output/Review Section */}
                <Motion.div className="glass-panel p-6 flex flex-col h-full" variants={itemVariants}>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <MessageSquare className="w-5 h-5 text-secondary" />
                            Review & Send
                        </h3>
                        {draftResult && (
                            <button
                                onClick={handleCopy}
                                className="flex items-center gap-1 text-xs bg-slate-700/50 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition-colors border border-slate-600"
                            >
                                {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                                {copied ? 'Copied' : 'Copy Text'}
                            </button>
                        )}
                    </div>

                    <div className="flex-1 bg-slate-950/50 rounded-xl border border-slate-800 p-4 relative flex flex-col overflow-hidden">
                        {draftResult ? (
                            <div className="flex flex-col h-full space-y-4">
                                {/* Send Metadata Fields */}
                                <div className="grid grid-cols-1 gap-3 pb-4 border-b border-slate-800">
                                    <div className="flex items-center gap-3">
                                        <label className="w-16 text-xs font-mono text-slate-500 uppercase">To:</label>
                                        <input
                                            name="to"
                                            value={reviewData.to}
                                            onChange={handleReviewChange}
                                            className="flex-1 bg-transparent border-b border-slate-800 focus:border-indigo-500 outline-none text-sm font-mono text-white py-1"
                                        />
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <label className="w-16 text-xs font-mono text-slate-500 uppercase">Subject:</label>
                                        <input
                                            name="subject"
                                            value={reviewData.subject}
                                            onChange={handleReviewChange}
                                            className="flex-1 bg-transparent border-b border-slate-800 focus:border-indigo-500 outline-none text-sm font-mono text-white py-1"
                                        />
                                    </div>
                                </div>

                                {/* Body Editor */}
                                <textarea
                                    name="body"
                                    value={reviewData.body}
                                    onChange={handleReviewChange}
                                    className="flex-1 bg-transparent border-none focus:ring-0 resize-none font-mono text-sm leading-relaxed text-slate-300 outline-none"
                                />

                                {/* Action Bar */}
                                <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                                    <div className="text-xs text-slate-500 flex flex-col gap-1">
                                        {draftResult.detected_context?.project ? (
                                            <span className="flex items-center gap-1 text-indigo-400">
                                                <Sparkles className="w-3 h-3" />
                                                Project: {draftResult.detected_context.project.name}
                                            </span>
                                        ) : "No project detected"}

                                        {draftResult.detected_context?.company_role && (
                                            <span className="flex items-center gap-1 text-emerald-400">
                                                <User className="w-3 h-3" />
                                                Sender Identified: {draftResult.detected_context.company_role}
                                            </span>
                                        )}

                                        {draftResult.detected_context?.file_context && (
                                            <span className="flex items-center gap-1 text-sky-400">
                                                <FileText className="w-3 h-3" />
                                                Deep Context: File Loaded
                                            </span>
                                        )}
                                    </div>

                                    <button
                                        onClick={handleSend}
                                        disabled={isSending || sendStatus?.success}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all ${sendStatus?.success
                                            ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                                            : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                                            }`}
                                    >
                                        {isSending ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Sending...
                                            </>
                                        ) : sendStatus?.success ? (
                                            <>
                                                <Check className="w-4 h-4" />
                                                Sent!
                                            </>
                                        ) : (
                                            <>
                                                <Send className="w-4 h-4" />
                                                Send with Outlook
                                            </>
                                        )}
                                    </button>
                                </div>
                                {sendStatus && (
                                    <div className={`text-xs mt-2 text-center ${sendStatus.success ? 'text-green-500' : 'text-red-400'}`}>
                                        {sendStatus.message}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-slate-600 opacity-60">
                                <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                                    <Mail className="w-8 h-8" />
                                </div>
                                <p>Generated drafts will appear here...</p>
                            </div>
                        )}

                        {isGenerating && (
                            <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center rounded-xl z-10">
                                <div className="flex flex-col items-center gap-3">
                                    <div className="w-12 h-12 border-t-2 border-primary rounded-full animate-spin"></div>
                                    <p className="text-primary text-sm font-medium animate-pulse">Analyzing & Drafting...</p>
                                </div>
                            </div>
                        )}
                    </div>
                </Motion.div>
            </div>
        </Motion.div>
    );
};

export default ComposeDraft;
