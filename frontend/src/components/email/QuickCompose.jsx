import React, { useState } from 'react';
import { X, Send, User, MessageSquare, Loader2, Mail } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';

const QuickCompose = ({ onClose, onSent }) => {
    const [to, setTo] = useState('');
    const [subject, setSubject] = useState('');
    const [body, setBody] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!to || !subject || !body) return;

        setLoading(true);
        try {
            await SYSTEM_API.sendEmail(to, subject, body);
            if (onSent) onSent();
            onClose();
        } catch (error) {
            console.error("Transmission failed", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
            <div className="w-full max-w-2xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-slide-in">
                <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                    <div className="flex items-center gap-3">
                        <Mail className="w-4 h-4 text-purple-400" />
                        <span className="text-xs font-mono text-gray-400 uppercase tracking-widest">New Transmission</span>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-white/5 rounded-full transition-colors group"
                    >
                        <X className="w-5 h-5 text-gray-500 group-hover:text-white" />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="space-y-1">
                        <label className="text-[10px] font-mono text-gray-500 uppercase tracking-widest ml-1">Recipient</label>
                        <input
                            autoFocus
                            type="email"
                            placeholder="pilot@nexus.com"
                            required
                            className="w-full bg-transparent border-b border-white/10 py-2 outline-none focus:border-purple-500 text-white transition-colors"
                            value={to}
                            onChange={e => setTo(e.target.value)}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[10px] font-mono text-gray-500 uppercase tracking-widest ml-1">Subject</label>
                        <input
                            type="text"
                            placeholder="Mission Directives"
                            required
                            className="w-full bg-transparent border-b border-white/10 py-2 outline-none focus:border-purple-500 text-white transition-colors"
                            value={subject}
                            onChange={e => setSubject(e.target.value)}
                        />
                    </div>
                    <div className="space-y-1 !mt-6">
                        <label className="text-[10px] font-mono text-gray-500 uppercase tracking-widest ml-1">Payload Context</label>
                        <textarea
                            rows={10}
                            placeholder="Initialize encrypted message payload..."
                            required
                            className="w-full bg-transparent border-none outline-none focus:ring-0 text-white resize-none font-mono text-sm leading-relaxed mt-2"
                            value={body}
                            onChange={e => setBody(e.target.value)}
                        />
                    </div>
                    <div className="pt-6 flex justify-end">
                        <button
                            disabled={loading}
                            type="submit"
                            className="px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl shadow-lg shadow-purple-900/40 flex items-center gap-3 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                            Execute Send
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default QuickCompose;
