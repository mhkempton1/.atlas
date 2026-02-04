import React, { useState } from 'react';
import { X, Server, Activity, Calendar, Database, AlertTriangle, CheckCircle, Copy, ExternalLink } from 'lucide-react';
import { motion as _motion, AnimatePresence } from 'framer-motion';

const SystemDiagnosticsModal = ({ isOpen, onClose, healthData }) => {
    const [copiedCommand, setCopiedCommand] = useState(null);

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedCommand(id);
        setTimeout(() => setCopiedCommand(null), 2000);
    };

    const getIconComponent = (iconName) => {
        const icons = {
            server: Server,
            activity: Activity,
            calendar: Calendar,
            database: Database
        };
        return icons[iconName] || Server;
    };

    if (!isOpen || !healthData) return null;

    const subsystems = healthData.subsystems || [];
    const degradedSystems = subsystems.filter(s => !s.healthy);

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                <_motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="bg-slate-950/95 border border-white/10 rounded-3xl shadow-[0_0_100px_rgba(0,0,0,0.9)] w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="p-8 border-b border-white/10 bg-white/5">
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-3xl font-mono font-medium tracking-[0.2em] text-white uppercase">System Diagnostics</h2>
                                <p className="text-sm text-white/40 font-mono mt-2">
                                    Overall Health: <span className={`${healthData.health_percentage >= 90 ? 'text-cyan-400' : 'text-amber-400'} font-bold`}>{healthData.health_percentage}%</span>
                                </p>
                            </div>
                            <button onClick={onClose} className="p-3 hover:bg-white/10 rounded-xl transition-colors">
                                <X className="w-6 h-6 text-white/40 hover:text-white" />
                            </button>
                        </div>
                    </div>

                    {/* Subsystems Grid */}
                    <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {subsystems.map((system, idx) => {
                                const IconComponent = getIconComponent(system.icon);
                                return (
                                    <div
                                        key={idx}
                                        className={`p-6 rounded-2xl border ${system.healthy
                                                ? 'bg-cyan-500/5 border-cyan-500/20'
                                                : 'bg-amber-500/5 border-amber-500/30'
                                            } transition-all`}
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className={`p-3 rounded-xl ${system.healthy ? 'bg-cyan-500/10' : 'bg-amber-500/10'}`}>
                                                <IconComponent className={`w-6 h-6 ${system.healthy ? 'text-cyan-400' : 'text-amber-400'}`} />
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-lg font-medium text-white">{system.name}</h3>
                                                    {system.healthy ? (
                                                        <CheckCircle className="w-5 h-5 text-cyan-400" />
                                                    ) : (
                                                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                                                    )}
                                                </div>
                                                <p className={`text-xs font-mono uppercase tracking-wider mb-2 ${system.healthy ? 'text-cyan-400/80' : 'text-amber-400/80'
                                                    }`}>
                                                    {system.status}
                                                </p>
                                                {system.details && (
                                                    <p className="text-sm text-white/60 mb-3">{system.details}</p>
                                                )}
                                                {system.error && (
                                                    <p className="text-sm text-amber-300 mb-3">{system.error}</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Remediation Steps */}
                        {degradedSystems.length > 0 && (
                            <div className="mt-8 p-6 bg-amber-500/5 border border-amber-500/20 rounded-2xl">
                                <h3 className="text-xl font-mono font-medium text-amber-400 mb-6 flex items-center gap-3">
                                    <AlertTriangle className="w-6 h-6" />
                                    Remediation Required
                                </h3>
                                <div className="space-y-6">
                                    {degradedSystems.map((system, idx) => (
                                        system.remediation && (
                                            <div key={idx} className="p-5 bg-black/40 rounded-xl border border-white/5">
                                                <h4 className="text-lg font-medium text-white mb-3">{system.name}: {system.remediation.title}</h4>
                                                <ol className="space-y-2 mb-4">
                                                    {system.remediation.steps.map((step, stepIdx) => (
                                                        <li key={stepIdx} className="text-sm text-white/70 font-mono flex items-start gap-3">
                                                            <span className="text-cyan-400 font-bold">{stepIdx + 1}.</span>
                                                            <span>{step}</span>
                                                        </li>
                                                    ))}
                                                </ol>
                                                {system.remediation.command && (
                                                    <div className="flex items-center gap-3">
                                                        <code className="flex-1 px-4 py-3 bg-black/60 border border-white/10 rounded-lg text-sm text-cyan-400 font-mono">
                                                            {system.remediation.command}
                                                        </code>
                                                        <button
                                                            onClick={() => copyToClipboard(system.remediation.command, `cmd-${idx}`)}
                                                            className="px-4 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition-colors flex items-center gap-2"
                                                        >
                                                            <Copy className="w-4 h-4" />
                                                            {copiedCommand === `cmd-${idx}` ? 'Copied!' : 'Copy'}
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-white/10 bg-black/40 flex justify-between items-center">
                        <p className="text-xs text-white/30 font-mono">
                            Last Updated: {new Date(healthData.timestamp).toLocaleString()}
                        </p>
                        <button
                            onClick={onClose}
                            className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </_motion.div>
            </div>
        </AnimatePresence>
    );
};

export default SystemDiagnosticsModal;
