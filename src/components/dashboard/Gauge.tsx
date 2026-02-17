import React, { useMemo } from 'react';

interface GaugeProps {
    value: number;
    min: number;
    max: number;
    label: string;
    units?: string;
    size?: number;
    warningThreshold?: number; // Where the "redline" starts
    criticalThreshold?: number;
    type?: 'tacho' | 'turbo' | 'fuel';
}

const Gauge: React.FC<GaugeProps> = ({
    value,
    min,
    max,
    label,
    units,
    size = 300,
    warningThreshold,
    criticalThreshold,
    type = 'tacho'
}) => {
    // Config
    const startAngle = 135;
    const endAngle = 405;
    const radius = size / 2;
    const strokeWidth = size * 0.08;
    const innerRadius = radius - strokeWidth * 2;
    const center = size / 2;

    // Value clamping
    const clampedValue = Math.min(Math.max(value, min), max);

    // Calculate angle
    const valueRange = max - min;
    const angleRange = endAngle - startAngle;
    const angle = startAngle + ((clampedValue - min) / valueRange) * angleRange;

    // Helpers for SVG paths
    const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
        const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
        return {
            x: centerX + (radius * Math.cos(angleInRadians)),
            y: centerY + (radius * Math.sin(angleInRadians))
        };
    };

    const describeArc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
        const start = polarToCartesian(x, y, radius, endAngle);
        const end = polarToCartesian(x, y, radius, startAngle);
        const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
        return [
            "M", start.x, start.y,
            "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
        ].join(" ");
    };

    // Generate ticks
    const ticks = useMemo(() => {
        const tickCount = 11; // 0 to 10
        const generatedTicks = [];
        for (let i = 0; i < tickCount; i++) {
            const tickValue = min + (valueRange / (tickCount - 1)) * i;
            const tickAngle = startAngle + ((tickValue - min) / valueRange) * angleRange;
            const isMajor = i % 1 === 0; // All are major for now
            const start = polarToCartesian(center, center, innerRadius - (isMajor ? 10 : 5), tickAngle);
            const end = polarToCartesian(center, center, innerRadius - (isMajor ? 20 : 10), tickAngle);

            generatedTicks.push(
                <line
                    key={i}
                    x1={start.x}
                    y1={start.y}
                    x2={end.x}
                    y2={end.y}
                    stroke={tickValue >= (warningThreshold ?? max) ? "#ef4444" : "#e5e7eb"}
                    strokeWidth={isMajor ? 3 : 1}
                />
            );

            // Tick Labels
            if (isMajor) {
                const labelPos = polarToCartesian(center, center, innerRadius - 40, tickAngle);
                generatedTicks.push(
                    <text
                        key={`text-${i}`}
                        x={labelPos.x}
                        y={labelPos.y}
                        fill={tickValue >= (warningThreshold ?? max) ? "#ef4444" : "#9ca3af"}
                        fontSize={size * 0.05}
                        fontFamily="monospace"
                        fontWeight="bold"
                        textAnchor="middle"
                        alignmentBaseline="middle"
                    >
                        {Math.abs(tickValue)}
                    </text>
                )
            }
        }
        return generatedTicks;
    }, [min, max, valueRange, angleRange, startAngle, center, innerRadius, warningThreshold, size]);

    // Color logic for the needle/arc
    const isCritical = criticalThreshold !== undefined && value >= criticalThreshold;
    const isWarning = warningThreshold !== undefined && value >= warningThreshold;

    // Dynamic color based on context
    // For stock: value > 0 is red (Taiwan style), value < 0 is green
    // But for a generic tachometer, usually high = red.
    // We will let the parent styling handle text colors, but the gauge itself uses standard racing colors (Green/White -> Red)
    // HOWEVER, for this specific use case (Stock Tachometer), let's adapt:
    // Center (0) is white. Right (+) is Red. Left (-) is Green.

    return (
        <div className="relative inline-flex flex-col items-center justify-center p-4">
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                {/* Background Arc */}
                <path
                    d={describeArc(center, center, innerRadius, startAngle, endAngle)}
                    fill="none"
                    stroke="#1f2937"
                    strokeWidth={strokeWidth}
                    strokeLinecap="butt"
                />

                {/* Dynamic Arc (Optional - maybe just fill to current value?) 
            Let's keep it simple: just the background ring and ticks first.
        */}

                {/* Ticks */}
                {ticks}

                {/* Needle */}
                <g style={{
                    transform: `rotate(${angle}deg)`,
                    transformOrigin: `${center}px ${center}px`,
                    transition: 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                }}>
                    <circle cx={center} cy={center} r={size * 0.04} fill="#ef4444" stroke="#ffffff" strokeWidth="2" />
                    <path d={`M ${center - 4} ${center} L ${center + 4} ${center} L ${center} ${center - innerRadius + 10} Z`} fill="#ef4444" />
                </g>

                {/* Metadata in bottom center area (replaces "x1000rpm") */}
                <text
                    x={center}
                    y={center + size * 0.25}
                    textAnchor="middle"
                    fill="#6b7280"
                    fontSize={size * 0.06}
                    fontFamily="monospace"
                    className="uppercase tracking-widest"
                >
                    {label}
                </text>
                {units && <text
                    x={center}
                    y={center + size * 0.32}
                    textAnchor="middle"
                    fill="#4b5563"
                    fontSize={size * 0.04}
                    fontFamily="monospace"
                >
                    {units}
                </text>}
            </svg>
        </div>
    );
};

export default Gauge;
