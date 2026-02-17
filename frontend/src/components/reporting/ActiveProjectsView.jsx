import React from 'react';

const ActiveProjectsView = ({ projects }) => {
    // Default mock data if no props provided
    const safeProjects = projects || [
        { id: 101, name: "Downtown Renovation", phases: ["Demo", "Rough-in"] },
        { id: 102, name: "Substation Upgrade", phases: ["Excavation"] },
        { id: 103, name: "City Hall Lighting", phases: ["Design", "Procurement", "Install"] }
    ];

    return (
        <div className="p-6 text-center text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <h3 className="text-lg font-bold mb-2">🏗️ Active Projects</h3>
            <p className="mb-2">List of active projects for service calls and contract jobs.</p>
            <div className="flex gap-3 justify-center mt-4">
                <div className="p-3 bg-white/5 rounded-lg border border-white/10 backdrop-blur-sm">
                    <h3 className="text-gray-400 text-[10px] mb-1">Involved Projects</h3>
                    <p className="text-xl font-bold text-white">{safeProjects.length}</p>
                </div>
                <div className="p-3 bg-white/5 rounded-lg border border-white/10 backdrop-blur-sm">
                    <h3 className="text-gray-400 text-[10px] mb-1">Ongoing Phases</h3>
                    <p className="text-xl font-bold text-white">{safeProjects.reduce((acc, p) => acc + (p.phases?.length || 0), 0)}</p>
                </div>
            </div>
        </div>
    );
};

export default ActiveProjectsView;
