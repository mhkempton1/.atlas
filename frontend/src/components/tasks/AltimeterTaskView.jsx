import React, { useState, useEffect, useCallback } from 'react';
import { Network, RefreshCw, Folder, Briefcase, Calendar } from 'lucide-react';
import { PageHeader, Spinner, EmptyState, Section, StatusBadge } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { SYSTEM_API } from '../../services/api';

const AltimeterTaskView = () => {
    const { toast, toastElement } = useToast();
    const [loading, setLoading] = useState(true);
    const [projects, setProjects] = useState([]);
    const [error, setError] = useState(null);

    const connectToAltimeter = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await SYSTEM_API.getAltimeterProjects();
            setProjects(data);
            toast("Connected to Altimeter via Atlas Bridge", "success");
        } catch (err) {
            console.error("Altimeter connection failed", err);
            setError("Bridge connection failed. Check backend logs.");
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => {
        connectToAltimeter();
    }, [connectToAltimeter]);

    if (loading && projects.length === 0) {
        return <Spinner label="Handshaking with Altimeter Bridge..." />;
    }

    return (
        <div className="h-full flex flex-col space-y-6">
            <PageHeader
                icon={Network}
                title="Altimeter Integration"
                subtitle={error ? "Bridge Status: Offline" : "Bridge Status: Active"}
            >
                {error && (
                    <button
                        onClick={connectToAltimeter}
                        className="px-3 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded-md text-xs font-bold hover:bg-red-500/20 flex items-center gap-2"
                    >
                        <RefreshCw className="w-3 h-3" /> RETRY CONNECTION
                    </button>
                )}
            </PageHeader>

            {error ? (
                <EmptyState
                    icon={Network}
                    title="Altimeter System Unavailable"
                    message={`Ensure the Altimeter service is running on Port 4203.\n\nDiagnostic: ${error}`}
                    action={
                        <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/5 font-mono text-[10px] text-gray-400 text-left w-full max-w-sm backdrop-blur-sm">
                            <p>Target: http://127.0.0.1:4203/api/projects</p>
                            <p>Protocol: HTTP/1.1</p>
                            <p>Bridge: v0.4.1-alpha</p>
                        </div>
                    }
                />
            ) : (
                <div className="flex-1 overflow-auto">
                    {projects.length === 0 ? (
                        <EmptyState
                            icon={Folder}
                            title="No Projects Found"
                            message="Altimeter returned an empty project list."
                        />
                    ) : (
                        <Section title="Active Projects" count={projects.length}>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {projects.map(p => (
                                    <div key={p.id} className="bg-white/[0.03] border border-white/5 p-4 rounded-xl hover:border-purple-500/30 transition-all cursor-pointer group backdrop-blur-md">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="p-2 bg-white/10 rounded-lg group-hover:bg-purple-500/10 group-hover:text-purple-400 transition-colors">
                                                <Briefcase className="w-5 h-5 text-gray-400" />
                                            </div>
                                            <StatusBadge status={p.status || 'Active'} />
                                        </div>
                                        <h3 className="font-bold text-gray-200 group-hover:text-white mb-1">{p.name}</h3>
                                        <p className="text-xs text-gray-500 mb-4">{p.description || "No description provided."}</p>

                                        <div className="flex items-center gap-2 text-xs text-gray-400 border-t border-white/5 pt-3">
                                            <Calendar className="w-3 h-3" />
                                            <span>Updated: {new Date(p.updated_at || Date.now()).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Section>
                    )}
                </div>
            )}
            {toastElement}
        </div>
    );
};

export default AltimeterTaskView;
