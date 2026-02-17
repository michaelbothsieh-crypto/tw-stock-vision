import React from 'react';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer
} from 'recharts';

export const NeoRadar = ({ data }: { data: any[] }) => {
    return (
        <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="55%" outerRadius="60%" data={data}>
                    <PolarGrid stroke="#ffffff" strokeOpacity={0.1} gridType="polygon" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#e4e4e7', fontSize: 9, fontWeight: 500 }} // Lighter text (zinc-200)
                    />
                    {/* 完全隱藏刻度文字與軸線 */}
                    <PolarRadiusAxis
                        domain={[0, 100]}
                        axisLine={false}
                        tick={false}
                        tickLine={false}
                    />
                    <Radar
                        name="Stock"
                        dataKey="A"
                        stroke="#10b981"
                        strokeWidth={3} // Thinner/Thicker per user request (Thicker +1px)
                        fill="#10b981"
                        fillOpacity={0.5} // More opaque (from 0.2->0.4 -> 0.5)
                        animationDuration={1000}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};
