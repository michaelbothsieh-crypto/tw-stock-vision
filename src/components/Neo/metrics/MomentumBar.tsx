import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { trunc2 } from '@/lib/visual-utils';

export const MomentumBar = ({ rsi }: { rsi: number }) => {
    // 映射 RSI (0-100) 到顏色
    // 30 以下: 灰藍, 70 以上: 螢光綠/火紅
    const getColor = (v: number) => {
        if (v > 70) return 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.5)]';
        if (v < 30) return 'bg-slate-500';
        return 'bg-emerald-600/50';
    };

    const rsiVal = trunc2(rsi);

    return (
        <div className="mt-6 rounded border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
            <div className="mb-3 flex items-center justify-between text-xs font-mono">
                <span className="text-zinc-500">市場動能 (MOMENTUM)</span>
                <span className={cn("font-bold", rsiVal > 70 ? "text-emerald-400" : rsiVal < 30 ? "text-zinc-400" : "text-zinc-300")}>
                    RSI {rsiVal.toFixed(1)} {rsiVal > 70 ? '🔥' : rsiVal < 30 ? '❄️' : ''}
                </span>
            </div>
            <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                <motion.div
                    className={cn("absolute h-full rounded-full transition-colors duration-500", getColor(rsiVal))}
                    initial={{ width: 0 }}
                    animate={{ width: `${rsiVal}%` }}
                    transition={{ type: "spring", stiffness: 50, damping: 15 }}
                />
            </div>
            <div className="mt-2 flex justify-between px-0.5 font-mono text-[8px] uppercase tracking-tighter text-zinc-600">
                <span>超賣</span>
                <span>中性</span>
                <span>超買</span>
            </div>
        </div>
    );
};
