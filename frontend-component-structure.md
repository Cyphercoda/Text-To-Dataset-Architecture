# Frontend Component Structure & Technical Architecture

## 🏗️ React Application Architecture

### Technology Stack
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS + Headless UI
- **State Management**: Zustand + React Query
- **Routing**: React Router v6
- **Build Tool**: Vite
- **Testing**: Jest + React Testing Library
- **Mobile**: PWA with responsive design

---

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI primitives
│   ├── forms/           # Form components
│   ├── navigation/      # Nav components
│   └── data-display/    # Charts, tables, etc.
├── pages/               # Route components
├── hooks/               # Custom React hooks
├── stores/              # Zustand stores
├── services/            # API services
├── utils/               # Utility functions
├── types/               # TypeScript definitions
└── assets/              # Static assets
```

---

## 🧩 Component Hierarchy

### App Shell Components

#### `App.tsx` (Root Component)
```typescript
interface AppState {
  user: User | null;
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
}

// Main app shell with routing
```

#### `Layout/MainLayout.tsx`
```typescript
interface MainLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  fullWidth?: boolean;
}

Components:
- Header/Navigation
- Sidebar (collapsible)
- Main content area
- Footer
```

#### `Navigation/Header.tsx`
```typescript
Features:
- Logo and branding
- User profile dropdown
- Theme toggle
- Notifications badge
- Mobile hamburger menu
```

#### `Navigation/Sidebar.tsx`
```typescript
Navigation Items:
- Dashboard
- Projects
- Chat Assistant
- Document Upload
- Analytics
- Settings
- Help & Support
```

---

### Page Components

#### `Dashboard/DashboardPage.tsx`
```typescript
interface DashboardData {
  recentJobs: ProcessingJob[];
  systemStats: SystemMetrics;
  quickActions: QuickAction[];
}

Child Components:
- QuickActionsPanel
- RecentJobsList
- SystemStatsCards
- PerformanceCharts
```

#### `Upload/UploadPage.tsx`
```typescript
interface UploadState {
  files: File[];
  uploadProgress: number;
  processingConfig: ProcessingConfig;
  isUploading: boolean;
}

Child Components:
- FileDropZone
- FileList
- ProcessingConfigForm
- ProgressIndicator
```

#### `Chat/ChatPage.tsx`
```typescript
interface ChatState {
  messages: Message[];
  isTyping: boolean;
  attachments: File[];
  chatHistory: ChatSession[];
}

Child Components:
- MessageList
- MessageInput
- TypingIndicator
- AttachmentPreview
- ChatHistory
```

#### `Analytics/AnalyticsPage.tsx`
```typescript
interface AnalyticsData {
  processingMetrics: ProcessingMetrics;
  entityStats: EntityStatistics;
  exportActivity: ExportActivity;
  timeSeriesData: TimeSeriesData;
}

Child Components:
- MetricCards
- ProcessingVolumeChart
- EntityTypesChart
- ExportActivityChart
- PerformanceGauges
```

---

### Reusable UI Components

#### Data Display Components

**`DataTable/DataTable.tsx`**
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  pagination?: PaginationConfig;
  sorting?: SortingConfig;
  filtering?: FilterConfig;
  actions?: ActionConfig<T>[];
}

Features:
- Virtual scrolling for large datasets
- Column sorting and filtering
- Row selection and bulk actions
- Responsive design
- Export functionality
```

**`Chart/Chart.tsx`**
```typescript
interface ChartProps {
  type: 'line' | 'bar' | 'pie' | 'gauge';
  data: ChartData;
  config: ChartConfig;
  responsive?: boolean;
}

Chart Types:
- LineChart (time series data)
- BarChart (categorical data)
- PieChart (proportional data)
- GaugeChart (single metrics)
```

**`MetricCard/MetricCard.tsx`**
```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  loading?: boolean;
}
```

#### Form Components

**`FileUpload/FileDropZone.tsx`**
```typescript
interface FileDropZoneProps {
  onFilesSelected: (files: File[]) => void;
  acceptedTypes: string[];
  maxSize: number;
  multiple?: boolean;
  disabled?: boolean;
}

Features:
- Drag & drop support
- File type validation
- Size limit checking
- Progress indicators
- Error handling
```

**`FormBuilder/ConfigForm.tsx`**
```typescript
interface ConfigFormProps {
  config: ProcessingConfig;
  onChange: (config: ProcessingConfig) => void;
  schema: FormSchema;
}

Form Fields:
- Output format selection
- NLP feature toggles
- Quality level slider
- Batch size options
- Advanced settings
```

#### Navigation Components

**`Breadcrumb/Breadcrumb.tsx`**
```typescript
interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: string;
  maxItems?: number;
}
```

**`TabNavigation/TabNav.tsx`**
```typescript
interface TabNavProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  variant?: 'pills' | 'underline';
}
```

#### Feedback Components

**`ProgressIndicator/ProgressBar.tsx`**
```typescript
interface ProgressBarProps {
  progress: number;
  status: 'pending' | 'processing' | 'complete' | 'error';
  showPercent?: boolean;
  animated?: boolean;
  size?: 'sm' | 'md' | 'lg';
}
```

