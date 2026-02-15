# ATLAS Frontend Documentation

## 1. Component Hierarchy Overview

The frontend is a React application built with Vite, structured around a central `App.jsx` layout that manages navigation, global state, and routing.

```
App.jsx (Root Component: Layout, Navigation, Permissions, Global State)
├── Dashboard (Command Center)
│   └── Overview of system health, recent notifications, and quick actions.
├── EmailModule (Email Control)
│   └── Intelligent email management, drafting, and categorization.
├── CalendarModule (Calendar)
│   └── Integration with Google Calendar for event visualization and management.
├── SchedulerView (Dept Schedule)
│   └── Department-level scheduling and coordination view.
├── TaskList (Mission Tasks)
│   └── Task management interface for tracking and updating mission tasks.
├── AltimeterTaskView (Altimeter Ops)
│   └── specialized view for Altimeter operational tasks.
├── HistoryView (System Logs)
│   └── Audit logs and system activity history viewer.
├── SystemHealthView (System Health)
│   └── Detailed diagnostics and health metrics of the system.
├── SystemConfig (System Config)
│   └── Configuration panel for system settings and preferences.
├── KnowledgeDashboard (The Library)
│   └── Knowledge base interface for accessing documentation and SOPs.
├── DocumentControl (Document Control)
│   └── Management system for controlled documents and versioning.
├── PortcullisView (Gatekeeper)
│   └── Security and access control interface.
├── ReportsDashboard (System Reports)
│   └── Analytics and reporting dashboard.
├── SystemStatusView (System Status)
│   └── Real-time status monitor for system components.
├── CommandBar (Global Component)
│   └── Quick action bar accessible via `Alt+K` or `Cmd+K`.
└── NotificationCenter (Global Component)
    └── Manages and displays user notifications.
```

## 2. Development Setup

### Prerequisites
- **Node.js**: v18.0.0 or higher is recommended.
- **npm**: v9.0.0 or higher.

### Installation
Install the project dependencies using npm:

```bash
npm install
```

*Note: Key dependencies include `react`, `react-dom`, `vite`, `tailwindcss`, `lucide-react`, `framer-motion`, and `axios`.*

### Running the Development Server
Start the development server with:

```bash
npm run dev
```

- **Local URL**: `http://localhost:4202`
- The application is configured to run on port **4202** by default.

### Environment & Proxy
The frontend uses a Vite proxy configuration to communicate with the backend.
- **API Proxy**: Requests to `/api` are proxied to `http://127.0.0.1:4201`.
- **Configuration**: Managed in `vite.config.js`.

## 3. Design System Reference

The ATLAS design system is built on a "Night Sky" aesthetic, utilizing deep blues, neon accents, and glassmorphism effects.

### Color Palette
Defined in `src/index.css` and `tailwind.config.js`.

| Token Name | Hex / RGBA | Usage |
| :--- | :--- | :--- |
| **Background** | `#05071a` | Main application background (Deep Space) |
| **Card Surface** | `rgba(255, 255, 255, 0.03)` | Glassmorphic card background |
| **Primary (Cyan)** | `#00f2ff` | Main accent, glows, active states |
| **Success (Green)**| `#39ff14` | Status indicators, success messages |
| **Warning (Amber)**| `#ffb100` | Alerts, warnings |
| **Danger (Red)** | `#ff003c` | Errors, critical alerts |
| **Space Blue** | `rgba(26, 42, 108, 0.4)` | Atmospheric gradient component |
| **Solar Orange** | `rgba(242, 153, 74, 0.2)` | Atmospheric gradient component |
| **Nebula Purple**| `rgba(88, 28, 135, 0.3)` | Atmospheric gradient component |

### Typography
Fonts are imported via Google Fonts.

- **Monospace (Default)**: `JetBrains Mono`
  - Usage: Body text, data displays, code, technical readouts.
- **Sans-Serif**: `Inter`
  - Usage: UI elements requiring high legibility at small sizes.
- **Display**: `Outfit`
  - Usage: Headings, large status displays.

### Spacing & Glassmorphism
The design relies heavily on translucency and blur to create depth.

- **Glass Cards**:
  - Background: `bg-white/[0.02]` or `rgba(255, 255, 255, 0.03)`
  - Border: `1px solid rgba(255, 255, 255, 0.08)`
  - Backdrop Filter: `backdrop-blur-xl` or `backdrop-blur-2xl`
  - Hover Effect: `bg-white/[0.06]`, `transform: translateY(-1px)`

### "Night Sky" Aesthetic Guidelines
- **Background**: A fixed multi-layer radial gradient simulating deep space.
- **Star Field**: CSS-generated star field with twinkling animation (`stars-twinkle` keyframes).
- **Glow Effects**: Use `box-shadow` or `text-shadow` with primary colors to simulate bioluminescence or neon tech.
- **Borders**: Subtle, translucent borders that may "pulse" (`pulsing-border-tech`) to indicate activity.
