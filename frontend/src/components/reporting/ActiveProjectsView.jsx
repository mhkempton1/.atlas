import React from 'react';

const ActiveProjectsView = ({ projects }) => {
    return (
        <div className="p-10 text-center text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <h3 className="text-xl font-bold mb-2">🏗️ Active Projects</h3>
            <p className="mb-4">List of active projects for service calls and contract jobs.</p>
            <div className="flex gap-4 justify-center mt-4">
                <div className="p-4 bg-white/5 rounded-lg border border-white/10 backdrop-blur-sm">
                    <h3 className="text-gray-400 text-sm mb-1">Involved Projects</h3>
                    <p className="text-2xl font-bold text-white">{projects.length}</p>
                </div>
                <div className="p-4 bg-white/5 rounded-lg border border-white/10 backdrop-blur-sm">
                    <h3 className="text-gray-400 text-sm mb-1">Ongoing Phases</h3>
                    <p className="text-2xl font-bold text-white">{projects.reduce((acc, p) => acc + p.phases.length, 0)}</p>
                </div>
            </div>
        </div>
    );
};

export default ActiveProjectsView;
