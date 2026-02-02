import React, { useState, useEffect, useCallback } from 'react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState, StatusBadge } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { CheckSquare, Plus, Trash2, Calendar, AlertCircle, Briefcase, Home, User, X, ChevronDown, Check } from 'lucide-react';

const TaskList = () => {
    const [tasks, setTasks] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [filter, setFilter] = useState('all'); // all, todo, in_progress, done
    const { addToast, toastElement } = useToast();

    // Form State
    const [newTask, setNewTask] = useState({
        title: '',
        description: '',
        priority: 'medium',
        category: 'work',
        project_id: '',
        due_date: null
    });

    // Altimeter Projects
    const [projects, setProjects] = useState([]);

    useEffect(() => {
        // Fetch Altimeter Projects for the dropdown
        const fetchProjects = async () => {
            try {
                const data = await SYSTEM_API.getAltimeterProjects();
                setProjects(data);
            } catch (err) {
                console.error("Failed to load projects", err);
            }
        };
        fetchProjects();
    }, []);

    const loadTasks = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await SYSTEM_API.getTasks(); // Fetch all
            setTasks(data);
        } catch (error) {
            console.error("Failed to load tasks", error);
            addToast("Failed to load tasks", "error");
        } finally {
            setIsLoading(false);
        }
    }, [addToast]);

    useEffect(() => {
        loadTasks();
    }, [loadTasks]);

    const handleCreateTask = async () => {
        if (!newTask.title.trim()) {
            addToast("Task title is required", "error");
            return;
        }

        try {
            // Clean up the task data before sending
            const taskToCreate = {
                ...newTask,
                due_date: newTask.due_date || null
            };
            await SYSTEM_API.createTask(taskToCreate);
            addToast("Task created successfully", "success");
            setNewTask({ title: '', description: '', priority: 'medium', category: 'work', project_id: '', due_date: null });
            setShowCreateForm(false);
            loadTasks();
        } catch (error) {
            console.error("Failed to create task", error);
            const errorMsg = error.response?.data?.detail?.[0]?.msg || error.message || "Failed to create task";
            addToast(`Creation Error: ${errorMsg}`, "error");
        }
    };

    const handleDelete = async (taskId) => {
        if (!confirm("Are you sure you want to delete this task?")) return;
        try {
            await SYSTEM_API.deleteTask(taskId);
            setTasks(tasks.filter(t => t.task_id !== taskId));
            addToast("Task deleted", "success");
        } catch (error) {
            console.error("Delete failed", error);
            addToast("Failed to delete task", "error");
        }
    };

    const cycleStatus = async (task) => {
        const statusOrder = ['todo', 'in_progress', 'done'];
        const currentIndex = statusOrder.indexOf(task.status);
        const nextStatus = statusOrder[(currentIndex + 1) % statusOrder.length];

        // Optimistic update
        const updatedTasks = tasks.map(t =>
            t.task_id === task.task_id ? { ...t, status: nextStatus } : t
        );
        setTasks(updatedTasks);

        try {
            await SYSTEM_API.updateTask(task.task_id, { status: nextStatus });
        } catch (error) {
            console.error("Update failed", error);
            addToast("Failed to update status", "error");
            loadTasks(); // Revert
        }
    };

    const cyclePriority = async (task) => {
        const priorityOrder = ['low', 'medium', 'high'];
        const currentIndex = priorityOrder.indexOf(task.priority);
        const nextPriority = priorityOrder[(currentIndex + 1) % priorityOrder.length];

        // Optimistic update
        const updatedTasks = tasks.map(t =>
            t.task_id === task.task_id ? { ...t, priority: nextPriority } : t
        );
        setTasks(updatedTasks);

        try {
            await SYSTEM_API.updateTask(task.task_id, { priority: nextPriority });
        } catch (error) {
            console.error("Priority update failed", error);
            addToast("Failed to update priority", "error");
            loadTasks(); // Revert
        }
    };

    const getPriorityColor = (p) => {
        switch (p) {
            case 'high': return 'text-red-400 bg-red-500/10 border-red-500/20';
            case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
            case 'low': return 'text-green-400 bg-green-500/10 border-green-500/20';
            default: return 'text-gray-400';
        }
    };

    const getCategoryIcon = (c) => {
        switch (c) {
            case 'work': return <Briefcase className="w-3 h-3" />;
            case 'home': return <Home className="w-3 h-3" />;
            case 'personal': return <User className="w-3 h-3" />;
            default: return <CheckSquare className="w-3 h-3" />;
        }
    };

    const filteredTasks = tasks.filter(t => {
        if (filter === 'all') return true;
        return t.status === filter;
    });

    return (
        <div className="h-full flex flex-col space-y-6 animate-fade-in p-6">
            <PageHeader
                title="Task Management"
                subtitle="Track, Prioritize & Execute"
                icon={CheckSquare}
                actions={
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${showCreateForm ? 'bg-red-500/20 text-red-400' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                            }`}
                    >
                        {showCreateForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                        {showCreateForm ? 'Cancel' : 'New Task'}
                    </button>
                }
            />

            {/* Inline Creation Form */}
            {showCreateForm && (
                <div className="bg-slate-900/50 border border-white/10 rounded-xl p-6 mb-6 backdrop-blur-sm">
                    <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-4">Create New Task</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <input
                            type="text"
                            placeholder="Task Title *"
                            className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500/50"
                            value={newTask.title}
                            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                        />
                        <div className="flex gap-2">
                            <select
                                className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50 flex-1"
                                value={newTask.priority}
                                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                            >
                                <option value="high">High Priority</option>
                                <option value="medium">Medium Priority</option>
                                <option value="low">Low Priority</option>
                            </select>
                            <select
                                className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50 flex-1"
                                value={newTask.category}
                                onChange={(e) => setNewTask({ ...newTask, category: e.target.value })}
                            >
                                <option value="work">Work</option>
                                <option value="personal">Personal</option>
                                <option value="home">Home</option>
                            </select>
                        </div>
                        {/* Project Selector */}
                        <div className="mt-2">
                            <select
                                className="w-full bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50"
                                value={newTask.project_id || ""}
                                onChange={(e) => setNewTask({ ...newTask, project_id: e.target.value })}
                            >
                                <option value="">Select Altimeter Project (Optional)</option>
                                {projects.map(p => (
                                    <option key={p.id} value={p.altimeter_project_id}>
                                        {p.altimeter_project_id} - {p.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <textarea
                            placeholder="Description (Optional)"
                            className="flex-1 bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500/50 h-20 resize-none"
                            value={newTask.description}
                            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                        />
                        <div className="flex flex-col gap-2">
                            <input
                                type="datetime-local"
                                className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50"
                                value={newTask.due_date}
                                onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                            />
                            <button
                                onClick={handleCreateTask}
                                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-all"
                            >
                                Create Task
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Filter Tabs */}
            <div className="flex gap-2 border-b border-white/5 pb-4">
                {['all', 'todo', 'in_progress', 'done'].map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all ${filter === f
                            ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                            : 'bg-slate-800/30 text-gray-400 hover:text-white border border-transparent'
                            }`}
                    >
                        {f.replace('_', ' ')}
                    </button>
                ))}
            </div>

            {/* Task List */}
            <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar" >
                {
                    isLoading ? (
                        <div className="flex justify-center py-20" > <Spinner size="lg" /></div>
                    ) : filteredTasks.length === 0 ? (
                        <EmptyState
                            icon={CheckSquare}
                            title="No Tasks Found"
                            description="You're all caught up! Create a new task to get started."
                            action={{ label: "Create Task", onClick: () => setShowCreateForm(true) }}
                        />
                    ) : (
                        filteredTasks.map(task => (
                            <div
                                key={task.task_id}
                                className={`group bg-slate-900/40 border border-white/5 hover:border-white/10 rounded-xl p-4 transition-all flex items-start gap-4 ${task.status === 'done' ? 'opacity-50' : ''}`}
                            >
                                {/* Status Checkbox */}
                                <button
                                    onClick={() => cycleStatus(task)}
                                    className={`mt-1 w-5 h-5 rounded border flex items-center justify-center transition-all ${task.status === 'done'
                                        ? 'bg-emerald-500 border-emerald-500 text-black'
                                        : task.status === 'in_progress'
                                            ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                                            : 'border-gray-600 hover:border-emerald-500'
                                        }`}
                                >
                                    {task.status === 'done' && <Check className="w-3.5 h-3.5" />}
                                    {task.status === 'in_progress' && <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />}
                                </button>

                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start mb-1">
                                        <h4 className={`text-sm font-medium truncate pr-2 ${task.status === 'done' ? 'line-through text-gray-500' : 'text-white'}`}>
                                            {task.title}
                                        </h4>
                                        <button
                                            onClick={() => cyclePriority(task)}
                                            className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border cursor-pointer hover:opacity-80 transition-opacity ${getPriorityColor(task.priority)}`}
                                        >
                                            {task.priority}
                                        </button>
                                    </div>

                                    {task.description && <p className="text-xs text-gray-500 line-clamp-2 mb-2">{task.description}</p>}

                                    <div className="flex items-center gap-4 text-[10px] text-gray-500 font-mono">
                                        <span className="flex items-center gap-1.5 px-2 py-1 bg-slate-950 rounded uppercase tracking-wider">
                                            {getCategoryIcon(task.category)}
                                            {task.category}
                                        </span>
                                        {task.due_date && (
                                            <span className={`flex items-center gap-1 ${new Date(task.due_date) < new Date() && task.status !== 'done' ? 'text-red-400' : ''
                                                }`}>
                                                <Calendar className="w-3 h-3" />
                                                {new Date(task.due_date).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <button
                                    onClick={() => handleDelete(task.task_id)}
                                    className="opacity-0 group-hover:opacity-100 p-2 text-gray-600 hover:text-red-400 transition-all"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))
                    )}
            </div >
            {toastElement}
        </div >
    );
};

export default TaskList;
