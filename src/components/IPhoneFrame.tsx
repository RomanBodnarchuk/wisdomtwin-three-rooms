import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Model label for aria / data attrs — marketing names iPhone 17 Max / 19 Max */
  model?: '17-max' | '19-max';
  className?: string;
  /** Show subtle live glow on the bezel */
  live?: boolean;
  /** Compact in-scene phone (kitchen handset) vs hero device */
  size?: 'hero' | 'handset';
}

/**
 * Photoreal titanium iPhone Pro Max chrome (Dynamic Island era).
 * Live Buzz UI renders inside the screen glass.
 */
export function IPhoneFrame({
  children,
  model = '19-max',
  className = '',
  live = false,
  size = 'hero',
}: Props) {
  const isHandset = size === 'handset';

  return (
    <div
      className={`iphone-device relative mx-auto select-none ${isHandset ? 'iphone-handset' : 'iphone-hero'} ${className}`}
      data-testid="iphone-frame"
      data-model={model}
      data-live={live ? 'true' : 'false'}
      role="presentation"
      aria-label={`iPhone ${model === '19-max' ? '19' : '17'} Pro Max with Buzz`}
    >
      {/* Outer titanium shell */}
      <div className="iphone-shell relative h-full w-full">
        {/* Side buttons — left: action + volume */}
        <div className="iphone-btn iphone-btn-action" aria-hidden />
        <div className="iphone-btn iphone-btn-vol-up" aria-hidden />
        <div className="iphone-btn iphone-btn-vol-down" aria-hidden />
        {/* Right: power */}
        <div className="iphone-btn iphone-btn-power" aria-hidden />

        {/* Bezel ring */}
        <div className={`iphone-bezel ${live ? 'iphone-bezel-live' : ''}`}>
          {/* Glass screen well */}
          <div className="iphone-glass">
            {/* Status / Dynamic Island row */}
            <div className="iphone-status-row" aria-hidden>
              <span className="iphone-time">9:40</span>
              <div className="iphone-island">
                <span className="iphone-island-camera" />
                <span className="iphone-island-sensor" />
              </div>
              <span className="iphone-status-icons">
                <span className="iphone-signal" />
                <span className="iphone-wifi" />
                <span className="iphone-battery" />
              </span>
            </div>

            {/* App content — clipped to screen radius */}
            <div className="iphone-screen-content">{children}</div>

            {/* Home indicator */}
            <div className="iphone-home-indicator" aria-hidden />

            {/* Specular glass sheen */}
            <div className="iphone-glass-sheen" aria-hidden />
          </div>
        </div>
      </div>

      {/* Soft drop shadow plate */}
      <div className="iphone-shadow" aria-hidden />
    </div>
  );
}
