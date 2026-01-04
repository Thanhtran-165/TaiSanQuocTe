/**
 * PriceCard Component
 * Displays price information with liquid glass effect
 */

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface PriceCardProps {
  icon: LucideIcon;
  title: string;
  price: string;
  subtitle: string;
  change?: {
    value: number;
    percent: number;
  };
  onClick?: () => void;
  className?: string;
  iconClass?: string;
  size?: 'md' | 'sm';
}

export default function PriceCard({
  icon: Icon,
  title,
  price,
  subtitle,
  change,
  onClick,
  className = '',
  iconClass = 'icon-glow',
  size = 'md',
}: PriceCardProps) {
  const changeColor = change && change.value >= 0 ? 'text-green-400' : 'text-red-400';

  const padClass = size === 'sm' ? 'p-4' : 'p-5';
  const iconSizeClass = size === 'sm' ? 'w-5 h-5' : 'w-6 h-6';
  const titleClass = size === 'sm' ? 'text-xs' : 'text-sm';
  const priceClass = size === 'sm' ? 'text-xl' : 'text-2xl';
  const subtitleClass = size === 'sm' ? 'text-[11px]' : 'text-xs';
  const changeClass = size === 'sm' ? 'text-[11px]' : 'text-xs';

  return (
    <div
      className={`glass-card rounded-2xl ${padClass} cursor-pointer ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={`${iconSizeClass} ${iconClass}`} />
          <h3 className={`${titleClass} font-semibold text-white/90`}>{title}</h3>
        </div>
      </div>

      <div className="space-y-1">
        <div className={`${priceClass} font-bold text-white`}>{price}</div>
        <div className={`${subtitleClass} text-white/70`}>{subtitle}</div>

        {change && (
          <div className={`${changeClass} font-semibold ${changeColor} mt-1`}>
            {change.value >= 0 ? '+' : ''}
            {change.value.toFixed(2)} ({change.percent >= 0 ? '+' : ''}
            {change.percent.toFixed(2)}%)
          </div>
        )}
      </div>
    </div>
  );
}
