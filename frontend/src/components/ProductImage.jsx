import React from 'react';
import { Package, ImageOff } from 'lucide-react';
import { API_BASE } from '../services/api';
import { cn } from '../lib/utils';

// URL base para imágenes via proxy
export const getImageUrl = (sku) => `${API_BASE}/images/${encodeURIComponent(sku)}`;

// Componente de imagen de producto con fallback y skeleton de carga
export default function ProductImage({ sku, alt, className, size = 'md' }) {
  const [error, setError] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-48 h-48',
    xl: 'w-full h-40',
  };

  if (error) {
    return (
      <div className={cn(
        "flex items-center justify-center bg-notion-bg-subtle rounded-lg",
        sizeClasses[size],
        className
      )}>
        <ImageOff className="text-notion-text-secondary" size={size === 'lg' || size === 'xl' ? 48 : size === 'md' ? 32 : 20} />
      </div>
    );
  }

  return (
    <div className={cn("relative", sizeClasses[size], className)}>
      {loading && (
        <div className={cn(
          "absolute inset-0 flex items-center justify-center bg-notion-bg-subtle rounded-lg animate-pulse",
          sizeClasses[size]
        )}>
          <Package className="text-notion-text-secondary" size={size === 'lg' || size === 'xl' ? 48 : size === 'md' ? 32 : 20} />
        </div>
      )}
      <img
        src={getImageUrl(sku)}
        alt={alt}
        className={cn(
          "object-contain rounded-lg",
          sizeClasses[size],
          loading && "opacity-0"
        )}
        onLoad={() => setLoading(false)}
        onError={() => {
          setLoading(false);
          setError(true);
        }}
      />
    </div>
  );
}
