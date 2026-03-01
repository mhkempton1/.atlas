import React, { useState } from 'react';
import { Users, Clock, Briefcase, Box, Truck, Zap } from 'lucide-react';
import { SYSTEM_API } from '../../services/api';
import { useToast } from '../../hooks/useToast';
import ActiveEmployeesView from './ActiveEmployeesView';
import TimeCardsView from './TimeCardsView';
import ActiveProjectsView from './ActiveProjectsView';
import WorkflowView from './WorkflowView';
import SupplyChainView from './SupplyChainView';

const ReportsDashboard = () => {
    const [activeTab, setActiveTab] = useState('employees');
    const { addToast, toastElement } = useToast();
    const [isTriggering, setIsTriggering] = useState(false);

    const handleTriggerMorningBriefing = async () => {
        setIsTriggering(true);
        try {
            await SYSTEM_API.triggerMorningBriefing();
            if (addToast) addToast("Morning Briefing dispatched successfully!", "success");
        } catch (error) {
            console.error("Failed to dispatch briefing:", error);
            if (addToast) addToast("Failed to dispatch Morning Briefing", "error");
        } finally {
            setIsTriggering(false);
        }
    };

    const TABS = [
        { id: 'employees', label: 'Active Employees', icon: Users },
        { id: 'timecards', label: 'Time Cards', icon: Clock },
        { id: 'projects', label: 'Active Projects', icon: Briefcase },
        { id: 'workflow', label: 'Workflow (Boxes)', icon: Box },
        { id: 'supply', label: 'Supply Chain / Production', icon: Truck },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'employees': return <ActiveEmployeesView />;
            case 'timecards': return <TimeCardsView />;
            case 'projects': return <ActiveProjectsView />;
            case 'workflow': return <WorkflowView />;
            case 'supply': return <SupplyChainView />;
            default: return <ActiveEmployeesView />;
        }
    };

    return (
        <div className="h-full flex flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-indigo-500/20 rounded-md">
                        <Box className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white">Atlas Reports</h2>
                        <p className="text-xs text-white/40">Operational intelligence and status reporting</p>
                    </div>
                </div>

                <button
                    onClick={handleTriggerMorningBriefing}
                    disabled={isTriggering}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600/30 to-indigo-600/30 hover:from-purple-600/50 hover:to-indigo-600/50 text-purple-300 border border-purple-500/30 rounded-lg text-sm font-bold transition-all backdrop-blur-md shadow-lg disabled:opacity-50"
                    title="Generate and email the Morning Briefing to management"
                >
                    <Zap className={`w-4 h-4 text-amber-400 ${isTriggering ? 'animate-pulse' : ''}`} />
                    {isTriggering ? 'Dispatching...' : 'Trigger Morning Briefing'}
                </button>
            </div>
            <div className="flex gap-2 border-b border-white/5 pb-1 overflow-x-auto">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-t-lg font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                            ? 'bg-white/10 text-white border-b-2 border-purple-500 backdrop-blur-md'
                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="flex-1 bg-white/[0.02] backdrop-blur-xl rounded-b-lg rounded-tr-lg p-4 shadow-2xl border border-white/10 min-h-0 overflow-auto">
                {renderContent()}
            </div>
            {toastElement && toastElement}
        </div>
    );
};

export default ReportsDashboard;
