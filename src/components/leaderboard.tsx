"use client"

import { useEffect, useState } from 'react'
import { Trophy, TrendingUp, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'

interface LeaderboardItem {
    nickname: string
    symbol: string
    return: number
    date: string
}

export function Leaderboard() {
    const [items, setItems] = useState<LeaderboardItem[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // In real dev, this URL needs to be dynamic or env based
        const fetchLeaderboard = async () => {
            try {
                const res = await fetch('/api/leaderboard?leaderboard=true')
                const data = await res.json()
                if (Array.isArray(data)) {
                    setItems(data)
                }
            } catch (e) {
                console.error(e)
            } finally {
                setLoading(false)
            }
        }
        fetchLeaderboard()
    }, [])

    if (loading) return <div className="animate-pulse h-48 bg-card/30 rounded-2xl"></div>

    return (
        <div className="rounded-3xl border border-yellow-500/20 bg-gradient-to-b from-yellow-500/5 to-transparent p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Trophy className="w-32 h-32" />
            </div>

            <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 text-yellow-500">
                <Trophy className="h-6 w-6" /> 操盤手排行榜 (Beta)
            </h2>

            <div className="space-y-3">
                {items.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">
                        尚無紀錄，快來成為第一位操盤手！
                    </div>
                ) : (
                    items.map((item, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="flex items-center justify-between p-3 rounded-xl bg-background/40 border border-white/5 hover:bg-background/60 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${idx < 3 ? 'bg-yellow-500 text-black' : 'bg-muted text-muted-foreground'}`}>
                                    {idx + 1}
                                </span>
                                <div className="flex flex-col">
                                    <span className="font-bold text-sm text-foreground/90">{item.nickname}</span>
                                    <span className="text-xs text-muted-foreground">買進 {item.symbol}</span>
                                </div>
                            </div>
                            <div className={`flex items-center gap-1 font-mono font-bold ${item.return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {item.return >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {item.return.toFixed(2)}%
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    )
}
