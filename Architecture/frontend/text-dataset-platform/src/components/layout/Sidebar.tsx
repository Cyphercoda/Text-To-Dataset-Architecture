/**
 * Sidebar Navigation Component
 * Collapsible sidebar with navigation links and quick actions
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import clsx from 'clsx';

// Components
import Badge from '../ui/Badge';

// Stores
import { useProcessingStore } from '../../stores/realTimeStore';

// Icons
import {
  HomeIcon,
  DocumentTextIcon,
  CloudArrowUpIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  FolderIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onCloseMobile: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  badgeVariant?: 'default' | 'success' | 'warning' | 'error' | 'info';
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle, onCloseMobile }) => {
  const location = useLocation();
  const { jobs } = useProcessingStore();

  // Calculate active jobs count for badge
  const activeJobsCount = jobs.filter(job => 
    ['pending', 'processing'].includes(job.status)
  ).length;

  const navigation: NavItem[] = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
    },
    {
      name: 'Upload',
      href: '/upload',
      icon: CloudArrowUpIcon,
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: DocumentTextIcon,
      badge: activeJobsCount > 0 ? activeJobsCount : undefined,
      badgeVariant: 'info',
    },
    {
      name: 'Chat Assistant',
      href: '/chat',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
    },
    {
      name: 'Projects',
      href: '/projects',
      icon: FolderIcon,
    },
  ];

  const secondaryNavigation: NavItem[] = [
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
    },
    {
      name: 'Help & Support',
      href: '/help',
      icon: QuestionMarkCircleIcon,
    },
  ];

  const NavItem = ({ item }: { item: NavItem }) => {
    const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
    
    return (
      <NavLink
        to={item.href}
        onClick={onCloseMobile}
        className={clsx(
          'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
          {
            'bg-blue-100 text-blue-900': isActive,
            'text-gray-700 hover:bg-gray-100 hover:text-gray-900': !isActive,
          }
        )}
        title={collapsed ? item.name : undefined}
      >
        <item.icon
          className={clsx(
            'flex-shrink-0 h-5 w-5',
            {
              'text-blue-500': isActive,
              'text-gray-400 group-hover:text-gray-500': !isActive,
            },
            collapsed ? 'mr-0' : 'mr-3'
          )}
        />
        
        {!collapsed && (
          <>
            <span className="flex-1">{item.name}</span>
            {item.badge && (
              <Badge 
                variant={item.badgeVariant || 'default'} 
                size="sm"
              >
                {item.badge}
              </Badge>
            )}
          </>
        )}
      </NavLink>
    );
  };

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">TD</span>
              </div>
              <h1 className="text-lg font-semibold text-gray-900">
                Text-to-Dataset
              </h1>
            </div>
          )}
          
          {/* Mobile close button */}
          <button
            onClick={onCloseMobile}
            className="p-1 text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
          
          {/* Desktop collapse button */}
          <button
            onClick={onToggle}
            className="hidden lg:block p-1 text-gray-500 hover:text-gray-700 transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRightIcon className="h-5 w-5" />
            ) : (
              <ChevronLeftIcon className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-8 overflow-y-auto">
        {/* Main navigation */}
        <div className="space-y-1">
          {!collapsed && (
            <h3 className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Main
            </h3>
          )}
          <div className="space-y-1 mt-2">
            {navigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </div>
        </div>

        {/* Secondary navigation */}
        <div className="space-y-1">
          {!collapsed && (
            <h3 className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Support
            </h3>
          )}
          <div className="space-y-1 mt-2">
            {secondaryNavigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </div>
        </div>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-200">
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <QuestionMarkCircleIcon className="h-5 w-5 text-blue-400" />
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-xs font-medium text-blue-900">
                  Need help?
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  Check our documentation or contact support.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;