"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Brain, Zap, History, ChevronRight, Activity, Target } from "lucide-react"
import { AI_RadarChart } from "./ui/radar-chart"
import { cn } from "@/lib/utils"

interface EvolutionState {
    version: string
    last_updated: string
    strategies: {
        [key: string]: {
            name: string
            description: string
            weights: { [key: string]: number }
            performance_history: any[]
        }
    }
}

export function EvolutionDashboard() {
    const [state, setState] = useState<EvolutionState | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchState = async () => {
            try {
                const res = await fetch('/api/evolution')
                const data = await res.json()
                setState(data)
            } catch (e) {
                console.error("Failed to fetch evolution state", e)
            } finally {
                setLoading(false)
            }
        }
        fetchState()
        const interval = setInterval(fetchState, 30000) // 30s auto-refresh
        return () => clearInterval(interval)
    }, [])

    if (loading) return null

    const mainStrategy = state?.strategies?.growth_value
    if (!mainStrategy) return null

    // Transform weights for radar chart to match RadarDataPoint interface
    const radarData = Object.entries(mainStrategy.weights).map(([key, value]) => ({
        subject: key.replace('_', ' ').toUpperCase(),
        A: value * 100,
        fullMark: 100
    }))

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="grid gap-6 lg:grid-cols-2"
        >
            {/* 1. Evolution Core: Strategy Radar */}
            <div className="rounded-[2rem] border border-primary/20 bg-zinc-900/40 p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-700" />

                <div className="flex items-center justify-between mb-8 relative z-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-2xl bg-primary/20 border border-primary/30 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                            <Brain className="h-6 w-6 text-primary animate-pulse" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-zinc-100">AI 自進化核心</h3>
                            <p className="text-xs text-zinc-500 font-medium uppercase tracking-widest mt-0.5">Strategy Version {state.version}</p>
                        </div>
                    </div>
                    <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold flex items-center gap-1.5 animate-pulse">
                        <Activity className="h-3 w-3" /> LIVE EVOLUTION
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center relative z-10">
                    <div className="h-64">
                        <AI_RadarChart data={radarData} />
                    </div>
                    <div className="space-y-4">
                        <div className="p-4 rounded-2xl bg-black/40 border border-white/5">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase block mb-1">當前模型</span>
                            <div className="text-lg font-bold text-primary">{mainStrategy.name}</div>
                            <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{mainStrategy.description}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {Object.entries(mainStrategy.weights).map(([key, val]) => (
                                <div key={key} className="p-3 rounded-xl bg-zinc-900/60 border border-white/5">
                                    <span className="text-[9px] text-zinc-500 font-bold block truncate">{key.toUpperCase()}</span>
                                    <span className="text-sm font-mono font-bold text-zinc-200">{(val * 100).toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* 2. Evolution Logs */}
            <div className="rounded-[2rem] border border-zinc-800 bg-zinc-900/40 p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden flex flex-col">
                <h3 className="text-lg font-bold flex items-center gap-3 mb-6 relative z-10 text-zinc-100">
                    <History className="h-5 w-5 text-zinc-400" /> 近期進化日誌
                </h3>

                <div className="flex-1 space-y-4 overflow-y-auto max-h-[300px] pr-2 custom-scrollbar relative z-10">
                    <AnimatePresence mode="popLayout">
                        {mainStrategy.performance_history.length > 0 ? (
                            mainStrategy.performance_history.map((log: any, i: number) => (
                                <motion.div
                                    key={i}
                                    initial={{ x: -10, opacity: 0 }}
                                    animate={{ x: 0, opacity: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="p-4 rounded-2xl bg-black/20 border border-white/5 hover:border-primary/20 transition-colors group/item"
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-[10px] font-mono text-zinc-500">{new Date(log.date).toLocaleDateString()}</span>
                                        <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-md", log.performance.avg_return >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
                                            {log.performance.avg_return >= 0 ? "+" : ""}{(log.performance.avg_return * 100).toFixed(1)}% Return
                                        </span>
                                    </div>
                                    {log.reflections.map((ref: string, j: number) => (
                                        <div key={j} className="flex gap-2 text-xs text-zinc-300 mt-1">
                                            <ChevronRight className="h-3 w-3 mt-0.5 text-primary flex-shrink-0" />
                                            {ref}
                                        </div>
                                    ))}
                                </motion.div>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center py-12 text-zinc-600 grayscale opacity-50">
                                <Zap className="h-12 w-12 mb-4 animate-pulse" />
                                <p className="text-sm font-medium">等待首個 14:30 反思週期...</p>
                                <p className="text-[10px] uppercase mt-1 tracking-widest">Self-Healing Active</p>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    )
}
