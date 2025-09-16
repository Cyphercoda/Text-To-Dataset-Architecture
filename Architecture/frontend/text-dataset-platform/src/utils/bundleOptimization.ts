/**
 * Bundle Optimization Utilities
 * Tools and configurations for optimizing bundle size and performance
 */

// Dynamic imports for code splitting
export const loadComponent = async <T>(
  componentImport: () => Promise<{ default: T }>,
  retries: number = 3
): Promise<T> => {
  let lastError: Error;

  for (let i = 0; i < retries; i++) {
    try {
      const module = await componentImport();
      return module.default;
    } catch (error) {
      lastError = error as Error;
      
      // Wait before retrying
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
  }

  throw lastError!;
};

// Preload components for better UX
export const preloadComponent = (componentImport: () => Promise<any>) => {
  // Use requestIdleCallback if available, otherwise setTimeout
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      componentImport().catch(() => {
        // Ignore preload errors
      });
    });
  } else {
    setTimeout(() => {
      componentImport().catch(() => {
        // Ignore preload errors
      });
    }, 100);
  }
};

// Bundle analyzer helper
export const analyzeBundleSize = () => {
  if (process.env.NODE_ENV === 'development') {
    const bundleSize = document.querySelectorAll('script[src]').length;
    const totalSize = Array.from(document.querySelectorAll('script[src]'))
      .reduce((total, script) => {
        const src = (script as HTMLScriptElement).src;
        return total + (src.length || 0);
      }, 0);

    console.log(`Bundle Analysis:`, {
      scriptCount: bundleSize,
      estimatedSize: `${(totalSize / 1024).toFixed(2)} KB`,
      timestamp: new Date().toISOString()
    });
  }
};

// Tree shaking helper - import only what you need
export const createSelectiveImport = <T extends Record<string, any>>(
  modulePromise: Promise<T>,
  selections: (keyof T)[]
) => {
  return modulePromise.then(module => {
    const selectedExports: Partial<T> = {};
    selections.forEach(key => {
      if (key in module) {
        selectedExports[key] = module[key];
      }
    });
    return selectedExports;
  });
};

// Webpack chunk naming for better caching
export const getChunkName = (routeName: string, feature?: string) => {
  return feature ? `${routeName}-${feature}` : routeName;
};

// Service Worker cache optimization
export const optimizeServiceWorkerCache = () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(registration => {
      // Cache critical resources
      const criticalResources = [
        '/static/js/vendor.chunk.js',
        '/static/js/main.chunk.js',
        '/static/css/main.css',
        '/manifest.json'
      ];

      registration.active?.postMessage({
        type: 'CACHE_URLS',
        urls: criticalResources
      });
    });
  }
};

// Resource hints for better loading
export const addResourceHints = () => {
  const head = document.head;

  // DNS prefetch for external domains
  const dnsPrefetchDomains = [
    'https://api.textdataset.com',
    'https://cdn.textdataset.com',
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com'
  ];

  dnsPrefetchDomains.forEach(domain => {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = domain;
    head.appendChild(link);
  });

  // Preconnect to critical origins
  const preconnectOrigins = [
    'https://api.textdataset.com',
    'https://cdn.textdataset.com'
  ];

  preconnectOrigins.forEach(origin => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = origin;
    link.crossOrigin = 'anonymous';
    head.appendChild(link);
  });
};

// Critical CSS inlining
export const inlineCriticalCSS = (criticalCSS: string) => {
  const style = document.createElement('style');
  style.textContent = criticalCSS;
  style.setAttribute('data-critical', 'true');
  document.head.appendChild(style);
};

// Image optimization utilities
export const optimizeImageLoading = () => {
  // Add loading="lazy" to images that are not in viewport
  const images = document.querySelectorAll('img:not([loading])');
  
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        img.loading = 'eager';
        imageObserver.unobserve(img);
      }
    });
  }, { rootMargin: '50px' });

  images.forEach(img => {
    (img as HTMLImageElement).loading = 'lazy';
    imageObserver.observe(img);
  });
};

