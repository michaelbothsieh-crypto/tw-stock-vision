'use client'

/**
 * DashboardClient — ISR 橋接層
 *
 * 職責：
 * - 接收 Server Component (page.tsx) 預取的 initialData
 * - 管理市場切換的 client-side 狀態
 * - 市場切換時才發 client-side fetch（TW 首次載入無需等待）
 */

import { useState, useEffect } from 'react'
import { Toaster, toast } from 'sonner'
import { NeoDashboard } from '@/components/Neo/NeoDashboard'

interface DashboardClientProps {
    initialData: any[]
    initialMarket: 'TW' | 'US'
}

function DashboardSkeleton() {
    return (
        <div className="flex h-screen flex-col bg-[#050505] overflow-hidden">
            {/* Header Skeleton */}
            <div className="h-10 border-b border-white/10 bg-black/50 backdrop-blur-md flex items-center px-4 justify-between">
                <div className="flex gap-4">
                    <div className="h-4 w-24 bg-zinc-800/50 rounded animate-pulse" />
                    <div className="h-4 w-32 bg-zinc-800/50 rounded animate-pulse" />
                </div>
                <div className="h-4 w-20 bg-zinc-800/50 rounded animate-pulse" />
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Left: Chart Skeleton */}
                <div className="w-5/12 border-r border-white/10 bg-zinc-900/20 p-4 flex flex-col gap-4">
                    <div className="flex-1 rounded-xl bg-zinc-800/20 animate-pulse relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent skew-x-12 animate-shimmer" />
                    </div>
                    <div className="h-8 flex gap-2">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="h-full w-12 bg-zinc-800/30 rounded animate-pulse" />
                        ))}
                    </div>
                </div>

                {/* Middle: Metrics Skeleton */}
                <div className="w-4/12 border-r border-white/10 bg-zinc-950/30 p-6 space-y-6">
                    <div className="h-8 w-32 bg-zinc-800/50 rounded animate-pulse" />
                    <div className="grid grid-cols-2 gap-4">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-24 rounded-xl bg-zinc-800/20 animate-pulse" />
                        ))}
                    </div>
                    <div className="h-40 rounded-xl bg-zinc-800/20 animate-pulse" />
                </div>

                {/* Right: List Skeleton */}
                <div className="w-3/12 bg-zinc-950/50 p-2 space-y-2 overflow-hidden">
                    {[...Array(12)].map((_, i) => (
                        <div key={i} className="h-14 rounded-lg bg-zinc-800/10 border border-white/5 flex items-center px-3 gap-3 animate-pulse delay-[${i * 50}ms]">
                            <div className="h-8 w-8 rounded bg-zinc-800/50" />
                            <div className="flex-1 space-y-2">
                                <div className="h-3 w-16 bg-zinc-800/50 rounded" />
                                <div className="h-2 w-24 bg-zinc-800/30 rounded" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Bottom: Evolution Skeleton */}
            <div className="h-64 border-t border-white/5 bg-zinc-950/20 p-6">
                <div className="h-full w-full rounded-2xl bg-zinc-800/10 border border-white/5 animate-pulse" />
            </div>
        </div>
    )
}

export function DashboardClient({ initialData, initialMarket }: DashboardClientProps) {
    const [data, setData] = useState<any[]>(initialData)
    const [market, setMarket] = useState<'TW' | 'US'>(initialMarket)
    const [selectedSymbol, setSelectedSymbol] = useState<string>(
        initialData.length > 0 ? initialData[0].symbol : ''
    )
    const [loading, setLoading] = useState(false)

    // 市場切換時才發 client-side fetch（TW 首次載入已由 SSR 預取，無需等待）
    useEffect(() => {
        if (market === initialMarket && data.length > 0) return  // TW 已有 SSR 資料

        const fetchTrending = async () => {
            try {
                setLoading(true)
                const res = await fetch(`/api/stock?trending=true&market=${market}`)
                if (!res.ok) throw new Error('Failed to fetch trending data')
                const fetchedData = await res.json()

                if (Array.isArray(fetchedData)) {
                    setData(fetchedData)
                    if (fetchedData.length > 0) {
                        setSelectedSymbol(fetchedData[0].symbol)
                    }
                } else {
                    setData([])
                }
            } catch (error) {
                console.error('Failed to fetch market data:', error)
                toast.error('市場數據載入失敗', {
                    description: '請檢查網路連線。',
                })
            } finally {
                setLoading(false)
            }
        }

        fetchTrending()
    }, [market]) // eslint-disable-line react-hooks/exhaustive-deps

    const handleSelectStock = (symbol: string) => {
        setSelectedSymbol(symbol)
    }

    if (loading) {
        return <DashboardSkeleton />
    }

    return (
        <>
            <Toaster theme="dark" position="top-right" />
            <NeoDashboard
                data={data}
                currentSymbol={selectedSymbol}
                onSelect={handleSelectStock}
                market={market}
                onMarketChange={setMarket}
            />
        </>
    )
}
