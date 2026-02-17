import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { cn } from '@/lib/utils';
import { getStatusColor, trunc2 } from '@/lib/visual-utils';

export const RVOLGauge = ({ rvol }: { rvol: number }) => {
    // RVOL 壓力計：0~3+ 分佈 (放寬上限讓爆量更明顯)
    // 視覺優化：更細的圓環，更現代的配色
    const data = [
        { value: Math.min(rvol, 3), color: getStatusColor(rvol, 'RVOL') },
        { value: Math.max(0, 3 - Math.min(rvol, 3)), color: '#27272a' } // Zinc-800 for background
    ];

    return (
        <div className="relative flex flex-col items-center group cursor-help">
            {/* Tooltip 說明 (純 CSS 實現，避免依賴複雜組件) */}
            <div className="absolute -top-12 z-50 w-48 scale-0 rounded-md border border-white/10 bg-zinc-900 p-2 text-[10px] text-zinc-300 shadow-xl opacity-0 transition-all group-hover:scale-100 group-hover:opacity-100 pointer-events-none">
                <div className="mb-1 font-bold text-emerald-400">量比 (Relative Volume)</div>
                當前成交量 / 過去平均量。
                <div className="mt-1 grid grid-cols-2 gap-1 text-zinc-500">
                    <span>&gt; 1.0 : 出量</span>
                    <span>&gt; 2.0 : 爆量</span>
                </div>
            </div>

            <div className="h-16 w-32">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="100%"
                            startAngle={180}
                            endAngle={0}
                            innerRadius={35} // 更細的環
                            outerRadius={45}
                            paddingAngle={0}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
                    <div className={cn("text-xl font-bold tracking-tighter", rvol > 1 ? "text-emerald-400" : "text-zinc-500")}>
                        {trunc2(rvol).toFixed(1)}x
                    </div>
                    <div className="text-[8px] uppercase tracking-wider text-zinc-600">量比 (RVOL)</div>
                </div>
            </div>
        </div>
    );
};
