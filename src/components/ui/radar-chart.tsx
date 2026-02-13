"use client"

import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts';

interface RadarDataPoint {
    subject: string;
    A: number;
    fullMark: number;
}

interface AI_RadarChartProps {
    data: RadarDataPoint[];
}

export function AI_RadarChart({ data }: AI_RadarChartProps) {
    return (
        <div className="w-full h-[300px] relative">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
                    <PolarGrid stroke="#3f3f46" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                        name="AI 綜合評分"
                        dataKey="A"
                        stroke="#8b5cf6"
                        strokeWidth={3}
                        fill="#8b5cf6"
                        fillOpacity={0.3}
                    />
                </RadarChart>
            </ResponsiveContainer>

            {/* Animated Scanner Effect */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-full opacity-20">
                <div className="absolute top-1/2 left-1/2 w-[150%] h-[2px] bg-primary/50 origin-left animate-[spin_4s_linear_infinite] -translate-y-1/2 -translate-x-1/2 shadow-[0_0_15px_2px_rgba(139,92,246,0.5)]"></div>
            </div>
        </div>
    );
}
