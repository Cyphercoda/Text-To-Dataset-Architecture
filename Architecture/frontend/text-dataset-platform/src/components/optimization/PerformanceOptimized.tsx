/**
 * Performance Optimization Components and Utilities
 * Collection of optimized components for better rendering performance
 */

import React, { memo, useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { debounce, throttle } from 'lodash-es';

// Memoized Card Component
export interface CardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  loading?: boolean;
  onClick?: () => void;
}

export const OptimizedCard = memo<CardProps>(({
  title,
  children,
  className = '',
  loading = false,
  onClick
}) => {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 animate-pulse ${className}`}>
        <div className="h-4 bg-gray-300 rounded mb-4 w-3/4"></div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-300 rounded"></div>
          <div className="h-3 bg-gray-300 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`bg-white rounded-lg shadow p-6 transition-shadow duration-200 hover:shadow-lg ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={onClick}
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  );
});

// Optimized Image Component with Lazy Loading
export interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
  fallback?: string;
  loading?: 'lazy' | 'eager';
  onLoad?: () => void;
  onError?: () => void;
}

export const OptimizedImage = memo<OptimizedImageProps>(({
  src,
  alt,
  className = '',
  placeholder,
  fallback,
  loading = 'lazy',
  onLoad,
  onError
}) => {
  const [imageSrc, setImageSrc] = useState(placeholder || src);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isLoaded && !hasError) {
          setImageSrc(src);
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(img);
    return () => observer.disconnect();
  }, [src, isLoaded, hasError]);

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleError = useCallback(() => {
    setHasError(true);
    if (fallback) {
      setImageSrc(fallback);
    }
    onError?.();
  }, [fallback, onError]);

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={`transition-opacity duration-300 ${
        isLoaded ? 'opacity-100' : 'opacity-50'
      } ${className}`}
      loading={loading}
      onLoad={handleLoad}
      onError={handleError}
    />
  );
});

// Debounced Search Input Component
export interface DebouncedSearchProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
  className?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export const DebouncedSearch = memo<DebouncedSearchProps>(({
  onSearch,
  placeholder = 'Search...',
  debounceMs = 300,
  className = '',
  value = '',
  onChange
}) => {
  const [inputValue, setInputValue] = useState(value);

  const debouncedSearch = useMemo(
    () => debounce((query: string) => {
      onSearch(query);
    }, debounceMs),
    [onSearch, debounceMs]
  );

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    onChange?.(newValue);
    debouncedSearch(newValue);
  }, [onChange, debouncedSearch]);

  useEffect(() => {
    return () => {
      debouncedSearch.cancel();
    };
  }, [debouncedSearch]);

  return (
    <div className="relative">
      <input
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        placeholder={placeholder}
        className={`w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${className}`}
      />
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>
  );
});

// Infinite Scroll Component
export interface InfiniteScrollProps {
  children: React.ReactNode;
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  threshold?: number;
  loader?: React.ReactNode;
}

export const InfiniteScroll = memo<InfiniteScrollProps>(({
  children,
  hasMore,
  loading,
  onLoadMore,
  threshold = 200,
  loader
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const throttledLoadMore = useMemo(
    () => throttle(async () => {
      if (!loading && !isLoadingMore && hasMore) {
        setIsLoadingMore(true);
        try {
          await onLoadMore();
        } finally {
          setIsLoadingMore(false);
        }
      }
    }, 200),
    [loading, isLoadingMore, hasMore, onLoadMore]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      if (scrollHeight - scrollTop - clientHeight < threshold) {
        throttledLoadMore();
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => {
      container.removeEventListener('scroll', handleScroll);
      throttledLoadMore.cancel();
    };
  }, [throttledLoadMore, threshold]);

  return (
    <div ref={containerRef} className="h-full overflow-y-auto">
      {children}
      {(loading || isLoadingMore) && (
        <div className="flex justify-center items-center py-4">
          {loader || (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-sm text-gray-600">Loading more...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

// Memoized List Item Component
export interface ListItemProps {
  id: string;
  title: string;
  subtitle?: string;
  avatar?: string;
  actions?: React.ReactNode;
  onClick?: (id: string) => void;
  selected?: boolean;
}

export const OptimizedListItem = memo<ListItemProps>(({
  id,
  title,
  subtitle,
  avatar,
  actions,
  onClick,
  selected = false
}) => {
  const handleClick = useCallback(() => {
    onClick?.(id);
  }, [onClick, id]);

  return (
    <div
      className={`flex items-center px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors duration-150 ${
        selected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
      }`}
      onClick={handleClick}
    >
      {avatar && (
        <OptimizedImage
          src={avatar}
          alt={title}
          className="h-10 w-10 rounded-full mr-3"
          fallback="/default-avatar.png"
        />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{title}</p>
        {subtitle && (
          <p className="text-sm text-gray-500 truncate">{subtitle}</p>
        )}
      </div>
      {actions && <div className="ml-4 flex-shrink-0">{actions}</div>}
    </div>
  );
});

// Code Splitting Helper Component
export const LazyComponent = ({
  fallback = <div>Loading...</div>,
  component: Component,
  ...props
}: {
  fallback?: React.ReactNode;
  component: React.LazyExoticComponent<React.ComponentType<any>>;
  [key: string]: any;
}) => (
  <React.Suspense fallback={fallback}>
    <Component {...props} />
  </React.Suspense>
);

// Performance monitoring hook
export const usePerformanceMonitoring = (componentName: string) => {
  const renderStartTime = useRef<number>();
  const renderCount = useRef(0);

  useEffect(() => {
    renderStartTime.current = performance.now();
    renderCount.current += 1;

    return () => {
      if (renderStartTime.current) {
        const renderTime = performance.now() - renderStartTime.current;
        
        // Log performance metrics in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[Performance] ${componentName}:`, {
            renderTime: `${renderTime.toFixed(2)}ms`,
            renderCount: renderCount.current,
            timestamp: new Date().toISOString()
          });
        }

        // Send to analytics in production
        if (process.env.NODE_ENV === 'production' && renderTime > 16) {
          // Report slow renders (>16ms = 60fps threshold)
          window.gtag?.('event', 'slow_render', {
            component_name: componentName,
            render_time: Math.round(renderTime),
            render_count: renderCount.current
          });
        }
      }
    };
  });

  return {
    renderCount: renderCount.current
  };
};

// Bundle size monitoring
export const measureBundleImpact = (moduleName: string) => {
  const startTime = performance.now();
  
  return () => {
    const loadTime = performance.now() - startTime;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Bundle] ${moduleName} loaded in ${loadTime.toFixed(2)}ms`);
    }
  };
};

// Memory leak detection hook
export const useMemoryLeakDetection = (componentName: string) => {
  useEffect(() => {
    const checkMemory = () => {
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        const memoryUsage = {
          used: Math.round(memInfo.usedJSHeapSize / 1048576), // MB
          total: Math.round(memInfo.totalJSHeapSize / 1048576), // MB
          limit: Math.round(memInfo.jsHeapSizeLimit / 1048576) // MB
        };

        // Warn if memory usage is high
        if (memoryUsage.used > 100) {
          console.warn(`[Memory] High usage in ${componentName}:`, memoryUsage);
        }
      }
    };

    const interval = setInterval(checkMemory, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [componentName]);
};