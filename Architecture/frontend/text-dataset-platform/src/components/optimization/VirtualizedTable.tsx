/**
 * High-Performance Virtualized Table Component
 * Optimized for handling large datasets with minimal memory footprint
 */

import React, { useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { areEqual } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

export interface Column<T> {
  key: keyof T;
  header: string;
  width: number;
  render?: (value: any, item: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  align?: 'left' | 'center' | 'right';
}

export interface VirtualizedTableProps<T> {
  data: T[];
  columns: Column<T>[];
  height?: number;
  rowHeight?: number;
  onRowClick?: (item: T, index: number) => void;
  onSort?: (column: keyof T, direction: 'asc' | 'desc') => void;
  sortColumn?: keyof T;
  sortDirection?: 'asc' | 'desc';
  loading?: boolean;
  loadingRows?: number;
  onLoadMore?: () => void;
  hasNextPage?: boolean;
  className?: string;
  stickyHeader?: boolean;
}

interface RowProps<T> {
  index: number;
  style: React.CSSProperties;
  data: {
    items: T[];
    columns: Column<T>[];
    onRowClick?: (item: T, index: number) => void;
  };
}

// Memoized Row Component for Performance
const Row = React.memo(<T,>({ index, style, data }: RowProps<T>) => {
  const { items, columns, onRowClick } = data;
  const item = items[index];

  const handleClick = useCallback(() => {
    if (onRowClick && item) {
      onRowClick(item, index);
    }
  }, [onRowClick, item, index]);

  if (!item) {
    // Loading skeleton row
    return (
      <div 
        style={style} 
        className="flex items-center border-b border-gray-200 animate-pulse"
      >
        {columns.map((column, colIndex) => (
          <div
            key={colIndex}
            style={{ width: column.width }}
            className="px-4 py-3"
          >
            <div className="h-4 bg-gray-300 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      style={style}
      className="flex items-center border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors duration-150"
      onClick={handleClick}
      role="row"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {columns.map((column) => {
        const value = item[column.key];
        const cellContent = column.render
          ? column.render(value, item, index)
          : String(value || '');

        return (
          <div
            key={String(column.key)}
            style={{ width: column.width }}
            className={`px-4 py-3 text-sm text-gray-900 ${
              column.align === 'center'
                ? 'text-center'
                : column.align === 'right'
                ? 'text-right'
                : 'text-left'
            }`}
          >
            {cellContent}
          </div>
        );
      })}
    </div>
  );
}, areEqual);

// Header Component with Sorting
const TableHeader = React.memo(<T,>({
  columns,
  onSort,
  sortColumn,
  sortDirection,
}: {
  columns: Column<T>[];
  onSort?: (column: keyof T, direction: 'asc' | 'desc') => void;
  sortColumn?: keyof T;
  sortDirection?: 'asc' | 'desc';
}) => {
  const handleSort = useCallback((column: keyof T) => {
    if (!onSort || !column) return;

    const newDirection = 
      sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc';
    onSort(column, newDirection);
  }, [onSort, sortColumn, sortDirection]);

  return (
    <div className="flex bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
      {columns.map((column) => (
        <div
          key={String(column.key)}
          style={{ width: column.width }}
          className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
            column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
          } ${
            column.align === 'center'
              ? 'text-center'
              : column.align === 'right'
              ? 'text-right'
              : 'text-left'
          }`}
          onClick={() => column.sortable && handleSort(column.key)}
        >
          <div className="flex items-center justify-between">
            <span>{column.header}</span>
            {column.sortable && sortColumn === column.key && (
              <span className="ml-1">
                {sortDirection === 'asc' ? '↑' : '↓'}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
});

// Main VirtualizedTable Component
export const VirtualizedTable = <T,>({
  data,
  columns,
  height = 400,
  rowHeight = 48,
  onRowClick,
  onSort,
  sortColumn,
  sortDirection,
  loading = false,
  loadingRows = 10,
  onLoadMore,
  hasNextPage = false,
  className = '',
  stickyHeader = true,
}: VirtualizedTableProps<T>) => {
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const listRef = useRef<List>(null);

  // Memoize the data for the virtualized list
  const listData = useMemo(() => ({
    items: loading ? Array(loadingRows).fill(null) : data,
    columns,
    onRowClick,
  }), [data, columns, onRowClick, loading, loadingRows]);

  // Handle infinite scrolling
  const handleItemsRendered = useCallback(
    async ({ visibleStopIndex }: { visibleStopIndex: number }) => {
      if (
        !loading &&
        !isLoadingMore &&
        hasNextPage &&
        onLoadMore &&
        visibleStopIndex >= data.length - 5 // Load more when 5 items from the end
      ) {
        setIsLoadingMore(true);
        try {
          await onLoadMore();
        } finally {
          setIsLoadingMore(false);
        }
      }
    },
    [loading, isLoadingMore, hasNextPage, onLoadMore, data.length]
  );

  // Calculate total table width
  const totalWidth = useMemo(
    () => columns.reduce((sum, column) => sum + column.width, 0),
    [columns]
  );

  const itemCount = loading ? loadingRows : data.length;

  return (
    <div className={`border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {stickyHeader && (
        <TableHeader
          columns={columns}
          onSort={onSort}
          sortColumn={sortColumn}
          sortDirection={sortDirection}
        />
      )}
      
      <div style={{ height }}>
        <AutoSizer>
          {({ height: containerHeight, width: containerWidth }) => (
            <List
              ref={listRef}
              height={containerHeight}
              width={Math.max(containerWidth, totalWidth)}
              itemCount={itemCount}
              itemSize={rowHeight}
              itemData={listData}
              onItemsRendered={handleItemsRendered}
              overscanCount={5} // Render 5 extra items for smooth scrolling
            >
              {Row}
            </List>
          )}
        </AutoSizer>
      </div>

      {/* Loading indicator for infinite scroll */}
      {isLoadingMore && (
        <div className="flex justify-center items-center py-4 border-t border-gray-200">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600">Loading more...</span>
        </div>
      )}
    </div>
  );
};

// Hook for managing table state
export const useVirtualizedTable = <T,>(initialData: T[] = []) => {
  const [data, setData] = useState<T[]>(initialData);
  const [sortColumn, setSortColumn] = useState<keyof T | undefined>();
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [loading, setLoading] = useState(false);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [page, setPage] = useState(1);

  const handleSort = useCallback((column: keyof T, direction: 'asc' | 'desc') => {
    setSortColumn(column);
    setSortDirection(direction);
    
    const sortedData = [...data].sort((a, b) => {
      const aValue = a[column];
      const bValue = b[column];
      
      if (aValue === bValue) return 0;
      
      const comparison = aValue > bValue ? 1 : -1;
      return direction === 'asc' ? comparison : -comparison;
    });
    
    setData(sortedData);
  }, [data]);

  const loadMore = useCallback(async () => {
    // This would typically call an API endpoint
    // For now, it's a placeholder
    setPage(prev => prev + 1);
  }, []);

  const resetData = useCallback((newData: T[]) => {
    setData(newData);
    setPage(1);
  }, []);

  const appendData = useCallback((newData: T[]) => {
    setData(prev => [...prev, ...newData]);
  }, []);

  return {
    data,
    setData,
    sortColumn,
    sortDirection,
    handleSort,
    loading,
    setLoading,
    hasNextPage,
    setHasNextPage,
    loadMore,
    resetData,
    appendData,
    page,
  };
};

export default VirtualizedTable;