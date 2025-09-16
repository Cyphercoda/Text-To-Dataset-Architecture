import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll, vi } from 'vitest';

// Mock environment variables
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});

Object.defineProperty(global, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
});

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: MockResizeObserver,
});

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url = '';
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  });
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
}

Object.defineProperty(window, 'WebSocket', {
  writable: true,
  configurable: true,
  value: MockWebSocket,
});

// Mock Canvas
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(() => ({
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi.fn(() => ({ data: new Array(4) })),
    putImageData: vi.fn(),
    createImageData: vi.fn(() => []),
    setTransform: vi.fn(),
    drawImage: vi.fn(),
    save: vi.fn(),
    fillText: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    translate: vi.fn(),
    scale: vi.fn(),
    rotate: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    measureText: vi.fn(() => ({ width: 0 })),
    transform: vi.fn(),
    rect: vi.fn(),
    clip: vi.fn(),
  })),
});

// Mock File and FileReader
Object.defineProperty(window, 'File', {
  writable: true,
  value: class MockFile {
    name: string;
    size: number;
    type: string;

    constructor(parts: BlobPart[], filename: string, properties?: FilePropertyBag) {
      this.name = filename;
      this.size = parts.reduce((acc, part) => acc + (typeof part === 'string' ? part.length : part.size || 0), 0);
      this.type = properties?.type || '';
    }
  },
});

Object.defineProperty(window, 'FileReader', {
  writable: true,
  value: class MockFileReader {
    result: string | ArrayBuffer | null = null;
    readyState = 0;
    onload: ((event: ProgressEvent<FileReader>) => void) | null = null;
    onerror: ((event: ProgressEvent<FileReader>) => void) | null = null;

    readAsText = vi.fn((file: File) => {
      setTimeout(() => {
        this.result = 'mock file content';
        this.readyState = 2;
        if (this.onload) {
          this.onload({ target: this } as ProgressEvent<FileReader>);
        }
      }, 10);
    });

    readAsDataURL = vi.fn((file: File) => {
      setTimeout(() => {
        this.result = 'data:text/plain;base64,bW9jayBmaWxlIGNvbnRlbnQ=';
        this.readyState = 2;
        if (this.onload) {
          this.onload({ target: this } as ProgressEvent<FileReader>);
        }
      }, 10);
    });
  },
});

// Mock crypto.randomUUID for older Node versions
Object.defineProperty(global.crypto, 'randomUUID', {
  value: () => 'mock-uuid-' + Math.random().toString(36).substr(2, 9),
});

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
});

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  value: vi.fn(() => 'mock-object-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: vi.fn(),
});

// Mock navigator
Object.defineProperty(navigator, 'userAgent', {
  value: 'Mozilla/5.0 (Test Environment)',
});

Object.defineProperty(navigator, 'onLine', {
  value: true,
});

// Mock fetch
global.fetch = vi.fn();

// Mock console methods for cleaner test output
beforeAll(() => {
  console.warn = vi.fn();
  console.error = vi.fn();
});

// Clean up after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Clean up after all tests
afterAll(() => {
  vi.restoreAllMocks();
});