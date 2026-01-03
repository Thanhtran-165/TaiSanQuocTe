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
}: PriceCardProps) {
  const changeColor = change && change.value >= 0 ? 'text-green-400' : 'text-red-400';

  return (
    <div
      className={`glass-card rounded-2xl p-5 cursor-pointer ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={`w-6 h-6 ${iconClass}`} />
          <h3 className="text-sm font-semibold text-white/90">{title}</h3>
        </div>
      </div>

      <div className="space-y-1">
        <div className="text-2xl font-bold text-white">{price}</div>
        <div className="text-xs text-white/70">{subtitle}</div>

        {change && (
          <div className={`text-xs font-semibold ${changeColor} mt-1`}>
            {change.value >= 0 ? '+' : ''}
            {change.value.toFixed(2)} ({change.percent >= 0 ? '+' : ''}
            {change.percent.toFixed(2)}%)
          </div>
        )}
      </div>
    </div>
  );
}
