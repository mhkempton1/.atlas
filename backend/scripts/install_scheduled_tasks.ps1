$ErrorActionPreference = "Stop"

# 1. Detect Environment
$PythonPath = (Get-Command python).Source
$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
$ExecuteScript = "$ProjectRoot\backend\scripts\execute_mission.py"

Write-Host "🧊 Atlas Autonomous Installer" -ForegroundColor Cyan
Write-Host "--------------------------------"
Write-Host "Python: $PythonPath"
Write-Host "Root:   $ProjectRoot"
Write-Host "Script: $ExecuteScript"
Write-Host ""

if (-not (Test-Path $ExecuteScript)) {
    Write-Error "Could not find execute_mission.py at $ExecuteScript"
}

# 2. Define Tasks
$Tasks = @(
    @{
        Name = "Atlas_Nightly_Maintenance"
        Time = "00:00"
        Type = "maintenance"
        Prompt = "Act as the Autonomous Architect for Atlas. Perform the following nightly maintenance and synthesis: 1. Intelligence Sync: Trigger a full scan of all communication providers. 2. The Oracle Audit: Review the last 24 hours of emails and cross-reference them with the Altimeter database. 3. AGENTS.md Update: Suggest updates for the 'Current Missions' section in AGENTS.md based on tonight's synthesis."
    },
    @{
        Name = "Atlas_Email_Improvement"
        Time = "01:00"
        Type = "email"
        Prompt = "Act as the Communications Engineer for Atlas. Focus on improving the email engine. 1. Audit Performance: Check current IMAP/SMTP logs and optimize connection pooling. 2. Feature Implementation: Suggest robust attachment metadata extraction improvements. 3. Intelligence Refinement: Suggest updates to 'Email Analysis' prompt templates."
    },
    @{
        Name = "Atlas_TasksCalendar_Improvement"
        Time = "02:00"
        Type = "calendar"
        Prompt = "Act as the Product Engineer for Atlas. Focus on improving task management and calendar synchronization. 1. Agent Audit: Evaluate CalendarAgent performance. 2. Smart Scheduling: Suggest 'Smart Deadlines' logic based on email dates. 3. Sync Robustness: Suggest improvements for multi-day event handling."
    },
    @{
        Name = "Atlas_AI_Assistant_Improvement"
        Time = "03:00"
        Type = "ai"
        Prompt = "Act as the AI Researcher for Atlas. Focus on the core 'Personal Assistant' intelligence. 1. Prompt Engineering: Suggest refinements for task_agent.py prompts. 2. Custom Persona: Evaluate response tone against 'Smooth as Ice' standards. 3. Knowledge Indexing: Suggest optimizations for Mission Intel retrieval."
    }
)

# 3. Register Tasks
foreach ($Task in $Tasks) {
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Task.Time
    $Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "backend/scripts/execute_mission.py --type $($Task.Type) --prompt `"$($Task.Prompt)`"" -WorkingDirectory $ProjectRoot
    
    Write-Host "Registering $($Task.Name) at $($Task.Time)..." -NoNewline
    
    try {
        Unregister-ScheduledTask -TaskName $Task.Name -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $Task.Name -Trigger $Trigger -Action $Action -Description "Atlas Autonomous Agent: $($Task.Type)" | Out-Null
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [FAILED]" -ForegroundColor Red
        Write-Error $_
    }
}

Write-Host ""
Write-Host "✅ All Autonomous Agents Scheduled." -ForegroundColor Cyan
Write-Host "To test immediately, search 'Task Scheduler' in Start Menu, right-click a task, and select 'Run'."
