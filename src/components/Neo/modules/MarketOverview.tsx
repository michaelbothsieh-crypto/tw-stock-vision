import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { StockData } from '../types';
import { fmtNum, fmtPct } from '@/lib/visual-utils';

export const MarketOverview = ({
    data,
    onSelect,
    currentSymbol,
    market,
    onMarketChange,
    className
}: {
    data: StockData[];
    onSelect: (s: string) => void;
    currentSymbol: string;
    market: 'TW' | 'US';
    onMarketChange: (m: 'TW' | 'US') => void;
    className?: string;
}) => {
    return (
        <div className={cn("flex flex-col border-l border-white/10 bg-zinc-950/50 lg:h-full lg:overflow-hidden", className)}>
            <div className="flex items-center justify-between border-b border-white/10 bg-black/20 p-2">
                <div className="font-mono text-[10px] tracking-wider text-zinc-500">市場總覽 (MARKET OVERVIEW)</div>
                <div className="flex rounded bg-black/40 p-0.5">
                    <button
                        onClick={() => onMarketChange('TW')}
                        className={cn(
                            "rounded px-2 py-0.5 text-[10px] font-bold transition-all",
                            market === 'TW' ? "bg-emerald-500/20 text-emerald-500" : "text-zinc-600 hover:text-zinc-400"
                        )}
                    >
                        台股
                    </button>
                    <button
                        onClick={() => onMarketChange('US')}
                        className={cn(
                            "rounded px-2 py-0.5 text-[10px] font-bold transition-all",
                            market === 'US' ? "bg-cyan-500/20 text-cyan-500" : "text-zinc-600 hover:text-zinc-400"
                        )}
                    >
                        美股
                    </button>
                </div>
            </div>

            {/* 搜尋欄位 (Desktop Only) */}
            <div className="hidden border-b border-white/5 bg-black/20 p-2 lg:block">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="搜尋代號 (如 2330, NVDA)..."
                        className="w-full rounded bg-zinc-900 py-1.5 pl-8 pr-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                const target = (e.target as HTMLInputElement).value.toUpperCase();
                                if (target) {
                                    onSelect(target);
                                    (e.target as HTMLInputElement).value = '';
                                }
                            }
                        }}
                    />
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>

            {/* 說明區塊 (Desktop Only) */}
            <div className="hidden border-b border-white/5 bg-emerald-500/5 p-3 font-sans text-[11px] leading-relaxed text-zinc-400 lg:block">
                <div className="mb-1 flex items-center gap-1.5 font-bold text-emerald-500/80">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                    {market === 'TW' ? '台股' : '美股'}市場資料指南
                </div>
                <p>
                    本列表依據 <span className="text-zinc-200">TradingView 技術評等</span> 降序排列。
                    {market === 'TW' && " 包含上市、上櫃及興櫃標的。"}
                    標註「<span className="text-emerald-500">強勢</span>」代表標的處於強力買入狀態。
                </p>
            </div>

            <div className="flex-1 p-2 icon-scrollbar lg:overflow-y-auto">
                <div className="space-y-1">
                    {data.map((stock) => (
                        <motion.div
                            key={stock.symbol}
                            onClick={() => onSelect(stock.symbol)}
                            whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                            className={cn(
                                'cursor-pointer rounded border border-transparent p-2 transition-all',
                                currentSymbol === stock.symbol ? 'border-emerald-500/30 bg-emerald-500/10' : 'hover:border-white/10'
                            )}
                        >
                            <div className="flex items-center justify-between font-mono">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold text-zinc-200">{stock.symbol}</span>
                                        {stock.rating > 0.5 && <span className="text-[10px] text-emerald-500">強勢</span>}
                                        {(stock as any).rsi > 70 && <span className="text-[10px] text-emerald-400">🔥 極強</span>}
                                    </div>
                                    <h4 className="max-w-[140px] truncate text-xs text-zinc-500">{stock.name || stock.symbol}</h4>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm text-zinc-200">{fmtNum(stock.price)}</div>
                                    <div className={cn('text-xs', stock.changePercent >= 0 ? 'text-emerald-400' : 'text-rose-500')}>
                                        {fmtPct(stock.changePercent)}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};
