"use client"

import { cn } from "@/lib/utils"

interface StatProps {
    label: string
    value: string | number
    subtext?: string
    color?: string
}

function Stat({ label, value, subtext, color }: StatProps) {
    return (
        <div className="flex flex-col gap-1 p-3 sm:p-4 rounded-2xl bg-background/40 border border-border/30 backdrop-blur-md hover:bg-background/50 transition-colors group relative overflow-hidden h-full">
            <div className="absolute top-0 left-0 w-full h-[1px] bg-white/20 animate-scan opacity-0 group-hover:opacity-100"></div>
            <span className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider font-semibold truncate">{label}</span>
            <span className={cn("text-lg sm:text-xl font-bold font-mono tracking-tight tabular-nums break-all", color || "text-foreground")}>{value}</span>
            {subtext && <span className="text-[9px] sm:text-[10px] text-muted-foreground/80 truncate">{subtext}</span>}
        </div>
    )
}

function formatMarketCap(value: number): string {
    if (value >= 1e12) return (value / 1e12).toFixed(2) + "兆"
    if (value >= 1e8) return (value / 1e8).toFixed(1) + "億"
    if (value >= 1e6) return (value / 1e6).toFixed(1) + "百萬"
    return value.toLocaleString()
}

interface TechnicalEvidenceProps {
    volume: number
    marketCap?: number
    rvol: number
    vwap: number
    cmf: number
    price: number
}

export function TechnicalEvidence({ volume, marketCap, rvol, vwap, cmf, price }: TechnicalEvidenceProps) {
    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
            <Stat label="成交量" value={(volume || 0).toLocaleString()} />
            <Stat label="市值" value={marketCap ? formatMarketCap(marketCap) : "--"} />
            <Stat label="RVOL (量能)" value={(rvol || 0).toFixed(2) + "x"}
                subtext={(rvol || 0) > 1.5 ? "🔥 主力介入明顯" : (rvol || 0) > 1.0 ? "量能溫和" : "量縮整理"}
                color={(rvol || 0) > 1.5 ? "text-amber-400" : undefined} />
            <Stat label="VWAP" value={(vwap || 0).toFixed(2)}
                subtext={price > (vwap || 0) ? "📈 站上均價線" : "📉 跌破均價線"}
                color={price > (vwap || 0) ? "text-emerald-400" : "text-rose-400"} />
            <Stat label="CMF (金流)" value={(cmf || 0).toFixed(2)}
                subtext={(cmf || 0) > 0 ? "💰 資金流入" : "💸 資金流出"}
                color={(cmf || 0) > 0 ? "text-emerald-400" : "text-rose-400"} />
        </div>
    )
}