// Font optimization
export const optimizeFontLoading = () => {
  // Preload critical fonts
  const criticalFonts = [
    '/fonts/Inter-Regular.woff2',
    '/fonts/Inter-Medium.woff2',
    '/fonts/Inter-SemiBold.woff2'
  ];

  criticalFonts.forEach(fontUrl => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = fontUrl;
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};

// Third-party script optimization
export const loadThirdPartyScript = async (
  src: string,
  options: {
    async?: boolean;
    defer?: boolean;
    onLoad?: () => void;
    onError?: () => void;
    timeout?: number;
  } = {}
) => {
  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = options.async ?? true;
    script.defer = options.defer ?? false;

    let timeoutId: NodeJS.Timeout | undefined;

    const cleanup = () => {
      if (timeoutId) clearTimeout(timeoutId);
      script.removeEventListener('load', onLoad);
      script.removeEventListener('error', onError);
    };

    const onLoad = () => {
      cleanup();
      options.onLoad?.();
      resolve();
    };

    const onError = () => {
      cleanup();
      options.onError?.();
      reject(new Error(`Failed to load script: ${src}`));
    };

    script.addEventListener('load', onLoad);
    script.addEventListener('error', onError);

    if (options.timeout) {
      timeoutId = setTimeout(() => {
        cleanup();
        reject(new Error(`Script load timeout: ${src}`));
      }, options.timeout);
    }

    document.head.appendChild(script);
  });
};

// Performance budget monitoring
export const monitorPerformanceBudget = () => {
  if ('PerformanceObserver' in window) {
    // Monitor resource loading
    const resourceObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        const resourceEntry = entry as PerformanceResourceTiming;
        
        // Check for large resources
        if (resourceEntry.transferSize > 1024 * 1024) { // > 1MB
          console.warn(`Large resource detected: ${resourceEntry.name} (${Math.round(resourceEntry.transferSize / 1024)} KB)`);
        }

        // Check for slow loading resources
        if (resourceEntry.duration > 3000) { // > 3s
          console.warn(`Slow resource: ${resourceEntry.name} (${Math.round(resourceEntry.duration)}ms)`);
        }
      });
    });

    resourceObserver.observe({ entryTypes: ['resource'] });

    // Monitor navigation timing
    const navigationObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        const navEntry = entry as PerformanceNavigationTiming;
        
        const metrics = {
          domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
          loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
          firstPaint: 0,
          firstContentfulPaint: 0
        };

        // Get paint metrics
        performance.getEntriesByType('paint').forEach((paintEntry: any) => {
          if (paintEntry.name === 'first-paint') {
            metrics.firstPaint = paintEntry.startTime;
          } else if (paintEntry.name === 'first-contentful-paint') {
            metrics.firstContentfulPaint = paintEntry.startTime;
          }
        });

        // Log performance metrics
        console.log('Performance Metrics:', metrics);

        // Send to analytics if needed
        if (window.gtag) {
          window.gtag('event', 'performance_timing', {
            dom_content_loaded: Math.round(metrics.domContentLoaded),
            load_complete: Math.round(metrics.loadComplete),
            first_paint: Math.round(metrics.firstPaint),
            first_contentful_paint: Math.round(metrics.firstContentfulPaint)
          });
        }
      });
    });

    navigationObserver.observe({ entryTypes: ['navigation'] });
  }
};

// Initialize all optimizations
export const initializeBundleOptimizations = () => {
  // Run on DOM content loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      addResourceHints();
      optimizeFontLoading();
      optimizeImageLoading();
      optimizeServiceWorkerCache();
      monitorPerformanceBudget();
    });
  } else {
    addResourceHints();
    optimizeFontLoading();
    optimizeImageLoading();
    optimizeServiceWorkerCache();
    monitorPerformanceBudget();
  }

  // Run on window load
  if (document.readyState === 'complete') {
    analyzeBundleSize();
  } else {
    window.addEventListener('load', analyzeBundleSize);
  }
};

// Export lazy loading components
export const LazyComponents = {
  Dashboard: React.lazy(() => loadComponent(() => import('../pages/Dashboard/DashboardPage'))),
  Upload: React.lazy(() => loadComponent(() => import('../pages/Upload/UploadPage'))),
  Chat: React.lazy(() => loadComponent(() => import('../pages/Chat/ChatPage'))),
  Analytics: React.lazy(() => loadComponent(() => import('../pages/Analytics/AnalyticsPage'))),
  Settings: React.lazy(() => loadComponent(() => import('../pages/Settings/SettingsPage'))),
  
  // Preload components for better UX
  preloadDashboard: () => preloadComponent(() => import('../pages/Dashboard/DashboardPage')),
  preloadUpload: () => preloadComponent(() => import('../pages/Upload/UploadPage')),
  preloadChat: () => preloadComponent(() => import('../pages/Chat/ChatPage')),
  preloadAnalytics: () => preloadComponent(() => import('../pages/Analytics/AnalyticsPage')),
  preloadSettings: () => preloadComponent(() => import('../pages/Settings/SettingsPage')),
};