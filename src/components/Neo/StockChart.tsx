import React, { useMemo } from 'react';
import {
    ComposedChart,
    Area,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { cn } from '@/lib/utils';

interface ChartData {
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    Volume: number;
    RSI?: number;
}

interface StockChartProps {
    data: ChartData[];
    color?: string;
    onRetry?: () => void;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        // 直接從原始數據對象獲取，這比 payload.find 穩定得多
        const rawData = payload[0].payload;
        const close = rawData.Close;
        const vol = rawData.Volume;
        const rsi = rawData.RSI;

        return (
            <div className="rounded border border-white/10 bg-black/95 p-3 text-[11px] font-mono shadow-[0_20px_50px_rgba(0,0,0,0.5)] backdrop-blur-xl">
                <div className="mb-2 border-b border-white/10 pb-1 flex justify-between">
                    <span className="text-zinc-500">{label.length < 6 ? '時間' : '日期'}</span>
                    <span className="text-emerald-500">{label}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 min-w-[120px]">
                    <div className="text-zinc-400">收盤 (C)</div>
                    <div className="text-right text-zinc-100 font-bold">
                        {typeof close === 'number' ? close.toFixed(2) : '--'}
                    </div>

                    <div className="text-zinc-400 text-[9px]">成交量 (V)</div>
                    <div className="text-right text-zinc-400 text-[9px]">
                        {typeof vol === 'number' ? vol.toLocaleString() : '--'}
                    </div>

                    {typeof rsi === 'number' && (
                        <>
                            <div className={cn("text-[10px]", rsi > 70 ? "text-emerald-400" : rsi < 30 ? "text-slate-500" : "text-zinc-500")}>RSI (14)</div>
                            <div className={cn("text-right text-[10px]", rsi > 70 ? "text-emerald-400" : rsi < 30 ? "text-slate-500" : "text-zinc-500")}>
                                {rsi.toFixed(1)} {rsi > 70 ? '🔥' : rsi < 30 ? '❄️' : ''}
                            </div>
                        </>
                    )}
                </div>
            </div>
        );
    }
    return null;
};

export const StockChart = ({ data, color = "#10b981", onRetry }: StockChartProps) => {
    // 計算 RSI (14)
    const chartData = useMemo(() => {
        if (!data || data.length < 2) return data;

        const rsiPeriod = 14;
        const results = data.map(d => ({ ...d, RSI: 50 }));

        if (data.length <= rsiPeriod) return results;

        let avgGain = 0;
        let avgLoss = 0;

        // 計算初始平均漲跌
        for (let i = 1; i <= rsiPeriod; i++) {
            const change = data[i].Close - data[i - 1].Close;
            if (change > 0) avgGain += change;
            else avgLoss -= change;
        }
        avgGain /= rsiPeriod;
        avgLoss /= rsiPeriod;

        // 初始化第一個 RSI 點
        results[rsiPeriod].RSI = 100 - (100 / (1 + (avgGain / (avgLoss || 1))));

        // 平滑計算後續 RSI
        for (let i = rsiPeriod + 1; i < data.length; i++) {
            const change = data[i].Close - data[i - 1].Close;
            const gain = change > 0 ? change : 0;
            const loss = change < 0 ? -change : 0;

            avgGain = (avgGain * (rsiPeriod - 1) + gain) / rsiPeriod;
            avgLoss = (avgLoss * (rsiPeriod - 1) + loss) / rsiPeriod;

            results[i].RSI = 100 - (100 / (1 + (avgGain / (avgLoss || 0.0001))));
        }

        return results;
    }, [data]);

    if (!chartData || chartData.length === 0) {
        return (
            <div className="flex h-full w-full flex-col items-center justify-center gap-3">
                <p className="font-mono text-xs text-zinc-500">暫無歷史數據</p>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="rounded border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 font-mono text-xs text-emerald-400 transition-colors hover:bg-emerald-500/20"
                    >
                        重新載入
                    </button>
                )}
            </div>
        );
    }

    // 取得價格區間以優化 Y 軸
    const prices = chartData.map(d => d.Close);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const range = maxP - minP;

    // 計算漸層 stops (根據 RSI)
    // 這裡我們簡化處理：使用 RSI 的動態色彩作為主色
    const latestRSI = chartData[chartData.length - 1].RSI || 50;
    const dynamicColor = latestRSI > 70 ? "#00ffbb" : latestRSI < 30 ? "#64748b" : color;

    return (
        <div className="h-full w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: 10 }}>
                    <defs>
                        <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={dynamicColor} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={dynamicColor} stopOpacity={0} />
                        </linearGradient>
                        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="2" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff" opacity={0.03} vertical={false} />

                    <XAxis
                        dataKey="Date"
                        hide
                    />

                    {/* 價格 Y 軸 */}
                    <YAxis
                        yAxisId="price"
                        orientation="right"
                        domain={[minP - range * 0.1, maxP + range * 0.1]}
                        tick={{ fill: '#444', fontSize: 9, fontFamily: 'monospace' }}
                        axisLine={false}
                        tickLine={false}
                        width={45}
                    />

                    {/* 成交量 Y 軸 (隱藏，僅用於 Bar 比例) */}
                    <YAxis
                        yAxisId="volume"
                        orientation="left"
                        hide
                        domain={[0, 'dataMax * 4']}
                    />

                    {/* 成交量 Bar */}
                    <Bar
                        yAxisId="volume"
                        dataKey="Volume"
                        barSize={2}
                        isAnimationActive={false}
                    >
                        {chartData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={index > 0 && entry.Close >= (chartData[index - 1]?.Close || 0) ? '#10b98122' : '#f43f5e22'}
                            />
                        ))}
                    </Bar>

                    {/* 價格區域 */}
                    <Area
                        yAxisId="price"
                        type="monotone"
                        dataKey="Close"
                        stroke={dynamicColor}
                        fillOpacity={1}
                        fill="url(#colorClose)"
                        strokeWidth={latestRSI > 70 ? 2 : 1.5}
                        dot={false}
                        isAnimationActive={false}
                        filter={latestRSI > 70 ? "url(#glow)" : undefined}
                        activeDot={{ r: 4, stroke: dynamicColor, strokeWidth: 2, fill: '#000' }}
                    />

                    <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ stroke: '#ffffff44', strokeWidth: 1 }} // 加深一點顏色確保可見
                        isAnimationActive={false}
                        offset={10}
                        position={{ y: 0 }} // 固定頂部顯示避免遮擋手指/游標
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
};
