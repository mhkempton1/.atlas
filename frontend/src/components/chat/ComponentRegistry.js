import React from 'react';
import TaskList from '../tasks/TaskList';
import SchedulerView from '../dashboard/SchedulerView';
import MissionBriefing from '../dashboard/MissionBriefing';

const ComponentRegistry = {
    // Map string keys to Components
    "render_task_list": (props) => <TaskList {...props} />,
    "render_schedule": (props) => <SchedulerView {...props} />,
    "render_briefing": (props) => <MissionBriefing phase={{ phase_name: props.phase_name, project_name: props.project_name }} />,

    // Default fallback
    "unknown": () => <div className="p-4 text-red-400">UI Component Not Found</div>
};

export const renderComponent = (componentName, props) => {
    const Component = ComponentRegistry[componentName] || ComponentRegistry["unknown"];
    return Component(props);
};

export default ComponentRegistry;
