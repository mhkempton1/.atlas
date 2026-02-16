import React, { useState, useEffect, useCallback } from 'react';
import { SYSTEM_API } from '../../services/api';
import { PageHeader, Section, Spinner, EmptyState, StatusBadge } from '../shared/UIComponents';
import { useToast } from '../../hooks/useToast';
import { CheckSquare, Plus, Trash2, Calendar, AlertCircle, Briefcase, Home, User, X, ChevronDown, Check, Link, Zap, RotateCw, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';
import MissionIntelSnippet from '../shared/MissionIntelSnippet';
import { webSocketService } from '../../services/websocket';

const ConflictModal = ({ isOpen, onClose, conflictData, onResolve }) => {
    if (!isOpen || !conflictData) return null;

    const { local, remote } = conflictData;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="bg-slate-900 border border-white/10 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                <div className="p-6 border-b border-white/10 flex justify-between items-center">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <AlertTriangle className="text-amber-500" />
                        Sync Conflict Resolution
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X />
                    </button>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Local Version */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-blue-400">Local Version (Atlas)</h3>
                            <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded">Last Modified</span>
                        </div>
                        <div className="bg-white/5 p-4 rounded-lg space-y-3 border border-blue-500/20">
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Title</label>
                                <p className="text-white font-medium">{local.title}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Status</label>
                                <p className="text-white">{local.status}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Description</label>
                                <p className="text-gray-300 text-sm whitespace-pre-wrap">{local.description || "N/A"}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Due Date</label>
                                <p className="text-gray-300 text-sm">{local.due_date ? new Date(local.due_date).toLocaleString() : "N/A"}</p>
                            </div>
                        </div>
                        <button
                            onClick={() => onResolve("local")}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            <CheckCircle className="w-4 h-4" />
                            Keep Local Version
                        </button>
                    </div>

                    {/* Remote Version */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-purple-400">Remote Version (Altimeter)</h3>
                            <span className="text-xs bg-purple-500/10 text-purple-400 px-2 py-1 rounded">Incoming</span>
                        </div>
                        <div className="bg-white/5 p-4 rounded-lg space-y-3 border border-purple-500/20">
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Title</label>
                                <p className="text-white font-medium">{remote.title}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Status</label>
                                <p className="text-white">{remote.status}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Description</label>
                                <p className="text-gray-300 text-sm whitespace-pre-wrap">{remote.description || "N/A"}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase">Due Date</label>
                                <p className="text-gray-300 text-sm">{remote.due_date ? new Date(remote.due_date).toLocaleString() : "N/A"}</p>
                            </div>
                        </div>
                        <button
                            onClick={() => onResolve("remote")}
                            className="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                            <RotateCw className="w-4 h-4" />
                            Accept Remote Version
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const TaskList = () => {
    const [tasks, setTasks] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [filter, setFilter] = useState('all'); // all, todo, in_progress, done
    const { addToast, toastElement } = useToast();
    const [syncStatuses, setSyncStatuses] = useState({});

    // Conflict Handling
    const [conflictModalOpen, setConflictModalOpen] = useState(false);
    const [currentConflict, setCurrentConflict] = useState(null);
    const [resolvingId, setResolvingId] = useState(null);

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
            const data = await SYSTEM_API.getTasks();
            setTasks(data);
        } catch (error) {
            console.error("Failed to load tasks", error);
            addToast("Failed to load tasks", "error");
        } finally {
            setIsLoading(false);
        }
    }, [addToast]);

    // WebSocket Subscription
    useEffect(() => {
        loadTasks();
        const unsubscribe = webSocketService.subscribe((msg) => {
            if (msg.type === 'sync_update' && msg.entity_type === 'task') {
                setSyncStatuses(prev => ({
                    ...prev,
                    [msg.entity_id]: msg.status
                }));

                // Reload on synced or conflict to ensure data consistency
                if (msg.status === 'synced' || msg.status === 'conflict') {
                    // Small delay to ensure DB commit visible
                    setTimeout(() => {
                         // Ideally we optimistically update, but reloading is safer for full consistency
                         // We can also just trigger a background reload without spinner
                         SYSTEM_API.getTasks().then(setTasks).catch(console.error);
                    }, 500);
                }
            }
        });
        return () => unsubscribe();
    }, [loadTasks]);

    const handleCreateTask = async () => {
        if (!newTask.title) return;
        try {
            await SYSTEM_API.createTask(newTask);
            setNewTask({ title: '', description: '', priority: 'medium', category: 'work', project_id: '', due_date: null });
            setShowCreateForm(false);
            loadTasks();
            addToast("Task created successfully", "success");
        } catch (error) {
            addToast("Failed to create task", "error");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure?")) return;
        try {
            await SYSTEM_API.deleteTask(id);
            setTasks(tasks.filter(t => t.task_id !== id));
            addToast("Task deleted", "success");
        } catch (error) {
            addToast("Failed to delete task", "error");
        }
    };

    const cycleStatus = async (task) => {
        const statuses = ['open', 'in_progress', 'done'];
        const nextIndex = (statuses.indexOf(task.status) + 1) % statuses.length;
        const nextStatus = statuses[nextIndex];

        try {
            // Optimistic update
            setTasks(tasks.map(t => t.task_id === task.task_id ? { ...t, status: nextStatus } : t));

            await SYSTEM_API.updateTask(task.task_id, { status: nextStatus });
        } catch (error) {
            console.error("Failed to update status", error);
            addToast(error.response?.data?.detail || "Failed to update status", "error");
            loadTasks(); // Revert
        }
    };

    const cyclePriority = async (task) => {
        const priorities = ['low', 'medium', 'high'];
        const nextIndex = (priorities.indexOf(task.priority) + 1) % priorities.length;
        const nextPriority = priorities[nextIndex];

        try {
            setTasks(tasks.map(t => t.task_id === task.task_id ? { ...t, priority: nextPriority } : t));
            await SYSTEM_API.updateTask(task.task_id, { priority: nextPriority });
        } catch (error) {
            addToast("Failed to update priority", "error");
            loadTasks();
        }
    };

    // Conflict Resolution
    const handleConflictClick = async (task) => {
        setResolvingId(task.task_id);
        try {
            const details = await SYSTEM_API.getConflictDetails("task", task.task_id);
            setCurrentConflict({ ...details, task_id: task.task_id });
            setConflictModalOpen(true);
        } catch (error) {
            addToast("Failed to load conflict details", "error");
        } finally {
            setResolvingId(null);
        }
    };

    const handleResolve = async (strategy) => {
        if (!currentConflict) return;
        try {
            await SYSTEM_API.resolveConflict("task", currentConflict.task_id, strategy);
            addToast("Conflict resolution queued", "success");
            setConflictModalOpen(false);
            setCurrentConflict(null);
            // Optimistically update status to pending
            setSyncStatuses(prev => ({ ...prev, [currentConflict.task_id]: 'pending' }));
        } catch (error) {
            addToast("Failed to resolve conflict", "error");
        }
    };

    const getPriorityColor = (p) => {
        switch (p) {
            case 'high': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            case 'low': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
        }
    };

    const getCategoryIcon = (c) => {
        switch (c) {
            case 'work': return <Briefcase className="w-3 h-3" />;
            case 'personal': return <User className="w-3 h-3" />;
            case 'home': return <Home className="w-3 h-3" />;
            default: return <CheckSquare className="w-3 h-3" />;
        }
    };

    const filteredTasks = tasks.filter(t => {
        if (filter === 'all') return t.status !== 'done';
        if (filter === 'done') return t.status === 'done';
        if (filter === 'todo') return t.status === 'open';
        return t.status === filter;
    });

    return (
        <div className="h-full flex flex-col bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
            <ConflictModal
                isOpen={conflictModalOpen}
                onClose={() => setConflictModalOpen(false)}
                conflictData={currentConflict}
                onResolve={handleResolve}
            />

            <PageHeader
                title="Mission Tasks"
                subtitle="Tactical Objectives & Directives"
                action={
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white p-2 rounded-lg transition-all"
                    >
                        <Plus className={`w-5 h-5 transition-transform ${showCreateForm ? 'rotate-45' : ''}`} />
                    </button>
                }
            />

            {/* Create Task Form */}
            {showCreateForm && (
                <div className="p-4 bg-white/5 border-b border-white/10 space-y-4 animate-in slide-in-from-top-4 fade-in">
                    <div className="flex gap-4">
                        <input
                            type="text"
                            placeholder="Task Directive..."
                            className="flex-1 bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500/50"
                            value={newTask.title}
                            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                        />
                        <div className="flex gap-2">
                            <select
                                className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50"
                                value={newTask.priority}
                                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                            >
                                <option value="low">Low Priority</option>
                                <option value="medium">Medium Priority</option>
                                <option value="high">High Priority</option>
                            </select>
                            <select
                                className="bg-slate-950 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50"
                                value={newTask.project_id}
                                onChange={(e) => setNewTask({ ...newTask, project_id: e.target.value })}
                            >
                                <option value="">No Project</option>
                                {projects.map(p => (
                                    <option key={p.id} value={p.altimeter_project_id}>{p.name}</option>
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
                                className="bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:border-emerald-500/50"
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
            <div className="flex gap-2 border-b border-white/5 pb-4 px-4 pt-4">
                {['all', 'todo', 'in_progress', 'done'].map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all ${filter === f
                            ? 'bg-purple-600/30 text-purple-400 border border-purple-500/40 backdrop-blur-md'
                            : 'bg-white/5 text-gray-400 hover:text-white border border-transparent'
                            }`}
                    >
                        {f.replace('_', ' ')}
                    </button>
                ))}
            </div>

            {/* Task List */}
            <div className="flex-1 overflow-y-auto space-y-3 p-4 custom-scrollbar" >
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
                        filteredTasks.map(task => {
                            const currentSyncStatus = syncStatuses[task.task_id] || task.sync_status || 'synced';

                            return (
                                <div
                                    key={task.task_id}
                                    className={`group bg-white/[0.02] border border-white/5 hover:border-white/10 rounded-xl p-4 transition-all flex items-start gap-4 backdrop-blur-sm ${task.status === 'done' ? 'opacity-50' : ''}`}
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
                                            <div className="flex items-center gap-2">
                                                {/* Sync Status Badge */}
                                                {currentSyncStatus === 'pending' && (
                                                    <span className="flex items-center gap-1 text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20" title="Syncing...">
                                                        <RotateCw className="w-3 h-3 animate-spin" />
                                                        Syncing
                                                    </span>
                                                )}
                                                {currentSyncStatus === 'error' && (
                                                    <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20" title="Sync Failed">
                                                        <AlertCircle className="w-3 h-3" />
                                                        Error
                                                    </span>
                                                )}
                                                {currentSyncStatus === 'conflict' && (
                                                    <button
                                                        onClick={() => handleConflictClick(task)}
                                                        disabled={resolvingId === task.task_id}
                                                        className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 hover:bg-amber-500/20 transition-colors cursor-pointer"
                                                        title="Click to resolve conflict"
                                                    >
                                                        {resolvingId === task.task_id ? <Spinner size="xs" /> : <AlertTriangle className="w-3 h-3" />}
                                                        Conflict
                                                    </button>
                                                )}

                                                <button
                                                    onClick={() => cyclePriority(task)}
                                                    className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border cursor-pointer hover:opacity-80 transition-opacity ${getPriorityColor(task.priority)}`}
                                                >
                                                    {task.priority}
                                                </button>
                                            </div>
                                        </div>

                                        {task.description && (
                                            <div className="task-body mt-2">
                                                {/* Mission Intel Parsing Logic */}
                                                {task.description.includes('### 💎 Mission Intel') ? (
                                                    <>
                                                        <p className="text-xs text-gray-500 line-clamp-1 mb-2">
                                                            {task.description.split('### 💎 Mission Intel')[0]}
                                                        </p>
                                                        <div className="space-y-1">
                                                            {task.description.split('### 💎 Mission Intel')[1]
                                                                .split('\n- ')
                                                                .filter(line => line.trim() && line.includes(':'))
                                                                .map((line, idx) => {
                                                                    const [title, snippet] = line.replace(/^\*\*|\*\*$/g, '').split(': ');
                                                                    return (
                                                                        <MissionIntelSnippet
                                                                            key={idx}
                                                                            intel={{ title: title.replace('**', ''), snippet: snippet }}
                                                                            type="sop"
                                                                        />
                                                                    );
                                                                })
                                                            }
                                                        </div>
                                                    </>
                                                ) : (
                                                    <p className="text-xs text-gray-500 line-clamp-2 mb-2">{task.description}</p>
                                                )}
                                            </div>
                                        )}

                                        <div className="flex items-center gap-4 text-[10px] text-gray-500 font-mono mt-2">
                                            <span className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded uppercase tracking-wider">
                                                {getCategoryIcon(task.category)}
                                                {task.category}
                                            </span>
                                            {task.project_id && (
                                                <span className="flex items-center gap-1.5 px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded uppercase tracking-wider animate-pulse">
                                                    <Link className="w-3 h-3" />
                                                    {task.project_id}
                                                </span>
                                            )}
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
                            );
                        })
                    )}
            </div >
            {toastElement}
        </div >
    );
};

export default TaskList;
