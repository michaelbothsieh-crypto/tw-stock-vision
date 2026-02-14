"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, User, Trash2, Edit2, Check, Save } from "lucide-react"
import { useUser } from "@/hooks/use-user"
import { toast } from "sonner"

interface PortfolioItem {
    id: string
    symbol: string
    entry_price: number | string
    entry_date: string
    current_price: string | null
}

interface PortfolioManagerProps {
    isOpen: boolean
    onClose: () => void
}

export function PortfolioManager({ isOpen, onClose }: PortfolioManagerProps) {
    const { user, register } = useUser()
    const [items, setItems] = useState<PortfolioItem[]>([])
    const [loading, setLoading] = useState(true)
    const [editingNickname, setEditingNickname] = useState(false)
    const [tempNickname, setTempNickname] = useState(user?.nickname || "")
    const [editingPriceId, setEditingPriceId] = useState<string | null>(null)
    const [tempPrice, setTempPrice] = useState<string>("")

    const fetchUserPortfolio = async () => {
        if (!user) return
        try {
            const res = await fetch("/api/index", {
                method: "POST",
                body: JSON.stringify({ action: "get_portfolio", user_id: user.id }),
            })
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

    useEffect(() => {
        if (isOpen) {
            fetchUserPortfolio()
            setTempNickname(user?.nickname || "")
        }
    }, [isOpen, user])

    const handleUpdateNickname = async () => {
        if (!user || !tempNickname.trim()) return
        try {
            const res = await fetch("/api/index", {
                method: "POST",
                body: JSON.stringify({
                    action: "update_nickname",
                    user_id: user.id,
                    nickname: tempNickname.trim(),
                }),
            })
            const result = await res.json()
            if (result.status === "success") {
                toast.success("暱稱已更新")
                setEditingNickname(false)
                // Refresh local user state if register() handles it, 
                // but here we might need to manually update local storage or just reload
                const updatedUser = { ...user, nickname: tempNickname.trim() }
                localStorage.setItem("tw_stock_user", JSON.stringify(updatedUser))
                window.dispatchEvent(new Event("refresh-leaderboard"))
            }
        } catch (e) {
            toast.error("更新失敗")
        }
    }

    const handleDelete = async (id: string) => {
        if (!user) return
        if (!confirm("確定要刪除這筆紀錄嗎？")) return

        try {
            const res = await fetch("/api/index", {
                method: "POST",
                body: JSON.stringify({
                    action: "delete_portfolio",
                    user_id: user.id,
                    portfolio_id: id,
                }),
            })
            const result = await res.json()
            if (result.status === "success") {
                toast.success("已刪除")
                fetchUserPortfolio()
                window.dispatchEvent(new Event("refresh-leaderboard"))
            }
        } catch (e) {
            toast.error("刪除失敗")
        }
    }

    const handleUpdatePrice = async (id: string) => {
        if (!user || !tempPrice) return
        try {
            const res = await fetch("/api/index", {
                method: "POST",
                body: JSON.stringify({
                    action: "update_portfolio_price",
                    user_id: user.id,
                    portfolio_id: id,
                    price: parseFloat(tempPrice),
                }),
            })
            const result = await res.json()
            if (result.status === "success") {
                toast.success("價格已修訂")
                setEditingPriceId(null)
                fetchUserPortfolio()
                window.dispatchEvent(new Event("refresh-leaderboard"))
            }
        } catch (e) {
            toast.error("修訂失敗")
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-xl bg-zinc-950 border border-white/10 rounded-3xl shadow-2xl overflow-hidden"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-gradient-to-r from-yellow-500/10 to-transparent">
                            <div>
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <User className="h-5 w-5 text-yellow-500" /> 個人自選管理
                                </h2>
                                <p className="text-xs text-zinc-500 mt-1">修改您的暱稱或自選股入路成本</p>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                                <X className="h-5 w-5 text-zinc-400" />
                            </button>
                        </div>

                        <div className="p-6 max-h-[70vh] overflow-y-auto space-y-8">
                            {/* Nickname Section */}
                            <section className="space-y-3">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">我的顯示暱稱</label>
                                <div className="flex items-center gap-2">
                                    {editingNickname ? (
                                        <>
                                            <input
                                                type="text"
                                                value={tempNickname}
                                                onChange={(e) => setTempNickname(e.target.value)}
                                                className="flex-1 bg-zinc-900 border border-yellow-500/50 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 ring-yellow-500/20"
                                                placeholder="輸入新暱稱"
                                            />
                                            <button onClick={handleUpdateNickname} className="p-2.5 bg-yellow-500 text-black rounded-xl hover:bg-yellow-400">
                                                <Save className="h-5 w-5" />
                                            </button>
                                            <button onClick={() => setEditingNickname(false)} className="p-2.5 bg-zinc-800 text-zinc-400 rounded-xl">
                                                <X className="h-5 w-5" />
                                            </button>
                                        </>
                                    ) : (
                                        <div className="flex-1 bg-zinc-900/50 border border-white/5 rounded-xl px-4 py-3 flex items-center justify-between group">
                                            <span className="font-bold text-zinc-100">{user?.nickname}</span>
                                            <button onClick={() => setEditingNickname(true)} className="p-1.5 opacity-0 group-hover:opacity-100 transition-opacity hover:text-yellow-500">
                                                <Edit2 className="h-4 w-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </section>

                            {/* Portfolio Section */}
                            <section className="space-y-4">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">我的自選清單 ({items.length})</label>
                                <div className="space-y-2">
                                    {loading ? (
                                        <div className="py-12 flex justify-center">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
                                        </div>
                                    ) : items.length === 0 ? (
                                        <div className="text-center py-12 bg-white/5 rounded-2xl border border-dashed border-white/10">
                                            <p className="text-sm text-zinc-500">尚無自選股</p>
                                        </div>
                                    ) : (
                                        items.map((item) => (
                                            <div key={item.id} className="bg-zinc-900/40 border border-white/5 p-4 rounded-2xl group hover:border-white/10 transition-colors">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <div className="bg-primary/10 text-primary px-2.5 py-1 rounded font-mono font-bold text-xs uppercase">
                                                            {item.symbol}
                                                        </div>
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] text-zinc-500">入路日期: {new Date(item.entry_date).toLocaleDateString()}</span>
                                                        </div>
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        {editingPriceId === item.id ? (
                                                            <div className="flex items-center gap-1">
                                                                <input
                                                                    type="number"
                                                                    value={tempPrice}
                                                                    onChange={(e) => setTempPrice(e.target.value)}
                                                                    className="w-20 bg-zinc-950 border border-yellow-500/50 rounded-lg px-2 py-1 text-xs font-mono focus:outline-none"
                                                                />
                                                                <button onClick={() => handleUpdatePrice(item.id)} className="p-1 text-green-500 hover:bg-green-500/10 rounded">
                                                                    <Check className="h-4 w-4" />
                                                                </button>
                                                                <button onClick={() => setEditingPriceId(null)} className="p-1 text-zinc-500 hover:bg-white/5 rounded">
                                                                    <X className="h-4 w-4" />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <div className="flex items-center gap-3">
                                                                <div className="text-right">
                                                                    <div className="text-[9px] text-zinc-600 font-bold uppercase">持有價</div>
                                                                    <div className="text-sm font-mono font-bold text-zinc-300">${item.entry_price}</div>
                                                                </div>
                                                                <button
                                                                    onClick={() => {
                                                                        setEditingPriceId(item.id)
                                                                        setTempPrice(String(item.entry_price))
                                                                    }}
                                                                    className="p-2 opacity-0 group-hover:opacity-100 transition-opacity hover:text-yellow-500"
                                                                >
                                                                    <Edit2 className="h-3.5 w-3.5" />
                                                                </button>
                                                                <button
                                                                    onClick={() => handleDelete(item.id)}
                                                                    className="p-2 opacity-0 group-hover:opacity-100 transition-opacity hover:text-rose-500"
                                                                >
                                                                    <Trash2 className="h-3.5 w-3.5" />
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </section>
                        </div>

                        <div className="p-6 bg-zinc-900/50 border-t border-white/5 text-center">
                            <p className="text-[10px] text-zinc-600 italic">所有更動將即時反映在操盤手排行榜中</p>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
