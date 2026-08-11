import React from 'react';
import { clsx } from 'clsx';
import { Region } from '@/lib/types';

interface GridMapProps {
  selectedRegion: Region;
  onSelect: (region: Region) => void;
  className?: string;
}

const PATHS = {
  CAISO: "M50,150 L80,150 L90,190 L110,250 L100,280 L70,300 L40,260 L30,200 Z",
  ERCOT_SYSTEM: "M350,280 L450,280 L450,320 L480,350 L450,420 L400,430 L340,380 L320,320 Z",
  PJM: "M600,180 L700,160 L750,180 L740,240 L680,250 L620,240 Z",
  NYISO: "M730,130 L780,120 L800,150 L770,165 L730,150 Z",
  USA: "M20,100 L200,100 L300,50 L500,50 L700,80 L850,50 L900,150 L850,350 L750,450 L500,480 L300,450 L100,350 L20,250 Z"
};

const LABELS = {
  CAISO: { x: 70, y: 225, label: "CAISO" },
  ERCOT_SYSTEM: { x: 400, y: 350, label: "ERCOT" },
  PJM: { x: 680, y: 210, label: "PJM" },
  NYISO: { x: 765, y: 145, label: "NYISO" },
};

export default function GridMap({ selectedRegion, onSelect, className }: GridMapProps) {
  return (
    <div className={clsx("relative aspect-[2/1] w-full select-none overflow-hidden border border-[#141414] bg-[#e4e3e0]", className)}>
      <svg viewBox="0 0 950 500" className="w-full h-full">
        <defs>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
           <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#b9b6af" strokeWidth="0.7"/>
          </pattern>
        </defs>

        {/* Technical Grid Background */}
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* USA Base Layer (Dark Context) */}
        <path 
          d={PATHS.USA} 
          fill="#d9d8d4"
          stroke="#141414"
          strokeWidth="1"
          strokeDasharray="4 4"
        />

        {/* Regions */}
        {(Object.keys(PATHS) as Array<keyof typeof PATHS>).map((key) => {
          if (key === 'USA') return null;
          const isSelected = selectedRegion === key;
          const regionKey = key as Region;

          return (
            <g 
              key={key} 
              onClick={() => onSelect(regionKey)}
              className="cursor-pointer group"
            >
              <path
                d={PATHS[key as keyof typeof PATHS]}
                fill={isSelected ? "rgba(255, 77, 0, 0.18)" : "transparent"}
                stroke={isSelected ? "#ff4d00" : "#6d6b66"}
                strokeWidth={isSelected ? 2 : 1}
                className="transition-all duration-300 group-hover:stroke-[#ff4d00]"
                filter={isSelected ? "url(#glow)" : ""}
              />
              
              {/* Connection Dots (Simulating Grid Nodes) */}
              {isSelected && (
                 <circle 
                   cx={LABELS[key as keyof typeof LABELS].x} 
                   cy={LABELS[key as keyof typeof LABELS].y - 20} 
                   r="3" 
                   fill="#ff4d00"
                   className="animate-pulse"
                 />
              )}

              {/* Label */}
              {LABELS[key as keyof typeof LABELS] && (
                <text
                  x={LABELS[key as keyof typeof LABELS].x}
                  y={LABELS[key as keyof typeof LABELS].y}
                  fill={isSelected ? "#141414" : "#6d6b66"}
                  fontSize={isSelected ? 14 : 12}
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="pointer-events-none transition-all duration-300"
                >
                  {LABELS[key as keyof typeof LABELS].label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