**`StatusBadge/StatusBadge.tsx`**
```typescript
interface StatusBadgeProps {
  status: ProcessingStatus;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

Status Types:
- Success (green)
- Processing (blue)
- Warning (orange)
- Error (red)
- Pending (gray)
```

**`Toast/ToastProvider.tsx`**
```typescript
interface ToastConfig {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  actions?: ToastAction[];
}
```

---

### Custom Hooks

#### Data Management Hooks

**`useProcessingJobs.ts`**
```typescript
interface UseProcessingJobsReturn {
  jobs: ProcessingJob[];
  createJob: (config: JobConfig) => Promise<void>;
  cancelJob: (jobId: string) => Promise<void>;
  retryJob: (jobId: string) => Promise<void>;
  isLoading: boolean;
  error: Error | null;
}
```

**`useChat.ts`**
```typescript
interface UseChatReturn {
  messages: Message[];
  sendMessage: (message: string, attachments?: File[]) => Promise<void>;
  isTyping: boolean;
  clearChat: () => void;
  exportChat: () => void;
}
```

**`useFileUpload.ts`**
```typescript
interface UseFileUploadReturn {
  uploadFiles: (files: File[]) => Promise<void>;
  uploadProgress: Record<string, number>;
  isUploading: boolean;
  cancelUpload: (fileId: string) => void;
}
```

#### UI State Hooks

**`useResponsive.ts`**
```typescript
interface UseResponsiveReturn {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  breakpoint: Breakpoint;
}
```

**`useLocalStorage.ts`**
```typescript
function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void];
```

---

### State Management

#### Zustand Stores

**`useAppStore.ts`** (Global App State)
```typescript
interface AppState {
  // User & Auth
  user: User | null;
  isAuthenticated: boolean;
  
  // UI State
  theme: Theme;
  sidebarCollapsed: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  toggleSidebar: () => void;
  setTheme: (theme: Theme) => void;
}
```

**`useProcessingStore.ts`** (Processing Jobs)
```typescript
interface ProcessingState {
  jobs: ProcessingJob[];
  activeJob: ProcessingJob | null;
  jobHistory: ProcessingJob[];
  
  // Actions
  addJob: (job: ProcessingJob) => void;
  updateJobStatus: (jobId: string, status: JobStatus) => void;
  removeJob: (jobId: string) => void;
}
```

**`useChatStore.ts`** (Chat State)
```typescript
interface ChatState {
  sessions: ChatSession[];
  activeSession: ChatSession | null;
  
  // Actions
  createSession: () => void;
  addMessage: (sessionId: string, message: Message) => void;
  clearSession: (sessionId: string) => void;
}
```

---

### API Services

#### `api/client.ts`
```typescript
class ApiClient {
  private baseURL: string;
  private headers: Record<string, string>;
  
  // HTTP methods
  get<T>(url: string): Promise<T>;
  post<T>(url: string, data: any): Promise<T>;
  put<T>(url: string, data: any): Promise<T>;
  delete(url: string): Promise<void>;
  
  // File upload
  uploadFiles(files: File[], config: UploadConfig): Promise<UploadResponse>;
}
```

#### `api/processing.ts`
```typescript
interface ProcessingService {
  createJob(config: JobConfig): Promise<ProcessingJob>;
  getJob(jobId: string): Promise<ProcessingJob>;
  cancelJob(jobId: string): Promise<void>;
  getJobResults(jobId: string): Promise<JobResults>;
  downloadResults(jobId: string, format: ExportFormat): Promise<Blob>;
}
```

#### `api/chat.ts`
```typescript
interface ChatService {
  sendMessage(message: string, attachments?: File[]): Promise<Message>;
  getHistory(): Promise<ChatSession[]>;
  exportChat(sessionId: string): Promise<Blob>;
}
```

---

### Mobile-Specific Components

#### `Mobile/BottomNavigation.tsx`
```typescript
interface BottomNavProps {
  items: NavItem[];
  activeItem: string;
  onItemSelect: (itemId: string) => void;
}
```

#### `Mobile/SwipeableViews.tsx`
```typescript
interface SwipeableViewsProps {
  children: React.ReactNode[];
  index: number;
  onIndexChange: (index: number) => void;
}
```

#### `Mobile/PullToRefresh.tsx`
```typescript
interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: React.ReactNode;
  disabled?: boolean;
}
```

---

### Performance Optimizations

#### Code Splitting
```typescript
// Lazy load pages
const DashboardPage = lazy(() => import('./pages/Dashboard/DashboardPage'));
const UploadPage = lazy(() => import('./pages/Upload/UploadPage'));
const ChatPage = lazy(() => import('./pages/Chat/ChatPage'));
```

#### Virtualization
```typescript
// For large datasets
const VirtualizedTable = lazy(() => import('./components/VirtualizedTable'));
const InfiniteScroll = lazy(() => import('./components/InfiniteScroll'));
```

#### Caching Strategy
```typescript
// React Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});
```

This component structure provides a scalable, maintainable frontend architecture optimized for data professionals working with text processing workflows.