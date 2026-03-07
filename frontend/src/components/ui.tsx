/* ── Shared UI components ─────────────────────────────────────────────── */

import { clsx } from 'clsx';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

/* ── Badge ────────────────────────────────────────────────────────────── */

const badgeColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  reviewed: 'bg-blue-100 text-blue-700',
  selected: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  // generic
  default: 'bg-gray-100 text-gray-700',
  info: 'bg-cyan-100 text-cyan-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
};

export function Badge({
  children,
  variant = 'default',
  className,
}: {
  children: ReactNode;
  variant?: string;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        badgeColors[variant] ?? badgeColors.default,
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ── Button ───────────────────────────────────────────────────────────── */

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const buttonBase =
  'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';

const buttonVariants: Record<string, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary:
    'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-400',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  ghost: 'text-gray-600 hover:bg-gray-100 focus:ring-gray-400',
};

const buttonSizes: Record<string, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        buttonBase,
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size={14} />}
      {children}
    </button>
  );
}

/* ── Card ─────────────────────────────────────────────────────────────── */

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        'rounded-xl border border-gray-200 bg-white shadow-sm',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx('border-b border-gray-100 px-6 py-4', className)}>
      {children}
    </div>
  );
}

export function CardBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={clsx('px-6 py-4', className)}>{children}</div>;
}

/* ── Score bar / meter ────────────────────────────────────────────────── */

export function ScoreBar({
  value,
  label,
  className,
}: {
  value: number;
  label?: string;
  className?: string;
}) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? 'bg-green-500'
      : pct >= 60
        ? 'bg-blue-500'
        : pct >= 40
          ? 'bg-amber-500'
          : 'bg-red-500';

  return (
    <div className={clsx('space-y-1', className)}>
      {label && (
        <div className="flex justify-between text-xs text-gray-500">
          <span>{label}</span>
          <span className="font-medium text-gray-700">{pct}%</span>
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-gray-100">
        <div
          className={clsx('h-2 rounded-full transition-all duration-500', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

/* ── Spinner ──────────────────────────────────────────────────────────── */

export function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg
      className={clsx('animate-spin text-current', className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

/* ── Empty state ──────────────────────────────────────────────────────── */

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="mb-4 text-gray-300">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-700">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ── Error banner ─────────────────────────────────────────────────────── */

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
      <div className="flex items-center gap-3">
        <span className="text-red-600 text-sm font-medium">Error</span>
        <span className="text-red-700 text-sm flex-1">{message}</span>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    </div>
  );
}

/* ── Stat card (for the dashboard) ────────────────────────────────────── */

export function StatCard({
  label,
  value,
  icon,
  className,
}: {
  label: string;
  value: string | number;
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <Card className={className}>
      <CardBody className="flex items-center gap-4">
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            {icon}
          </div>
        )}
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </CardBody>
    </Card>
  );
}
