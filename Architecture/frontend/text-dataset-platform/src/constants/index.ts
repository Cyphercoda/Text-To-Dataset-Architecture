// Application constants based on workflow documentation

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.textdataset.com/v1';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  DOCUMENTS: '/documents',
  ANALYSIS: '/analysis',
  DATASETS: '/datasets',
  SETTINGS: '/settings',
  SUPPORT: '/support'
} as const;

export const PROCESSING_STAGES = {
  VALIDATION: 'validation',
  EXTRACTION: 'extraction',
  NLP: 'nlp',
  DATASET_GENERATION: 'dataset_generation',
  COMPLETED: 'completed'
} as const;

export const DOCUMENT_STATUS = {
  UPLOADING: 'uploading',
  VALIDATING: 'validating',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

export const USER_ROLES = {
  FREE: 'free',
  BASIC: 'basic',
  PRO: 'pro',
  ENTERPRISE: 'enterprise'
} as const;

export const ENTITY_TYPES = {
  PERSON: 'PERSON',
  ORGANIZATION: 'ORGANIZATION',
  LOCATION: 'LOCATION',
  DATE: 'DATE',
  MONEY: 'MONEY',
  QUANTITY: 'QUANTITY',
  EMAIL: 'EMAIL',
  PHONE: 'PHONE',
  CUSTOM: 'CUSTOM'
} as const;

export const DATASET_FORMATS = {
  JSON: 'json',
  CSV: 'csv',
  PARQUET: 'parquet',
  HUGGINGFACE: 'huggingface'
} as const;

export const SUPPORTED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/rtf',
  'text/html',
  'text/markdown',
  'message/rfc822'
] as const;

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const USAGE_LIMITS = {
  [USER_ROLES.FREE]: {
    apiCallsPerDay: 1000,
    uploadVolumePerDay: 100, // MB
    documentsPerDay: 50,
    concurrentUploads: 2
  },
  [USER_ROLES.BASIC]: {
    apiCallsPerDay: 10000,
    uploadVolumePerDay: 1000, // MB
    documentsPerDay: 500,
    concurrentUploads: 5
  },
  [USER_ROLES.PRO]: {
    apiCallsPerDay: 100000,
    uploadVolumePerDay: 10000, // MB
    documentsPerDay: 5000,
    concurrentUploads: 20
  },
  [USER_ROLES.ENTERPRISE]: {
    apiCallsPerDay: -1, // Unlimited
    uploadVolumePerDay: -1, // Unlimited
    documentsPerDay: -1, // Unlimited
    concurrentUploads: -1 // Unlimited
  }
} as const;

export const QUALITY_THRESHOLDS = {
  EXCELLENT: 90,
  GOOD: 75,
  FAIR: 60,
  POOR: 40
} as const;

export const REFRESH_INTERVALS = {
  DASHBOARD_METRICS: 30000, // 30 seconds
  PROCESSING_STATUS: 5000, // 5 seconds
  SYSTEM_HEALTH: 60000, // 1 minute
  USER_ACTIVITY: 10000 // 10 seconds
} as const;

export const CHART_COLORS = {
  PRIMARY: '#1976d2',
  SECONDARY: '#dc004e',
  SUCCESS: '#2e7d32',
  WARNING: '#ed6c02',
  ERROR: '#d32f2f',
  INFO: '#0288d1',
  QUALITY_EXCELLENT: '#4caf50',
  QUALITY_GOOD: '#8bc34a',
  QUALITY_FAIR: '#ff9800',
  QUALITY_POOR: '#f44336'
} as const;

export const SENTIMENT_LABELS = {
  POSITIVE: 'positive',
  NEGATIVE: 'negative',
  NEUTRAL: 'neutral'
} as const;

export const WEBHOOK_EVENTS = [
  'document.uploaded',
  'processing.started',
  'processing.completed',
  'processing.failed',
  'dataset.generated',
  'download.completed'
] as const;