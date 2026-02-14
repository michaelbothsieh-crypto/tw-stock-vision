"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { TrendingUp, RefreshCcw, ChevronRight, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

interface TrendingStock {
    symbol: string
    description: string
    price: number
    changePercent: number
    rating: number
}

interface MarketExplorerProps {
    onSelectStock: (symbol: string) => void
}

export function MarketExplorer({ onSelectStock }: MarketExplorerProps) {
    const [trending, setTrending] = useState<TrendingStock[]>([])
    const [loading, setLoading] = useState(true)
    const [market, setMarket] = useState<'TW' | 'US'>('TW')
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

    const fetchTrending = async (m: 'TW' | 'US' = market) => {
        setLoading(true)
        try {
            const res = await fetch(`/api/market/trending?market=${m}`)
            const data = await res.json()
            const results = Array.isArray(data) ? data : (data.results || [])
            setTrending(results)
            setLastUpdated(new Date())
        } catch (error) {
            console.error("Failed to fetch trending:", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchTrending()
        const interval = setInterval(() => fetchTrending(market), 300000)
        return () => clearInterval(interval)
    }, [market])

    return (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-md overflow-hidden flex flex-col h-full shadow-2xl">
            <div className="p-5 border-b border-white/5 flex items-center justify-between bg-zinc-900/90">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-inner">
                        <TrendingUp className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                            市場發現
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">AI</span>
                        </h3>
                        <div className="flex gap-2 mt-1">
                            <button
                                onClick={() => { setMarket('TW'); fetchTrending('TW'); }}
                                className={cn("text-[10px] uppercase tracking-tighter transition-colors", market === 'TW' ? "text-primary font-bold" : "text-zinc-500 hover:text-zinc-400")}
                            >
                                台股趨勢
                            </button>
                            <span className="text-zinc-800">|</span>
                            <button
                                onClick={() => { setMarket('US'); fetchTrending('US'); }}
                                className={cn("text-[10px] uppercase tracking-tighter transition-colors", market === 'US' ? "text-primary font-bold" : "text-zinc-500 hover:text-zinc-400")}
                            >
                                美股動能
                            </button>
                        </div>
                    </div>
                </div>
                <button
                    onClick={() => fetchTrending(market)}
                    disabled={loading}
                    className="p-2 hover:bg-zinc-800 rounded-full transition-all active:scale-90"
                >
                    <RefreshCcw className={cn("h-4 w-4 text-zinc-400 group-hover:text-primary transition-all", loading && "animate-spin")} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2.5">
                {loading && trending.length === 0 ? (
                    Array(5).fill(0).map((_, i) => (
                        <div key={i} className="h-16 w-full bg-zinc-800/20 animate-pulse rounded-2xl border border-white/5" />
                    ))
                ) : trending.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-3">
                        <div className="w-12 h-12 bg-zinc-800/50 rounded-full flex items-center justify-center border border-white/5">
                            <Activity className="h-5 w-5 text-zinc-600" />
                        </div>
                        <p className="text-xs text-zinc-500 font-medium">暫無趨勢資料<br />請稍後重試</p>
                    </div>
                ) : (
                    <AnimatePresence mode="popLayout">
                        {trending.map((stock, index) => (
                            <motion.button
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: index * 0.03 }}
                                key={stock.symbol}
                                onClick={() => onSelectStock(stock.symbol)}
                                className="w-full p-4 rounded-2xl bg-zinc-900/60 border border-white/5 hover:border-primary/40 hover:bg-primary/5 transition-all group flex items-center justify-between text-left shadow-sm hover:shadow-primary/5"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="flex flex-col">
                                        <span className="text-xs font-mono font-bold text-primary tracking-tight">{stock.symbol}</span>
                                        <span className="text-xs text-zinc-400 font-medium truncate max-w-[140px] leading-tight mt-0.5">{stock.description}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-5">
                                    <div className="text-right">
                                        <div className="text-xs font-bold text-zinc-100 font-mono tracking-tighter">{stock.price > 0 ? stock.price.toFixed(2) : "--"}</div>
                                        <div className={cn("text-[11px] font-bold", (stock.changePercent || 0) >= 0 ? "text-emerald-400" : "text-rose-400")}>
                                            {(stock.changePercent || 0) >= 0 ? "+" : ""}{(stock.changePercent || 0).toFixed(2)}%
                                        </div>
                                    </div>
                                    <ChevronRight className="h-4 w-4 text-zinc-700 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                </div>
                            </motion.button>
                        ))}
                    </AnimatePresence>
                )}
            </div>

            <div className="p-3.5 border-t border-white/5 bg-black/40 flex justify-between items-center px-5">
                <div className="flex items-center gap-1.5 grayscale opacity-70">
                    <Activity className="h-3 w-3 text-emerald-500 animate-pulse" />
                    <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">Live Feed</span>
                </div>
                <span className="text-[9px] text-zinc-600 font-bold font-mono">
                    SENTINEL-SYNC: {lastUpdated.toLocaleTimeString([], { hour12: false })}
                </span>
            </div>
        </div>
    )
}
