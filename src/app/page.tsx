"use client"

import { useState } from "react"
import { StockSearch } from "@/components/stock-search"
import { StockDashboard } from "@/components/stock-dashboard"

export default function Home() {
    const [symbol, setSymbol] = useState<string | null>(null)
    const [data, setData] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSearch = async (query: string) => {
        setSymbol(query)
        setLoading(true)
        setError(null)
        setData(null)

        try {
            // Fetch data from our Python API
            // Note: In development without 'vercel dev', this will 404 if hitting /api directly.
            // We need a way to mock or proxy. 
            // For now, let's assume it works and implement the fetch.
            // If deployed or running with 'vercel dev', this works.
            const res = await fetch(`/api?symbol=${query}`)
            if (!res.ok) throw new Error("Failed to fetch data")

            const json = await res.json()
            if (json.error) throw new Error(json.error)

            // Transform API response to UI model if needed
            // Currently our API returns basic info, we might need to mock detailed data 
            // until the backend is fully fleshed out.

            // Real data only
            setData(json)

        } catch (err) {
            setError(err instanceof Error ? err.message : "An unknown error occurred")
        } finally {
            setLoading(false)
        }
    }

    // Auto-load 2330 on mount if no data
    if (!data && !loading && !error && !symbol) {
        handleSearch("2330")
    }

    return (
        <main className="min-h-screen bg-background text-foreground selection:bg-primary/20">
            {/* Background Gradients */}
            <div className="fixed inset-0 -z-10 h-full w-full bg-background">
                <div className="absolute top-0 -left-4 w-72 h-72 bg-primary/20 rounded-full mix-blend-screen filter blur-[128px] opacity-50 shadow-2xl animate-pulse" />
                <div className="absolute top-0 -right-4 w-72 h-72 bg-accent/20 rounded-full mix-blend-screen filter blur-[128px] opacity-50 shadow-2xl animate-pulse delay-1000" />
            </div>

            {/* Navbar */}
            <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
                <div className="container px-4 md:px-8 h-16 flex items-center justify-between mx-auto max-w-7xl">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                            <span className="font-bold text-white">TW</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
                            TwStockVision
                        </span>
                    </div>
                </div>
            </nav>

            <div className="container mx-auto max-w-7xl px-4 md:px-8 py-8 space-y-8">
                {/* Search Header */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 py-8">
                    <div className="text-center md:text-left space-y-4">
                        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl text-foreground/90">
                            TwStockVision <span className="text-primary">智能股市視野</span>
                        </h1>
                        <div className="text-muted-foreground text-lg max-w-[650px] leading-relaxed">
                            <p className="mb-2">專為現代投資人打造的 <span className="font-semibold text-foreground">SMC 聰明錢</span> 技術分析儀表板。</p>
                            <ul className="grid gap-2 text-base mt-4 border-l-2 border-primary/30 pl-4">
                                <li>🤖 <b>AI 輔助解讀</b>：一秒看懂多空趨勢，不再被 K 線圖淹沒。</li>
                                <li>⚡ <b>SMC 主力籌碼</b>：即時追蹤資金流向 (RVOL) 與機構佈局。</li>
                                <li>🎯 <b>目標價運算</b>：整合分析師預期與技術位階，提供進出參考。</li>
                            </ul>
                        </div>
                    </div>
                    <div className="w-full md:w-auto">
                        <StockSearch onSearch={handleSearch} className="md:w-[400px] shadow-lg" />
                    </div>
                </div>

                {/* Dashboard Content */}
                <StockDashboard data={data} loading={loading} error={error} />
            </div>
        </main>
    )
}
