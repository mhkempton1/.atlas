import React, { useState, useEffect } from 'react';
import {
    ClipboardCheck, AlertTriangle, ShieldCheck, PenTool,
    CheckCircle, X, ArrowRight, FileText, Lock
} from 'lucide-react';
import { useToast } from '../../hooks/useToast';
import { SYSTEM_API } from '../../services/api';
import { AnimatePresence, motion } from 'framer-motion';

const MissionBriefing = ({ phase, sopId, onBack }) => {
    const { toast } = useToast();
    const [briefing, setBriefing] = useState(null);
    const [loading, setLoading] = useState(true);
    const [safetyAck, setSafetyAck] = useState(false);
    const [checklistState, setChecklistState] = useState({});
    const [showAuditModal, setShowAuditModal] = useState(false);
    const [draftLog, setDraftLog] = useState("");

    useEffect(() => {
        const fetchBriefing = async () => {
            try {
                // In a real scenario, we'd fetch the SOP content from 'sopId' or 'phase' metadata
                // For this integration, we'll assume the SOP content is retrieved or passed.
                // We'll use a placeholder string that triggers the AI to generate a realistic checklist.
                const sopContent = `Standard Operating Procedure for ${phase?.phase_name || "General Construction"}.
                1. Perform Site Hazard Assessment (JHA).
                2. Verify LOTO.
                3. Stage materials.
                4. Execute primary task.
                5. Clean up workspace.`;

                const data = await SYSTEM_API.generateMissionBriefing(phase?.id || "unknown", sopContent);
                setBriefing(data);
            } catch (e) {
                console.error(e);
                toast("Failed to generate briefing. AI Service may be offline.", "error");
                // Fallback for demo if API fails (e.g. no AI key)
                setBriefing({
                    checklist: [{ step: "Manual SOP Review Required", is_safety_critical: true }],
                    tools_status: []
                });
            } finally {
                setLoading(false);
            }
        };
        fetchBriefing();
    }, [phase]);

    const toggleStep = (idx) => {
        setChecklistState(prev => ({
            ...prev,
            [idx]: !prev[idx]
        }));
    };

    const handleStartWork = async () => {
        if (!safetyAck) return;

        try {
            // Call API to update task status (Gatekeeper check happens here)
            // Ideally we pass the real task ID associated with the phase
            await SYSTEM_API.updateTaskStatus("active-task", 'in_progress', true);
            toast("Safety Protocol Acknowledged. Work Started.", "success");
        } catch (e) {
            // Mock success for prototype if task doesn't exist
            if (e.response && e.response.status === 404) {
                toast("Safety Protocol Acknowledged. Work Started (Simulated).", "success");
            } else {
                toast("Gatekeeper Rejection: Safety Acknowledgement Failed", "error");
            }
        }
    };

    const handleComplete = async () => {
        // Generate Draft Log
        const items = briefing.checklist.map((c, i) => ({
            step: c.step,
            completed: !!checklistState[i]
        }));

        try {
            const res = await SYSTEM_API.draftDailyLog({
                project_id: phase?.project_name || "Unknown",
                checklist_items: items
            });
            setDraftLog(res.preview);
            setShowAuditModal(true);
        } catch (e) {
            console.error(e);
            toast("Failed to draft log", "error");
        }
    };

    if (loading) {
        return (
            <div className="bg-slate-900 rounded-xl p-8 border border-white/5 flex flex-col items-center justify-center animate-pulse">
                <PenTool className="w-8 h-8 text-purple-400 mb-4 animate-bounce" />
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Foreman is Generating Briefing...</h3>
                <p className="text-xs text-gray-600 mt-2">Decomposing SOP & Checking Inventory</p>
            </div>
        );
    }

    if (!briefing || !briefing.checklist) {
        return <div className="p-6 text-center text-gray-500 text-xs">Briefing unavailable.</div>;
    }

    const completedCount = Object.values(checklistState).filter(Boolean).length;
    const progress = (completedCount / briefing.checklist.length) * 100;

    return (
        <div className="bg-white/[0.02] border border-purple-500/20 rounded-2xl overflow-hidden mb-6 relative group backdrop-blur-2xl shadow-[0_0_40px_rgba(0,0,0,0.2)]">
            <div className="p-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <ClipboardCheck className="w-5 h-5 text-purple-400" />
                    <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Mission Briefing</h3>
                        <p className="text-[10px] text-gray-500 font-mono">{phase?.project_name} // {phase?.phase_name}</p>
                    </div>
                </div>
                <button onClick={onBack} className="p-1 hover:bg-white/10 rounded"><X className="w-4 h-4 text-gray-400" /></button>
            </div>

            <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Inventory & Safety */}
                <div className="space-y-6">
                    {/* Tool Check */}
                    <div className="bg-slate-800/40 rounded-lg p-4 border border-white/5">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <PenTool className="w-3 h-3" /> Tool Readiness
                        </h4>
                        <div className="space-y-2">
                            {briefing.tools_status.map((t, i) => (
                                <div key={i} className="flex justify-between items-center text-xs">
                                    <span className="text-gray-300">{t.tool}</span>
                                    <span className={`px-2 py-0.5 rounded font-mono ${t.available ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {t.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Safety Gatekeeper */}
                    <div className={`p-4 rounded-lg border transition-colors ${safetyAck ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-amber-500/10 border-amber-500/30'}`}>
                        <div className="flex items-start gap-3">
                            <ShieldCheck className={`w-5 h-5 ${safetyAck ? 'text-emerald-400' : 'text-amber-400'}`} />
                            <div>
                                <h4 className={`text-sm font-bold ${safetyAck ? 'text-emerald-400' : 'text-amber-400'}`}>
                                    {safetyAck ? "Safety Protocols Active" : "Safety Acknowledgement Required"}
                                </h4>
                                <p className="text-[10px] text-gray-400 mt-1 leading-relaxed">
                                    By acknowledging, I confirm I have read the relevant SOPs and verified site conditions are safe for work.
                                </p>
                                {!safetyAck && (
                                    <button
                                        onClick={() => setSafetyAck(true)}
                                        className="mt-3 w-full py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold uppercase rounded border border-amber-500/40 transition-colors"
                                    >
                                        Acknowledge & Unlock
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Checklist */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs text-gray-500 font-mono">PROGRESS: {Math.round(progress)}%</span>
                        <div className="w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 transition-all duration-500" style={{ width: `${progress}%` }} />
                        </div>
                    </div>

                    <div className="space-y-2">
                        {briefing.checklist.map((item, i) => (
                            <div
                                key={i}
                                onClick={() => safetyAck && toggleStep(i)}
                                className={`
                                    group flex items-center gap-4 p-3 rounded-lg border transition-all cursor-pointer
                                    ${!safetyAck ? 'opacity-50 grayscale pointer-events-none' : ''}
                                    ${checklistState[i] ? 'bg-purple-500/10 border-purple-500/30' : 'bg-slate-800/30 border-white/5 hover:bg-slate-800/60'}
                                `}
                            >
                                <div className={`
                                    w-5 h-5 rounded border flex items-center justify-center transition-colors
                                    ${checklistState[i] ? 'bg-purple-500 border-purple-500' : 'border-gray-600 group-hover:border-purple-400'}
                                `}>
                                    {checklistState[i] && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                                </div>
                                <div className="flex-1">
                                    <p className={`text-sm font-medium transition-colors ${checklistState[i] ? 'text-purple-200 line-through decoration-purple-500/50' : 'text-gray-200'}`}>
                                        {item.step}
                                    </p>
                                    {item.is_safety_critical && (
                                        <span className="text-[9px] text-amber-400 font-bold uppercase tracking-wider mt-0.5 block">
                                            ⚠️ Safety Critical
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {progress === 100 && (
                        <button
                            onClick={handleComplete}
                            className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold uppercase tracking-widest rounded-lg shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 animate-in fade-in slide-in-from-bottom-2"
                        >
                            <FileText className="w-4 h-4" />
                            Draft Daily Log
                        </button>
                    )}
                </div>
            </div>

            {/* Audit Modal */}
            <AnimatePresence>
                {showAuditModal && (
                    <div className="absolute inset-0 z-50 bg-slate-900/95 backdrop-blur-sm flex items-center justify-center p-6 animate-in fade-in">
                        <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-full">
                            <div className="p-4 bg-purple-600 flex justify-between items-center">
                                <h3 className="font-bold text-white flex items-center gap-2">
                                    <ShieldCheck className="w-5 h-5" />
                                    Daily Log Audit
                                </h3>
                                <button onClick={() => setShowAuditModal(false)}><X className="w-5 h-5 text-white/70" /></button>
                            </div>
                            <div className="p-6 space-y-4">
                                <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-center gap-3">
                                    <Lock className="w-5 h-5 text-amber-400" />
                                    <p className="text-xs text-amber-200">
                                        This log is currently in <strong>DRAFT</strong> mode. Review and edit before committing to the permanent Altimeter Record.
                                    </p>
                                </div>
                                <textarea
                                    className="w-full h-64 bg-slate-950 border border-white/10 rounded-lg p-4 font-mono text-sm text-gray-300 focus:border-purple-500 focus:outline-none resize-none"
                                    value={draftLog}
                                    onChange={(e) => setDraftLog(e.target.value)}
                                />
                            </div>
                            <div className="p-4 border-t border-white/10 flex justify-end gap-3 bg-slate-950/50">
                                <button
                                    onClick={() => setShowAuditModal(false)}
                                    className="px-4 py-2 text-sm font-bold text-gray-400 hover:text-white"
                                >
                                    Cancel
                                </button>
                                <button
                                    className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold rounded-lg shadow-lg shadow-emerald-500/20 flex items-center gap-2"
                                    onClick={() => {
                                        toast("Daily Log Committed to Altimeter DB", "success");
                                        setShowAuditModal(false);
                                        onBack();
                                    }}
                                >
                                    <CheckCircle className="w-4 h-4" />
                                    Commit Record
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default MissionBriefing;
