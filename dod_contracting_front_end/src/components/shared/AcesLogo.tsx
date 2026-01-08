/**
 * AcesLogo Component
 *
 * SVG logo for ACES (Acquisition Contracting Enterprise System)
 * Features a spade symbol with an integrated checkmark.
 *
 * @param size - Size variant: 'sm', 'md', 'lg', 'xl'
 * @param showText - Whether to show "ACES" text next to the icon
 * @param className - Additional CSS classes
 */

import { cn } from '@/lib/utils';

interface AcesLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  sm: { height: 28 },
  md: { height: 36 },
  lg: { height: 56 },
  xl: { height: 80 },
};

export function AcesLogo({ size = 'md', showText = true, className }: AcesLogoProps) {
  const config = sizeMap[size];

  // Calculate width based on aspect ratio (860:240 for full logo, 240:240 for icon only)
  const aspectRatio = showText ? 860 / 240 : 1;
  const width = config.height * aspectRatio;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={width}
      height={config.height}
      viewBox={showText ? "0 0 860 240" : "0 0 240 240"}
      role="img"
      aria-label="ACES logo"
      className={cn('flex-shrink-0', className)}
    >
      <defs>
        <style>
          {`.aces-navy { fill: hsl(var(--primary)); }
            .aces-word { fill: hsl(var(--primary)); font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-weight: 600; letter-spacing: 0.04em; }`}
        </style>
      </defs>

      {/* Icon */}
      <g transform={showText ? "translate(60,28)" : "translate(0,28)"}>
        {/* Spade body */}
        <path
          className="aces-navy"
          d="
            M120 18
            C 82 54, 44 78, 44 122
            C 44 168, 98 182, 120 154
            C 142 182, 196 168, 196 122
            C 196 78, 158 54, 120 18
            Z
            M108 154
            C 102 178, 92 196, 78 210
            L 162 210
            C 148 196, 138 178, 132 154
            Z
          "
        />

        {/* Checkmark */}
        <path
          d="M86 118 L112 146 L170 72"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="16"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>

      {/* Wordmark */}
      {showText && (
        <text x="300" y="145" className="aces-word" fontSize="104">
          ACES
        </text>
      )}
    </svg>
  );
}

/**
 * AcesLogoIcon - Just the spade icon without text
 * Useful for favicons, small buttons, etc.
 */
export function AcesLogoIcon({
  size = 32,
  className
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 240 240"
      role="img"
      aria-label="ACES icon"
      className={className}
    >
      <defs>
        <style>
          {`.aces-icon-fill { fill: hsl(var(--primary)); }`}
        </style>
      </defs>
      {/* Icon centered */}
      <g transform="translate(0,28)">
        {/* Spade body */}
        <path
          className="aces-icon-fill"
          d="
            M120 18
            C 82 54, 44 78, 44 122
            C 44 168, 98 182, 120 154
            C 142 182, 196 168, 196 122
            C 196 78, 158 54, 120 18
            Z
            M108 154
            C 102 178, 92 196, 78 210
            L 162 210
            C 148 196, 138 178, 132 154
            Z
          "
        />

        {/* Checkmark */}
        <path
          d="M86 118 L112 146 L170 72"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="16"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    </svg>
  );
}

export default AcesLogo;
