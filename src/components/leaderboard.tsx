"use client"

import { useEffect, useState } from 'react'
import { Trash2, Trophy, TrendingUp, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'
import { useUser } from '@/hooks/use-user'
import { toast } from 'sonner'

interface LeaderboardItem {
    id: string
    user_id: string
    nickname: string
    symbol: string
    return: number
    date: string
    entry_price: number | string
}

export function Leaderboard() {
    const { user } = useUser()
    const [items, setItems] = useState<LeaderboardItem[]>([])
    const [loading, setLoading] = useState(true)
    const [deleting, setDeleting] = useState<string | null>(null)

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

    const handleDelete = async (portfolioId: string) => {
        if (!user || deleting) return
        if (!confirm("確定要刪除這筆追蹤紀錄嗎？")) return

        setDeleting(portfolioId)
        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                body: JSON.stringify({
                    action: 'delete_portfolio',
                    user_id: user.id,
                    portfolio_id: portfolioId
                })
            })
            const result = await res.json()
            if (result.status === 'success') {
                toast.success("紀錄已刪除")
                fetchLeaderboard()
            } else {
                toast.error("刪除失敗: " + (result.error || "未知錯誤"))
            }
        } catch (e) {
            toast.error("連線錯誤")
        } finally {
            setDeleting(null)
        }
    }

    useEffect(() => {
        fetchLeaderboard()

        // Listen for internal refresh events (e.g. from StockDashboard)
        const handleRefresh = () => {
            fetchLeaderboard()
        }
        window.addEventListener('refresh-leaderboard', handleRefresh)
        return () => window.removeEventListener('refresh-leaderboard', handleRefresh)
    }, [])

    const formatTime = (dateStr: string) => {
        try {
            const date = new Date(dateStr)
            return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
        } catch (e) {
            return "-"
        }
    }

    if (loading) return <div className="animate-pulse h-48 bg-card/30 rounded-2xl"></div>

    return (
        <div className="rounded-3xl border border-yellow-500/20 bg-gradient-to-b from-yellow-500/5 to-transparent p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Trophy className="w-32 h-32 text-yellow-500" />
            </div>

            <h2 className="text-xl font-bold flex items-center gap-2 mb-6 text-yellow-500/90">
                <Trophy className="h-5 w-5" /> 操盤手排行榜 (Beta)
            </h2>

            <div className="space-y-4">
                {items.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8 text-sm">
                        尚無紀錄，快來成為第一位操盤手！
                    </div>
                ) : (
                    items.map((item, idx) => {
                        const isOwn = user?.id === item.user_id
                        return (
                            <motion.div
                                key={item.id || idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                className={`group flex flex-col gap-2 p-4 rounded-2xl bg-zinc-900/40 border transition-all duration-300 shadow-lg ${isOwn ? 'border-yellow-500/30' : 'border-white/5'} hover:bg-zinc-800/60 hover:border-yellow-500/20`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${idx === 0 ? 'bg-yellow-500 text-black' : idx === 1 ? 'bg-zinc-300 text-black' : idx === 2 ? 'bg-amber-700 text-white' : 'bg-zinc-800 text-zinc-500'}`}>
                                            {idx + 1}
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="font-bold text-sm text-zinc-100 group-hover:text-white transition-colors">
                                                {item.nickname} {isOwn && <span className="text-[9px] bg-yellow-500/10 text-yellow-500 px-1 rounded ml-1">Me</span>}
                                            </span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-[10px] font-bold text-primary px-1.5 py-0.5 rounded bg-primary/10">{item.symbol}</span>
                                                <span className="text-[10px] text-zinc-500">{formatTime(item.date)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className={`flex items-center gap-1 font-mono font-bold text-sm ${item.return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {item.return >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                            {item.return > 0 ? "+" : ""}{item.return.toFixed(2)}%
                                        </div>
                                        {isOwn && (
                                            <button
                                                onClick={() => handleDelete(item.id)}
                                                disabled={deleting === item.id}
                                                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg bg-rose-500/10 text-rose-500 hover:bg-rose-500 hover:text-white transition-all disabled:opacity-30"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center justify-between pt-2 mt-1 border-t border-white/5">
                                    <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-wider">買進價格</span>
                                    <span className="text-xs font-mono font-bold text-zinc-400">${item.entry_price}</span>
                                </div>
                            </motion.div>
                        )
                    })
                )}
            </div>
        </div>
    )
}
