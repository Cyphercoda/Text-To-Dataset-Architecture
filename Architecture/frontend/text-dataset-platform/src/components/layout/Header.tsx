/**
 * Header Component
 * Top navigation bar with user menu, notifications, and controls
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import clsx from 'clsx';

// Components
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';

// Stores and Services
import { useAppStore } from '../../stores/appStore';
import { useNotificationStore, useConnectionStore } from '../../stores/realTimeStore';

// Icons
import {
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
  MoonIcon,
  SunIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

interface HeaderProps {
  onMenuClick: () => void;
  sidebarCollapsed: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, sidebarCollapsed }) => {
  const navigate = useNavigate();
  const { user, logout, theme, toggleTheme } = useAppStore();
  const { notifications, unreadCount, markAllAsRead } = useNotificationStore();
  const { isWebSocketConnected } = useConnectionStore();
  
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  
  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/auth/login');
  };

  const recentNotifications = notifications.slice(0, 5);

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="p-2 text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          {/* Logo and title */}
          <div className="flex items-center ml-2 lg:ml-0">
            <Link to="/dashboard" className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">TD</span>
              </div>
              {!sidebarCollapsed && (
                <h1 className="text-xl font-semibold text-gray-900 hidden lg:block">
                  Text-to-Dataset
                </h1>
              )}
            </Link>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Connection status */}
          <div className="hidden md:flex items-center">
            <div
              className={clsx('w-2 h-2 rounded-full mr-2', {
                'bg-green-500': isWebSocketConnected,
                'bg-red-500': !isWebSocketConnected,
              })}
            />
            <span className="text-xs text-gray-600">
              {isWebSocketConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <SunIcon className="h-5 w-5" />
            ) : (
              <MoonIcon className="h-5 w-5" />
            )}
          </button>

          {/* Notifications */}
          <div className="relative" ref={notificationsRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <BellIcon className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* Notifications dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900">
                      Notifications
                    </h3>
                    {unreadCount > 0 && (
                      <button
                        onClick={markAllAsRead}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>
                </div>

                <div className="max-h-64 overflow-y-auto">
                  {recentNotifications.length > 0 ? (
                    recentNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={clsx(
                          'p-4 border-b border-gray-100 last:border-0',
                          {
                            'bg-blue-50': !notification.read,
                          }
                        )}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                              {new Date(notification.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <Badge variant={notification.type} size="sm">
                            {notification.type}
                          </Badge>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-8 text-center text-gray-500">
                      <BellIcon className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No notifications yet</p>
                    </div>
                  )}
                </div>

                {notifications.length > 5 && (
                  <div className="p-4 border-t border-gray-200">
                    <button
                      onClick={() => navigate('/notifications')}
                      className="w-full text-center text-sm text-blue-600 hover:text-blue-700"
                    >
                      View all notifications
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center p-1 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <div className="flex items-center">
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name}
                    className="h-8 w-8 rounded-full"
                  />
                ) : (
                  <UserCircleIcon className="h-8 w-8" />
                )}
                <span className="ml-2 text-sm font-medium text-gray-700 hidden md:block">
                  {user?.name || 'User'}
                </span>
                <ChevronDownIcon className="ml-1 h-4 w-4 hidden md:block" />
              </div>
            </button>

            {/* User dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center">
                    {user?.avatar ? (
                      <img
                        src={user.avatar}
                        alt={user.name}
                        className="h-10 w-10 rounded-full"
                      />
                    ) : (
                      <UserCircleIcon className="h-10 w-10 text-gray-400" />
                    )}
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.name || 'User'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {user?.email}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="py-2">
                  <Link
                    to="/settings/profile"
                    onClick={() => setShowUserMenu(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <UserCircleIcon className="h-4 w-4 mr-3" />
                    Profile Settings
                  </Link>
                  
                  <Link
                    to="/settings/account"
                    onClick={() => setShowUserMenu(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Cog6ToothIcon className="h-4 w-4 mr-3" />
                    Account Settings
                  </Link>

                  <div className="border-t border-gray-200 my-2" />

                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <ArrowRightOnRectangleIcon className="h-4 w-4 mr-3" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;