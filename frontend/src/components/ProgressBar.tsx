/**
 * ProgressBar Component
 * Display progress for long-running operations
 */

import { HTMLAttributes } from 'react';

export interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  variant?: 'primary' | 'secondary' | 'success';
  size?: 'sm' | 'md' | 'lg';
}

export function ProgressBar({
  value,
  label,
  showPercentage = true,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ProgressBarProps) {
  // Clamp value between 0 and 100
  const clampedValue = Math.min(Math.max(value, 0), 100);

  const sizeStyles = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const variantStyles = {
    primary: 'bg-gradient-to-r from-primary-500 to-secondary-500',
    secondary: 'bg-gray-500',
    success: 'bg-green-500',
  };

  return (
    <div className={className} {...props}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm text-gray-700">{label}</span>}
          {showPercentage && (
            <span className="text-sm font-semibold text-gray-700">
              {Math.round(clampedValue)}%
            </span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeStyles[size]}`}>
        <div
          className={`${sizeStyles[size]} ${variantStyles[variant]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${clampedValue}%` }}
          role="progressbar"
          aria-valuenow={clampedValue}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'white';
}

export function Spinner({
  size = 'md',
  variant = 'primary',
  className = '',
  ...props
}: SpinnerProps) {
  const sizeStyles = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  const variantStyles = {
    primary: 'border-primary-500 border-t-transparent',
    secondary: 'border-gray-500 border-t-transparent',
    white: 'border-white border-t-transparent',
  };

  return (
    <div className={`inline-block ${className}`} {...props}>
      <div
        className={`${sizeStyles[size]} ${variantStyles[variant]} rounded-full animate-spin`}
      />
    </div>
  );
}
