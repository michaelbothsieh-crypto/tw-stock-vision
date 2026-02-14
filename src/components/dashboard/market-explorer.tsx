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
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

    const fetchTrending = async () => {
        setLoading(true)
        try {
            const res = await fetch("/api/market/trending")
            const data = await res.json()
            if (Array.isArray(data)) {
                setTrending(data)
                setLastUpdated(new Date())
            }
        } catch (error) {
            console.error("Failed to fetch trending:", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchTrending()
        const interval = setInterval(fetchTrending, 300000) // 5 min auto refresh
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900/30 backdrop-blur-md overflow-hidden flex flex-col h-full border-t-0 border-l-0 shadow-2xl">
            <div className="p-5 border-b border-white/5 flex items-center justify-between bg-gradient-to-r from-zinc-900/80 to-transparent">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                        <TrendingUp className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-zinc-200">市場發現 (AI Explorer)</h3>
                        <p className="text-[10px] text-zinc-500 uppercase tracking-tighter">按技術強度與動能排序</p>
                    </div>
                </div>
                <button
                    onClick={fetchTrending}
                    disabled={loading}
                    className="p-2 hover:bg-zinc-800 rounded-full transition-colors group"
                >
                    <RefreshCcw className={cn("h-4 w-4 text-zinc-500 group-hover:text-primary transition-all", loading && "animate-spin")} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
                {loading && trending.length === 0 ? (
                    Array(5).fill(0).map((_, i) => (
                        <div key={i} className="h-16 w-full bg-zinc-800/20 animate-pulse rounded-2xl border border-white/5" />
                    ))
                ) : (
                    <AnimatePresence mode="popLayout">
                        {trending.map((stock, index) => (
                            <motion.button
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.05 }}
                                key={stock.symbol}
                                onClick={() => onSelectStock(stock.symbol)}
                                className="w-full p-4 rounded-2xl bg-zinc-900/40 border border-white/5 hover:border-primary/30 hover:bg-primary/5 transition-all group flex items-center justify-between text-left"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="flex flex-col">
                                        <span className="text-xs font-mono font-bold text-primary">{stock.symbol}</span>
                                        <span className="text-[10px] text-zinc-400 font-medium truncate max-w-[120px]">{stock.description}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <div className="text-xs font-semibold text-zinc-200">${stock.price.toFixed(2)}</div>
                                        <div className={cn("text-[10px] font-bold", stock.changePercent >= 0 ? "text-emerald-400" : "text-rose-400")}>
                                            {stock.changePercent >= 0 ? "+" : ""}{stock.changePercent.toFixed(2)}%
                                        </div>
                                    </div>
                                    <ChevronRight className="h-4 w-4 text-zinc-700 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                </div>
                            </motion.button>
                        ))}
                    </AnimatePresence>
                )}
            </div>

            <div className="p-3 border-t border-white/5 bg-black/20 flex justify-between items-center">
                <div className="flex items-center gap-1.5 opacity-50">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[9px] text-zinc-400 uppercase">Live Market Data</span>
                </div>
                <span className="text-[9px] text-zinc-600 font-mono">
                    LAST UPDATE: {lastUpdated.toLocaleTimeString()}
                </span>
            </div>
        </div>
    )
}
