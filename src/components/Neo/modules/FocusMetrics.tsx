import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { StockData } from '../types';
import { getRadarData, trunc2, fmtNum, fmtPct } from '@/lib/visual-utils';
import { RVOLGauge } from '../metrics/RVOLGauge';
import { MomentumBar } from '../metrics/MomentumBar';
import { NeoRadar } from '../metrics/NeoRadar';
import { BulletMetric } from '../metrics/BulletMetric';

const metric = (label: string, value: string, emphasize = false) => (
    <div className="rounded border border-white/10 bg-white/5 p-3 backdrop-blur-sm transition-colors hover:bg-white/10">
        <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">{label}</div>
        <div className={cn('text-sm font-bold tabular-nums text-zinc-200', emphasize && 'text-cyan-400')}>{value}</div>
    </div>
);

export const FocusMetrics = ({ stock, detailedName, chartData }: { stock: StockData; detailedName?: string; chartData: any[] }) => {
    if (!stock) return null;

    const latestRSI = useMemo(() => {
        if (!chartData || chartData.length < 15) return 50;
        const data = chartData;
        const last = data[data.length - 1];
        if (last && last.RSI !== undefined) return last.RSI;

        // Fallback calculation
        const rsiPeriod = 14;
        let avgGain = 0; let avgLoss = 0;
        const startIndex = Math.max(0, data.length - rsiPeriod - 1);
        for (let i = startIndex + 1; i < data.length; i++) {
            const change = data[i].Close - data[i - 1].Close;
            if (change > 0) avgGain += change;
            else avgLoss -= change;
        }
        avgGain /= rsiPeriod; avgLoss /= rsiPeriod;
        return 100 - (100 / (1 + (avgGain / (avgLoss || 0.0001))));
    }, [chartData]);

    const radarData = useMemo(() => {
        const raw = getRadarData(stock);
        return raw.map(item => ({
            ...item,
            subject: `${item.subject} ${trunc2(item.A)}`
        }));
    }, [stock]);

    return (
        <div className="flex h-full flex-col p-6 font-mono custom-scrollbar overflow-y-auto">
            <div className="mb-6 flex items-start justify-between">
                <div className="flex-1">
                    <Badge variant="outline" className="mb-2 border-emerald-500/30 bg-emerald-500/10 text-emerald-500">即時 (LIVE)</Badge>
                    <div className="flex items-center gap-3">
                        <h1 className="text-4xl font-bold tracking-tight text-white">{stock.symbol}</h1>
                        <AnimatePresence>
                            {latestRSI > 70 && (
                                <motion.span
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    exit={{ scale: 0.8, opacity: 0 }}
                                    className="rounded-sm bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.3)]"
                                >
                                    極度強勢
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </div>
                    <h2 className="line-clamp-1 text-lg text-zinc-500">{detailedName || stock.name || stock.symbol}</h2>
                </div>
                <RVOLGauge rvol={stock.rvol || 0} />
            </div>

            <div className="grid gap-4">
                <div className="mb-2">
                    <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">當前價格 (PRICE)</div>
                    <div className="flex items-baseline gap-3">
                        <span className="tabular-nums text-6xl font-bold tracking-tighter text-white">{fmtNum(stock.price)}</span>
                        <span className={cn('tabular-nums text-xl font-medium', stock.changePercent >= 0 ? 'text-emerald-400' : 'text-rose-500')}>
                            {fmtPct(stock.changePercent)}
                        </span>
                    </div>
                </div>

                <MomentumBar rsi={latestRSI} />

                <div className="mt-4 flex flex-col items-center border-y border-white/5 bg-black/40 py-2">
                    <div className="mb-0 w-full text-[10px] font-bold tracking-widest text-emerald-500/90 text-center">五維基本面戰力 (POWER)</div>
                    <NeoRadar data={radarData} />
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                    {metric('成交量', `${fmtNum((stock.volume || 0) / 1000, 1)}K`)}
                    {metric('產業版塊', stock.sector || '--')}
                </div>

                <div className="mt-6">
                    <div className="mb-4 w-full text-[10px] font-bold tracking-wider text-emerald-500/90">獲利與估值對比 (VALUATION)</div>
                    <BulletMetric label="殖利率 (Yield)" value={stock.yield || 0} target={4.5} unit="%" />
                    <BulletMetric label="獲利能力 (ROE)" value={stock.roe || 0} target={12} unit="%" />
                    <BulletMetric label="營收年增 (RevG)" value={stock.revGrowth || 0} target={15} unit="%" />
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 opacity-60">
                    {metric('本益比 (P/E)', fmtNum(stock.peRatio))}
                    {metric('淨值比 (P/B)', fmtNum(stock.pbRatio))}
                </div>
            </div>
        </div>
    );
};
