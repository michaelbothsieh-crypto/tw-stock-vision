'use client'

import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { Toaster, toast } from 'sonner'
import { NeoDashboard } from '@/components/Neo/NeoDashboard';

export default function Home() {
    const [data, setData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedSymbol, setSelectedSymbol] = useState<string>("")
    const [market, setMarket] = useState<'TW' | 'US'>('TW')

    // Fetch trending stocks based on selected market
    useEffect(() => {
        const fetchTrending = async () => {
            try {
                setLoading(true)
                const res = await fetch(`/api/stock?trending=true&market=${market}`)
                if (!res.ok) throw new Error('Failed to fetch trending data')
                const fetchedData = await res.json()

                if (Array.isArray(fetchedData)) {
                    setData(fetchedData)
                    if (fetchedData.length > 0) {
                        setSelectedSymbol(fetchedData[0].symbol);
                    }
                } else {
                    console.error("API returned non-array:", fetchedData)
                    setData([])
                }
            } catch (error) {
                console.error("Failed to boot system:", error)
                toast.error("系統連線失敗 (System Offline)", {
                    description: "無法取得市場數據，請檢查連線。",
                })
            } finally {
                setLoading(false)
            }
        }
        fetchTrending()
    }, [market])

    const handleSelectStock = (symbol: string) => {
        setSelectedSymbol(symbol);
    };

    return (
        <main className="fixed inset-0 overflow-hidden bg-[#050505] text-white font-sans">
            <Toaster theme="dark" position="top-right" />

            {loading ? (
                <div className="flex h-full flex-col items-center justify-center space-y-4 font-mono text-emerald-500">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-zinc-800">
                        <div className="h-full w-full animate-progress-indeterminate bg-emerald-500" />
                    </div>
                    <p className="animate-pulse text-sm">市場數據初始化中 (INITIALIZING)...</p>
                </div>
            ) : (
                <NeoDashboard
                    data={data}
                    currentSymbol={selectedSymbol}
                    onSelect={handleSelectStock}
                    market={market}
                    onMarketChange={setMarket}
                />
            )}
        </main>
    )
}
