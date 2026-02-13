# Cyloid Frontend

React-based frontend for the Cyloid financial document processing platform using
Next.js 16 and React 19.

## Overview

This frontend provides a user interface for managing:

- **Assignments** - Workflow assignments to clients with status and progress tracking
- **Projects** - Kanban-based project management with drag-drop task organization
- **Canvas** - Visual workflow and assignment visualization using SVG nodes/edges

## Project Structure

```bash
frontend/
├── app/
│   ├── components/
│   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   ├── AssignmentList.tsx    # Assignment list with filtering
│   │   └── ...
│   ├── dashboard/
│   │   ├── assignments/          # Assignment pages
│   │   │   └── [id]/page.tsx    # Assignment detail with hierarchy
│   │   ├── projects/             # Project pages
│   │   │   ├── page.tsx         # Project list (grid)
│   │   │   └── [id]/page.tsx    # Kanban board
│   │   └── ...
│   ├── canvas/
│   │   ├── [type]/
│   │   │   └── [id]/page.tsx    # Canvas visualization
│   │   └── ...
│   ├── hooks/
│   │   └── useApi.ts            # Data fetching hooks
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   └── globals.css               # Global styles
├── public/                        # Static assets
├── next.config.ts                # Next.js configuration
├── tailwind.config.ts            # TailwindCSS configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json                  # Dependencies
```

## Features

### Assignment Management

- **List View** - Browse all assignments with status, priority, and progress filters
- **Detail View** - Expand hierarchy to see stages → steps → tasks
- **Progress Tracking** - Visual progress bars and percentage completion
- **Status Updates** - Update assignment and task status
- **Canvas Mode** - Visual workflow representation with node/edge visualization

### Project Management (Kanban)

- **Kanban Board** - 4-column layout (To Do, In Progress, Review, Completed)
- **Drag & Drop** - Move tasks between columns and reorder within columns
- **Task Management** - Create, edit, and delete project tasks
- **Statistics** - Real-time task counts and completion percentages
- **Filtering** - Filter projects by status

### Canvas Visualization

- **Workflow Canvas** - View workflow templates as interactive node diagram
- **Assignment Canvas** - Show assignment status with color-coded stages
- **Pan & Zoom** - Navigate complex workflows
- **Details Panel** - Click nodes to see detailed information

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Running backend at `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
# or
yarn install
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Running Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Key Components & Pages

### Components

**AssignmentList** (`app/components/AssignmentList.tsx`)

- Paginated list of assignments
- Filter by status and priority
- Progress bar for each assignment
- Links to detail and canvas views

**KanbanBoard** (`app/dashboard/projects/[id]/page.tsx`)

- 4-column Kanban board
- Drag-drop task movement
- Task statistics
- Quick add task form

**WorkflowCanvas** (`app/canvas/[type]/[id]/page.tsx`)

- SVG-based canvas rendering
- Interactive node selection
- Pan and zoom controls
- Real-time status visualization

### Pages

| Page | Route | Purpose |
| --- | --- | --- |
| Assignment List | `/dashboard/assignments` | Browse assignments |
| Assignment Detail | `/dashboard/assignments/[id]` | View hierarchy |
| Project List | `/dashboard/projects` | Browse projects |
| Kanban Board | `/dashboard/projects/[id]` | Manage tasks |
| Workflow Canvas | `/canvas/workflows/[id]` | View template |
| Assignment Canvas | `/canvas/assignments/[id]` | View assignment status |

## API Hooks (`app/hooks/useApi.ts`)

Centralized data fetching with React hooks:

```typescript
import { useAssignments, useProjects, useKanbanBoard } from '@/app/hooks/useApi';

// In component:
const { data, loading, error } = useAssignments('org-123', {
  status: 'active',
  page: 1,
});
```

Available hooks:

- `useAssignments()` - Fetch assignments list
- `useAssignmentDetail()` - Fetch single assignment
- `useProjects()` - Fetch projects list
- `useKanbanBoard()` - Fetch Kanban board
- `useWorkflowCanvas()` - Fetch workflow visualization
- `useAssignmentCanvas()` - Fetch assignment visualization

## Styling

- **TailwindCSS** for utility-first styling
- **Custom CSS** in `app/globals.css` for custom variables and components
- Color scheme: Blue (#2196F3) as primary, with green, red, yellow accents

## Building for Production

```bash
npm run build
npm run start
```

Or deploy to Vercel:

```bash
npm install -g vercel
vercel
```

## To-Do

- [ ] Role-based access control (RBAC)
- [ ] Real-time updates with WebSocket
- [ ] Bulk operations on tasks
- [ ] Advanced filtering and search
- [ ] Export/import functionality
- [ ] Notification system
- [ ] User preferences/settings
- [ ] Mobile responsive improvements

## Troubleshooting

### API Connection Issues

- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Browser console for network errors

### Styling Issues

- Run `npm run build` to rebuild Tailwind
- Clear `.next` folder: `rm -rf .next`

### State Not Updating

- Check API responses in Network tab
- Verify component `useEffect` dependencies
- Use React DevTools to inspect state
