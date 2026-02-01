import React, { useState } from 'react';
import SystemHealth from './SystemHealth';
import { SYSTEM_API } from '../services/api';

const EmailScanner = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const scanEmails = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await SYSTEM_API.scanEmails(10);
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-slate-800 rounded-lg shadow-lg border border-slate-700">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-6">
                    <div>
                        <h2 className="text-xl font-bold text-white">📧 Email Intelligence Scanner</h2>
                        <p className="text-sm text-slate-400">Scan recent unread emails for Altimeter tasks & events</p>
                    </div>
                    <SystemHealth />
                </div>
                <button
                    onClick={scanEmails}
                    disabled={loading}
                    className={`px-4 py-2 rounded font-medium transition-colors ${loading
                        ? 'bg-slate-600 cursor-not-allowed text-slate-300'
                        : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
                        }`}
                >
                    {loading ? 'Consulting Agents...' : 'Start Intelligence Scan'}
                </button>
            </div>

            {error && (
                <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded mb-4">
                    ❌ Error: {error}
                </div>
            )}

            {result && (
                <div className="space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                        <div className="bg-slate-700/50 p-4 rounded border border-slate-600 text-center">
                            <div className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">Emails Scanned</div>
                            <div className="text-2xl font-mono text-white font-bold">{result.emails_found}</div>
                        </div>
                        <div className="bg-slate-700/50 p-4 rounded border border-slate-600 text-center">
                            <div className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">Tasks Extracted</div>
                            <div className="text-2xl font-mono text-emerald-400 font-bold">{result.tasks_created.length}</div>
                        </div>
                        <div className="bg-slate-700/50 p-4 rounded border border-slate-600 text-center">
                            <div className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">Events Detected</div>
                            <div className="text-2xl font-mono text-purple-400 font-bold">{result.events_created.length}</div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {/* Task Results */}
                        {result.tasks_created.length > 0 && (
                            <div className="space-y-2">
                                <h3 className="text-xs font-bold text-emerald-500 uppercase tracking-widest px-1">Intelligent Tasks</h3>
                                {result.tasks_created.map((task, i) => (
                                    <div key={i} className="bg-slate-900/60 p-4 rounded-xl border border-emerald-500/20 shadow-sm flex justify-between items-center group hover:bg-slate-900/80 transition-all">
                                        <div>
                                            <h4 className="font-bold text-white text-sm">{task.title}</h4>
                                            <div className="text-[10px] text-slate-500 font-mono mt-1">CONTEXT PRECURSOR: {task.context_precursor || "DIRECT EMAIL"}</div>
                                        </div>
                                        <div className="flex gap-2">
                                            {task.type === 'proposal' && (
                                                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded border bg-yellow-500/10 text-yellow-400 border-yellow-500/20">
                                                    PROPOSAL
                                                </span>
                                            )}
                                            <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${task.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                                                }`}>
                                                {task.priority}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Event Results */}
                        {result.events_created.length > 0 && (
                            <div className="space-y-2">
                                <h3 className="text-xs font-bold text-purple-500 uppercase tracking-widest px-1">Calendar Intelligence</h3>
                                {result.events_created.map((event, i) => (
                                    <div key={i} className="bg-slate-900/60 p-4 rounded-xl border border-purple-500/20 shadow-sm flex justify-between items-center group hover:bg-slate-900/80 transition-all">
                                        <div>
                                            <h4 className="font-bold text-white text-sm">{event.title}</h4>
                                            <div className="text-[10px] text-slate-500 font-mono mt-1">START: {event.start_time ? new Date(event.start_time).toLocaleString() : "TBD"}</div>
                                        </div>
                                        <div className="bg-purple-500/20 p-1.5 rounded-lg">
                                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {result.tasks_created.length === 0 && result.events_created.length === 0 && (
                            <div className="text-center py-10 bg-slate-900/30 rounded-xl border border-dashed border-slate-700">
                                <p className="text-slate-500 italic text-sm">Agents scanned the payload but found no actionable intelligence.</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmailScanner;
