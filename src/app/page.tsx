"use client"

import { useState, useEffect } from "react"
import { Search } from "lucide-react"
import { StockDashboard } from "@/components/stock-dashboard"
import { Leaderboard } from "@/components/leaderboard"
import { useUser } from "@/hooks/use-user"

export default function Home() {
    const [query, setQuery] = useState("")
    const [stockData, setStockData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const { user, register } = useUser()

    const searchStock = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query) return

        setLoading(true)
        setError(null)
        setStockData(null)

        try {
            const res = await fetch(`http://127.0.0.1:8000?symbol=${encodeURIComponent(query)}`)
            if (!res.ok) throw new Error("API Error")
            const data = await res.json()
            if (data.error) throw new Error(data.error)
            setStockData(data)
        } catch (err) {
            setError("無法取得資料，請檢查代號是否正確")
        } finally {
            setLoading(false)
        }
    }

    // Auto-fetch 2330 on mount
    useEffect(() => {
        setQuery("2330")
        const fetchInitial = async () => {
            setLoading(true)
            try {
                const res = await fetch(`http://127.0.0.1:8000?symbol=2330`)
                if (!res.ok) throw new Error("API Error")
                const data = await res.json()
                if (data.error) throw new Error(data.error)
                setStockData(data)
            } catch (err) {
                console.error("Initial fetch failed", err)
            } finally {
                setLoading(false)
            }
        }
        fetchInitial()
    }, [])

    return (
        <main className="min-h-screen bg-black text-white selection:bg-primary selection:text-primary-foreground">


            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

            <div className="container mx-auto px-4 py-12 max-w-5xl relative">
                <header className="mb-12 text-center space-y-4">
                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-gradient-to-br from-white to-zinc-500 bg-clip-text text-transparent">
                        TwStock<span className="text-primary glow-text">Vision</span>
                    </h1>
                    <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
                        AI 驅動的台股/美股視覺化分析儀表板
                    </p>
                </header>

                {/* Search Bar */}
                <form onSubmit={searchStock} className="relative max-w-2xl mx-auto mb-16 group">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                    <div className="relative z-10 flex items-center">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="輸入代號 (e.g., 2330, TSLA)..."
                            className="w-full bg-zinc-900/80 border border-zinc-800 rounded-full px-6 py-4 pl-14 text-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-2xl"
                        />
                        <Search className="absolute left-5 text-zinc-500 w-6 h-6" />
                        <button
                            type="submit"
                            disabled={loading}
                            className="absolute right-3 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-full font-bold transition-all disabled:opacity-50"
                        >
                            {loading ? "分析中..." : "分析"}
                        </button>
                    </div>
                </form>

                {/* Main Content Area */}
                <div className="grid gap-12 lg:grid-cols-[1fr_300px]">

                    {/* Left: Stock Dashboard */}
                    <div className="min-h-[500px]">
                        <StockDashboard data={stockData} loading={loading} error={error} />
                    </div>

                    {/* Right: Leaderboard */}
                    <div className="space-y-6">
                        <Leaderboard />

                        {/* User Profile Card (Mini) */}
                        {user && (
                            <div className="p-4 rounded-2xl bg-zinc-900/50 border border-zinc-800">
                                <div className="text-xs text-zinc-500 uppercase font-bold mb-2">My Profile</div>
                                <div className="font-bold text-lg">{user.nickname}</div>
                                <div className="text-xs text-zinc-400 mt-1">ID: {user.id.slice(0, 8)}...</div>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </main>
    )
}
