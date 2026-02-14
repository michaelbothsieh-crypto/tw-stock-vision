"use client"

import { StockData } from "./types"
import { TrendingUp, ShieldCheck, PieChart, Activity } from "lucide-react"
import { InfoTooltip, Gauge } from "./vitals-grid"
import { STOCK_DEFINITIONS } from "@/lib/tooltips"
import { cn } from "@/lib/utils"

interface FinancialHealthCardProps {
    data: StockData
}

export function FinancialHealthCard({ data }: FinancialHealthCardProps) {
    if (!data) return null;

    // 獲利得分 (ROE/ROA/Margin 綜合)
    const profitability = Math.min(100, (data.roe || 0) * 2 + (data.netMargin || 0) * 2);
    // 安全得分 (Debt/Equity 越低越高分)
    const safety = Math.max(0, Math.min(100, 100 - (data.debtToEquity || 50)));
    // 成長得分 (Revenue Growth)
    const growth = Math.min(100, 50 + (data.revGrowth || 0));

    const getStatusColor = (val: number) => {
        if (val > 70) return "text-emerald-400";
        if (val > 40) return "text-yellow-400";
        return "text-rose-400";
    };

    return (
        <div className="rounded-3xl border border-border/50 bg-black/20 p-6 shadow-xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute top-0 right-0 p-4">
                {data.healthLabel && (
                    <div className={cn(
                        "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter shadow-lg border",
                        data.healthLabel === "優" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" :
                            data.healthLabel === "良" ? "bg-blue-500/20 text-blue-400 border-blue-500/50" :
                                data.healthLabel === "普" ? "bg-zinc-500/20 text-zinc-400 border-zinc-500/50" :
                                    "bg-rose-500/20 text-rose-400 border-rose-500/50"
                    )}>
                        體質{data.healthLabel}
                    </div>
                )}
            </div>

            <div className="relative z-10 space-y-6">
                <div className="flex justify-between items-center">
                    <h3 className="text-xs md:text-sm font-bold text-zinc-400 uppercase tracking-[0.12em] flex items-center gap-2">
                        <Activity className="h-4 w-4 text-indigo-400" /> 財務體質深度分析
                        {data.growthProjection && (
                            <span className="ml-2 px-2 py-0.5 rounded bg-zinc-800 text-[10px] text-zinc-500 font-mono">
                                趨勢: {data.growthProjection}
                            </span>
                        )}
                    </h3>
                </div>

                <div className="space-y-5">
                    {/* Profitability */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-end">
                            <div className="flex items-center gap-2">
                                <PieChart className="w-4 h-4 text-blue-400" />
                                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">獲利能力 (ROE)</span>
                                <InfoTooltip content={STOCK_DEFINITIONS["ROE"] || "股東權益報酬率，衡量公司獲利效率。"} />
                            </div>
                            <span className={cn("text-xs font-mono font-bold", getStatusColor(profitability))}>
                                {data.roe?.toFixed(1) || "0.0"}%
                            </span>
                        </div>
                        <Gauge value={profitability} min={0} max={100} />
                    </div>

                    {/* Safety */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-end">
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">財務安全性 (負債比)</span>
                                <InfoTooltip content={STOCK_DEFINITIONS["負債權益比"] || "負債佔權益比例，數值越低代表財務越穩健。"} />
                            </div>
                            <span className={cn("text-xs font-mono font-bold", getStatusColor(safety))}>
                                {data.debtToEquity?.toFixed(1) || "0.0"}
                            </span>
                        </div>
                        <Gauge value={safety} min={0} max={100} />
                    </div>

                    {/* Growth */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-end">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-rose-400" />
                                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">成長動能 (營收 YoY)</span>
                                <InfoTooltip content={STOCK_DEFINITIONS["營收成長率"] || "營收年增率，判定公司是否處於擴張期。"} />
                            </div>
                            <span className={cn("text-xs font-mono font-bold", getStatusColor(growth))}>
                                {data.revGrowth?.toFixed(1) || "0.0"}%
                            </span>
                        </div>
                        <Gauge value={growth} min={0} max={100} />
                    </div>
                </div>

                <div className="pt-2 grid grid-cols-2 gap-4">
                    <div className="bg-zinc-800/30 p-3 rounded-2xl border border-zinc-700/30">
                        <p className="text-[10px] text-zinc-500 uppercase font-black tracking-widest mb-1">F-Score</p>
                        <p className="text-lg font-black font-mono text-zinc-200">{data.fScore || 0}<span className="text-zinc-500 text-xs ml-1">/ 9</span></p>
                    </div>
                    <div className="bg-zinc-800/30 p-3 rounded-2xl border border-zinc-700/30">
                        <p className="text-[10px] text-zinc-500 uppercase font-black tracking-widest mb-1">Z-Score</p>
                        <p className="text-lg font-black font-mono text-zinc-200">{data.zScore?.toFixed(2) || 0.00}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
