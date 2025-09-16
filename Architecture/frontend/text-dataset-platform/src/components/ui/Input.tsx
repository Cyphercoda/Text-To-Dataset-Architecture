/**
 * Input Component
 * Reusable input field with validation states and icons
 */

import React, { forwardRef } from 'react';
import clsx from 'clsx';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  hint,
  leftIcon,
  rightIcon,
  size = 'md',
  fullWidth = false,
  className,
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const baseInputClasses = 'block border rounded-md shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-gray-50 disabled:text-gray-500';

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  const stateClasses = error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';

  const iconClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const paddingWithIcon = {
    sm: leftIcon ? 'pl-8' : rightIcon ? 'pr-8' : '',
    md: leftIcon ? 'pl-10' : rightIcon ? 'pr-10' : '',
    lg: leftIcon ? 'pl-12' : rightIcon ? 'pr-12' : '',
  };

  return (
    <div className={clsx('relative', { 'w-full': fullWidth }, className)}>
      {label && (
        <label 
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className={clsx(
            'absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400',
            iconClasses[size]
          )}>
            {leftIcon}
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            baseInputClasses,
            sizeClasses[size],
            stateClasses,
            paddingWithIcon[size],
            {
              'w-full': fullWidth,
            }
          )}
          {...props}
        />
        
        {rightIcon && (
          <div className={clsx(
            'absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400',
            iconClasses[size]
          )}>
            {rightIcon}
          </div>
        )}
      </div>
      
      {hint && !error && (
        <p className="mt-1 text-xs text-gray-500">{hint}</p>
      )}
      
      {error && (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;