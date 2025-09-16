/**
 * Button Component
 * Reusable button with multiple variants, sizes, and states
 */

import React, { forwardRef } from 'react';
import clsx from 'clsx';
import LoadingSpinner from './LoadingSpinner';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  disabled,
  ...props
}, ref) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-4 py-2 text-base',
    xl: 'px-6 py-3 text-base',
  };

  const iconSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
    xl: 'h-5 w-5',
  };

  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        {
          'w-full': fullWidth,
        },
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <LoadingSpinner
          size={size === 'sm' ? 'sm' : 'md'}
          color={variant === 'outline' || variant === 'ghost' ? 'gray' : 'white'}
          className="mr-2"
        />
      )}
      
      {!loading && leftIcon && (
        <span className={clsx('mr-2', iconSizeClasses[size])}>
          {leftIcon}
        </span>
      )}
      
      <span>{children}</span>
      
      {!loading && rightIcon && (
        <span className={clsx('ml-2', iconSizeClasses[size])}>
          {rightIcon}
        </span>
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;