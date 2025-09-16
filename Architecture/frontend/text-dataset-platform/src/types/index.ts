// Core application types based on workflow documentation

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'free' | 'basic' | 'pro' | 'enterprise';
  company?: string;
  createdDate: string;
  subscriptionTier: string;
  usageLimits: UsageLimits;
}

export interface UsageLimits {
  apiCallsPerDay: number;
  uploadVolumePerDay: number; // in MB
  documentsPerDay: number;
  concurrentUploads: number;
}

export interface Document {
  id: string;
  userId: string;
  filename: string;
  uploadDate: string;
  status: 'uploading' | 'validating' | 'processing' | 'completed' | 'failed';
  fileSize: number;
  format: string;
  processingStage: ProcessingStage;
  qualityScore?: number;
  language?: string;
}

export interface ProcessingStage {
  current: 'validation' | 'extraction' | 'nlp' | 'dataset_generation' | 'completed';
  progress: number;
  estimatedCompletion?: string;
  errorMessage?: string;
}

export interface ProcessingJob {
  id: string;
  userId: string;
  documentIds: string[];
  status: 'queued' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  createdDate: string;
  processingConfig: ProcessingConfig;
  progressPercentage: number;
  costEstimate: number;
}

export interface ProcessingConfig {
  extractEntities: boolean;
  analyzeSentiment: boolean;
  classifyDocument: boolean;
  extractKeyPhrases: boolean;
  qualityThreshold: number;
  outputFormats: DatasetFormat[];
}

export interface AnalysisResults {
  documentId: string;
  entities: Entity[];
  sentiment: SentimentAnalysis;
  classification: DocumentClassification;
  keyPhrases: KeyPhrase[];
  qualityMetrics: QualityMetrics;
}

export interface Entity {
  type: EntityType;
  text: string;
  startPosition: number;
  endPosition: number;
  confidence: number;
  metadata?: Record<string, any>;
}

export type EntityType = 
  | 'PERSON' 
  | 'ORGANIZATION' 
  | 'LOCATION' 
  | 'DATE' 
  | 'MONEY' 
  | 'QUANTITY' 
  | 'EMAIL' 
  | 'PHONE' 
  | 'CUSTOM';

export interface SentimentAnalysis {
  overall: {
    score: number; // -1 to 1
    label: 'positive' | 'negative' | 'neutral';
    confidence: number;
  };
  sentences: Array<{
    sentenceId: number;
    score: number;
    emotions: string[];
  }>;
}

export interface DocumentClassification {
  documentType: string;
  topics: string[];
  confidence: number;
  alternativeCategories: Array<{
    category: string;
    confidence: number;
  }>;
}

export interface KeyPhrase {
  text: string;
  score: number;
  beginOffset: number;
  endOffset: number;
}

export interface QualityMetrics {
  overallScore: number;
  extractionAccuracy: number;
  completeness: number;
  consistency: number;
  issues: QualityIssue[];
}

export interface QualityIssue {
  type: 'low_confidence' | 'missing_data' | 'inconsistent_format' | 'encoding_error';
  description: string;
  severity: 'low' | 'medium' | 'high';
  affectedText?: string;
}

export interface Dataset {
  id: string;
  userId: string;
  name: string;
  documentIds: string[];
  format: DatasetFormat;
  size: number; // in bytes
  recordCount: number;
  createdDate: string;
  qualityMetrics: DatasetQualityMetrics;
  downloadCount: number;
}

export type DatasetFormat = 'json' | 'csv' | 'parquet' | 'huggingface';

export interface DatasetQualityMetrics {
  qualityScore: number;
  completeness: number;
  consistency: number;
  diversity: number;
  bias: number;
  trainingReadiness: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface DashboardMetrics {
  totalDocuments: number;
  documentsProcessedToday: number;
  averageQualityScore: number;
  successRate: number;
  totalCostThisMonth: number;
  processingTimeAverage: number;
  storageUsed: number;
  apiCallsUsed: number;
}

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'down';
  services: ServiceStatus[];
  responseTime: number;
  uptime: number;
}

export interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  responseTime: number;
  lastChecked: string;
}

export interface WebhookConfig {
  id: string;
  url: string;
  events: WebhookEvent[];
  secret: string;
  active: boolean;
  deliveryStats: {
    successful: number;
    failed: number;
    lastDelivery?: string;
  };
}

export type WebhookEvent = 
  | 'document.uploaded'
  | 'processing.started'
  | 'processing.completed'
  | 'processing.failed'
  | 'dataset.generated'
  | 'download.completed';

// Chat and AI Assistant Types
export interface ChatSession {
  id: string;
  userId: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  isActive: boolean;
  lastMessage?: ChatMessage;
  documentContext?: string[];
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachments?: AttachmentFile[];
  metadata?: {
    tokens?: number;
    model?: string;
    processingTime?: number;
  };
}

export interface AttachmentFile {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
  url?: string;
}

// Analytics Types
export interface AnalyticsQuery {
  startDate?: string;
  endDate?: string;
  granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly';
  filters?: Record<string, any>;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  metadata?: Record<string, any>;
}

export interface AnalyticsDashboard {
  kpis: {
    documents_processed: number;
    documents_processed_change?: number;
    projects_count: number;
    projects_change?: number;
    accuracy_avg: number;
    accuracy_change?: number;
    cost_saved: number;
    cost_saved_change?: number;
    avg_processing_time: number;
    processing_time_change?: number;
  };
  processing_volume: TimeSeriesData[];
  entity_distribution: Array<{ type: string; count: number; percentage: number }>;
  export_activity: Array<{ format: string; count: number }>;
  system_performance: {
    cpu_usage: number;
    memory_usage: number;
    active_connections: number;
    queue_depth: number;
  };
}

// System and Performance Types
export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    temperature?: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    inbound: number;
    outbound: number;
    connections: number;
  };
  timestamp: string;
}

export interface ConnectionStatus {
  websocket: 'connected' | 'disconnected' | 'connecting' | 'error';
  api: 'healthy' | 'degraded' | 'error';
  lastCheck: string;
}

// Mobile API Types
export interface MobileUploadRequest {
  files: FileData[];
  compressionLevel: 'low' | 'medium' | 'high';
  offlineSync: boolean;
  batchSize: number;
}

export interface FileData {
  id: string;
  name: string;
  size: number;
  type: string;
  data: ArrayBuffer | string;
  thumbnailData?: string;
}

export interface OfflineQueue {
  id: string;
  type: 'upload' | 'processing' | 'download';
  data: any;
  timestamp: string;
  retryCount: number;
  status: 'pending' | 'syncing' | 'completed' | 'failed';
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id?: string;
}

export interface ProcessingUpdate {
  jobId: string;
  status: ProcessingJob['status'];
  progress: number;
  stage: ProcessingStage['current'];
  estimatedCompletion?: string;
  errorMessage?: string;
}

export interface ChatMessageUpdate {
  sessionId: string;
  message: ChatMessage;
  typing?: boolean;
}

export interface NotificationData {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

// Auth Types
export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  name: string;
  company?: string;
  acceptTerms: boolean;
}

export interface PasswordReset {
  email: string;
  token?: string;
  newPassword?: string;
}

// AWS Integration Types
export interface CognitoUser {
  sub: string;
  email: string;
  email_verified: boolean;
  name: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
  groups?: string[];
}

export interface S3UploadParams {
  bucket: string;
  key: string;
  file: File;
  contentType: string;
  metadata?: Record<string, string>;
  onProgress?: (progress: number) => void;
}

export interface CloudWatchMetric {
  MetricName: string;
  Namespace: string;
  Value: number;
  Unit: string;
  Timestamp: Date;
  Dimensions?: Array<{
    Name: string;
    Value: string;
  }>;
}

