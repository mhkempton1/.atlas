import React, { useState, useEffect } from 'react';
import { ArrowLeft, Building, DollarSign, Activity, FileText, CheckSquare, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { Spinner, StatusBadge, Section } from '../shared/UIComponents';

const AltimeterProjectDashboard = ({ projectId, onBack }) => {
    const [projectData, setProjectData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const data = await SYSTEM_API.getProjectContext(projectId);
                setProjectData(data);
            } catch (err) {
                console.error("Failed to load project context", err);
                setError("Failed to load project details.");
            } finally {
                setLoading(false);
            }
        };

        if (projectId) fetchData();
    }, [projectId]);

    if (loading) return <div className="h-full flex items-center justify-center"><Spinner label="Loading Project Context..." /></div>;
    if (error) return (
        <div className="h-full flex flex-col items-center justify-center text-red-400 space-y-4">
            <AlertTriangle className="w-12 h-12" />
            <p>{error}</p>
            <button onClick={onBack} className="text-sm underline hover:text-red-300">Return to List</button>
        </div>
    );

    const { project, phases, financials, stats, recent_activity } = projectData;

    // Phases for Visualization
    const allPhases = ['Inquiry', 'Estimating', 'Proposal', 'Engineering', 'Procurement', 'Production', 'QC', 'Closeout'];
    const currentPhaseIndex = allPhases.indexOf(project.status) !== -1 ? allPhases.indexOf(project.status) : 0;

    return (
        <div className="h-full flex flex-col space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                            {project.name}
                            <StatusBadge status={project.status} />
                        </h2>
                        <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                            <span className="font-mono bg-white/5 px-2 py-0.5 rounded">ID: {project.altimeter_project_id || project.id}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                                <Building className="w-3 h-3" />
                                {project.address || "No Address"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Procore Status */}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${project.procore_id
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-slate-700/30 border-slate-600 text-slate-400'
                    }`}>
                    <div className={`w-2 h-2 rounded-full ${project.procore_id ? 'bg-emerald-500' : 'bg-slate-500'}`} />
                    {project.procore_id ? 'Procore Linked' : 'Procore Offline'}
                </div>
            </div>

            {/* Lifecycle Progress */}
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-6 relative overflow-hidden backdrop-blur-sm">
                <div className="absolute top-1/2 left-6 right-6 h-0.5 bg-slate-700/50 -translate-y-1/2 z-0" />
                <div className="relative z-10 flex justify-between">
                    {allPhases.map((phase, idx) => {
                        const isCompleted = idx < currentPhaseIndex;
                        const isCurrent = idx === currentPhaseIndex;
                        return (
                            <div key={phase} className="flex flex-col items-center gap-2">
                                <div className={`w-3 h-3 rounded-full border-2 transition-all duration-500 ${isCurrent ? 'bg-purple-500 border-purple-400 scale-125 shadow-[0_0_10px_rgba(168,85,247,0.5)]' :
                                        isCompleted ? 'bg-emerald-500 border-emerald-500' :
                                            'bg-slate-800 border-slate-600'
                                    }`} />
                                <span className={`text-[10px] font-medium tracking-wide uppercase ${isCurrent ? 'text-purple-400' :
                                        isCompleted ? 'text-emerald-500/70' :
                                            'text-slate-600'
                                    }`}>
                                    {phase}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-4 gap-4">
                {/* Financials */}
                <div className="bg-white/[0.03] border border-white/5 p-4 rounded-xl hover:bg-white/[0.05] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                        <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                            <DollarSign className="w-4 h-4" />
                        </div>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Financials</span>
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                        ${(financials?.contract_value || 0).toLocaleString()}
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400">
                        <span>Billed: ${(financials?.billed || 0).toLocaleString()}</span>
                    </div>
                </div>

                {/* Efficiency */}
                <div className="bg-white/[0.03] border border-white/5 p-4 rounded-xl hover:bg-white/[0.05] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                            <Activity className="w-4 h-4" />
                        </div>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Efficiency</span>
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                        {stats?.efficiency || 1.0}
                    </div>
                    <div className={`text-[10px] ${stats?.margin >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {stats?.margin >= 0 ? '+' : ''}{stats?.margin}% Margin Proj.
                    </div>
                </div>

                {/* Docs */}
                <div className="bg-white/[0.03] border border-white/5 p-4 rounded-xl hover:bg-white/[0.05] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                        <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
                            <FileText className="w-4 h-4" />
                        </div>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Documents</span>
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                        Active
                    </div>
                    <div className="text-[10px] text-slate-400">
                        View Document Central
                    </div>
                </div>

                {/* Schedule */}
                <div className="bg-white/[0.03] border border-white/5 p-4 rounded-xl hover:bg-white/[0.05] transition-colors">
                    <div className="flex justify-between items-start mb-2">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                            <Clock className="w-4 h-4" />
                        </div>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Schedule</span>
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                        On Time
                    </div>
                    <div className="text-[10px] text-slate-400">
                        Comp: {project.completion_date || 'TBD'}
                    </div>
                </div>
            </div>

            {/* Info & Activity */}
            <div className="grid grid-cols-3 gap-6 flex-1 min-h-0">
                <div className="col-span-2 space-y-6">
                    <Section title="Project Details">
                        <div className="grid grid-cols-2 gap-4 bg-white/[0.02] p-4 rounded-lg border border-white/5">
                            <div>
                                <label className="text-[10px] text-slate-500 uppercase">Project Manager</label>
                                <p className="text-sm text-slate-200">Mark Kempton (PM)</p>
                            </div>
                            <div>
                                <label className="text-[10px] text-slate-500 uppercase">Customer</label>
                                <p className="text-sm text-slate-200">{project.customer || 'Unknown'}</p>
                            </div>
                            <div>
                                <label className="text-[10px] text-slate-500 uppercase">Start Date</label>
                                <p className="text-sm text-slate-200">{project.start_date || 'TBD'}</p>
                            </div>
                            <div>
                                <label className="text-[10px] text-slate-500 uppercase">Est. Completion</label>
                                <p className="text-sm text-slate-200">{project.completion_date || 'TBD'}</p>
                            </div>
                        </div>
                    </Section>

                    <Section title="Recent Activity">
                        <div className="bg-white/[0.02] p-4 rounded-lg border border-white/5 font-mono text-xs text-slate-400 whitespace-pre-wrap h-32 overflow-y-auto">
                            {recent_activity || "No recent activity log found."}
                        </div>
                    </Section>
                </div>

                <div className="space-y-4">
                    <Section title="Quick Actions">
                        <div className="flex flex-col gap-2">
                            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-left flex items-center gap-3 transition-colors">
                                <CheckSquare className="w-4 h-4 text-purple-400" />
                                View Daily Logs
                            </button>
                            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-left flex items-center gap-3 transition-colors">
                                <FileText className="w-4 h-4 text-blue-400" />
                                Procurement Logs
                            </button>
                            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-left flex items-center gap-3 transition-colors">
                                <Activity className="w-4 h-4 text-emerald-400" />
                                Quality Control
                            </button>
                            {project.procore_id && (
                                <button className="px-4 py-2 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 rounded-lg text-sm text-left flex items-center gap-3 transition-colors text-orange-400">
                                    <RefreshCw className="w-4 h-4" />
                                    Sync Procore
                                </button>
                            )}
                        </div>
                    </Section>
                </div>
            </div>
        </div>
    );
};

export default AltimeterProjectDashboard;
