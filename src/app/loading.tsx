export default function Loading() {
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
                </div>

                {/* Middle: Metrics Skeleton */}
                <div className="w-4/12 border-r border-white/10 bg-zinc-950/30 p-6 space-y-6">
                    <div className="h-8 w-32 bg-zinc-800/50 rounded animate-pulse" />
                    <div className="grid grid-cols-2 gap-4">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-24 rounded-xl bg-zinc-800/20 animate-pulse" />
                        ))}
                    </div>
                </div>

                {/* Right: List Skeleton */}
                <div className="w-3/12 bg-zinc-950/50 p-2 space-y-2 overflow-hidden">
                    {[...Array(12)].map((_, i) => (
                        <div key={i} className="h-14 rounded-lg bg-zinc-800/10 border border-white/5 flex items-center px-3 gap-3 animate-pulse" />
                    ))}
                </div>
            </div>

            <div className="h-64 border-t border-white/5 bg-zinc-950/20 p-6">
                <div className="h-full w-full rounded-2xl bg-zinc-800/10 border border-white/5 animate-pulse" />
            </div>
        </div>
    )
}