// Form and UI Types
export interface FormField {
  name: string;
  type: 'text' | 'email' | 'password' | 'select' | 'checkbox' | 'textarea' | 'file';
  label: string;
  placeholder?: string;
  required?: boolean;
  validation?: any;
  options?: Array<{ label: string; value: string }>;
}

export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  width?: string;
}

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area';
  data: ChartDataPoint[];
  options?: any;
  colors?: string[];
}

// Settings and Configuration Types
export interface UserSettings {
  notifications: {
    email: boolean;
    push: boolean;
    processing: boolean;
    marketing: boolean;
  };
  privacy: {
    shareAnalytics: boolean;
    allowCookies: boolean;
    dataRetention: number;
  };
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    dateFormat: string;
  };
  integrations: {
    webhooks: WebhookConfig[];
    apiKeys: Array<{
      id: string;
      name: string;
      key: string;
      createdAt: string;
      lastUsed?: string;
    }>;
  };
}

export interface BillingInfo {
  subscriptionTier: string;
  billingCycle: 'monthly' | 'yearly';
  nextBillingDate: string;
  paymentMethod: {
    type: 'card' | 'paypal';
    last4?: string;
    brand?: string;
    expiryMonth?: number;
    expiryYear?: number;
  };
  billingHistory: Array<{
    id: string;
    amount: number;
    currency: string;
    date: string;
    status: 'paid' | 'pending' | 'failed';
    description: string;
  }>;
}

// Error Types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Component Props Types
export interface ComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingSpinnerProps extends ComponentProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export interface ProgressBarProps extends ComponentProps {
  progress: number;
  showLabel?: boolean;
  color?: string;
  height?: number;
}

export interface ButtonProps extends ComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface InputProps extends ComponentProps {
  type?: string;
  value?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  label?: string;
  required?: boolean;
  onChange?: (value: string) => void;
}

export interface ModalProps extends ComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closeOnBackdrop?: boolean;
}

export interface BadgeProps extends ComponentProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
}

// Store Types for State Management
export interface AppStore {
  // Auth
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // UI State
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  connectionStatus: ConnectionStatus;
  notifications: NotificationData[];
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshAuthToken: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  toggleSidebar: () => void;
  addNotification: (notification: Omit<NotificationData, 'id' | 'timestamp'>) => void;
  markNotificationRead: (id: string) => void;
  updateConnectionStatus: (status: Partial<ConnectionStatus>) => void;
}

export interface RealTimeStore {
  // Processing Jobs
  processingJobs: ProcessingJob[];
  activeJobs: ProcessingJob[];
  
  // Chat Sessions
  chatSessions: ChatSession[];
  activeChatSession: ChatSession | null;
  chatMessages: Record<string, ChatMessage[]>;
  
  // WebSocket
  connected: boolean;
  reconnectAttempts: number;
  
  // Actions
  updateProcessingJob: (jobId: string, update: Partial<ProcessingJob>) => void;
  addChatMessage: (sessionId: string, message: ChatMessage) => void;
  setActiveChatSession: (session: ChatSession | null) => void;
  updateConnectionStatus: (connected: boolean) => void;
  subscribeToJob: (jobId: string) => void;
  subscribeToChatSession: (sessionId: string) => void;
}

// Utility Types
export type Nullable<T> = T | null;
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Route Types
export type RouteParams = Record<string, string>;
export type QueryParams = Record<string, string | string[] | undefined>;

export interface RouteConfig {
  path: string;
  component: React.ComponentType<any>;
  exact?: boolean;
  protected?: boolean;
  roles?: string[];
  title?: string;
}

// Environment Configuration
export interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retries: number;
  };
  aws: {
    region: string;
    userPoolId: string;
    userPoolClientId: string;
    identityPoolId: string;
    s3Bucket: string;
  };
  features: {
    realTimeUpdates: boolean;
    offlineSupport: boolean;
    analytics: boolean;
    chat: boolean;
  };
  limits: {
    maxFileSize: number;
    maxFiles: number;
    requestTimeout: number;
  };
}