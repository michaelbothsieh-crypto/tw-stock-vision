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
                    <div className="text-center md:text-left space-y-2">
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl text-foreground/90">
                            市場概況
                        </h1>
                        <p className="text-muted-foreground text-lg max-w-[600px]">
                            台灣股市即時洞察
                        </p>
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
