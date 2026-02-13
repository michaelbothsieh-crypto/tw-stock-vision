"use client"

import * as React from "react"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

export interface SearchProps extends React.InputHTMLAttributes<HTMLInputElement> {
    onSearch: (value: string) => void
}

const StockSearch = React.forwardRef<HTMLInputElement, SearchProps>(
    ({ className, onSearch, ...props }, ref) => {
        const [value, setValue] = React.useState("")

        const handleSubmit = (e: React.FormEvent) => {
            e.preventDefault()
            onSearch(value)
        }

        return (
            <form onSubmit={handleSubmit} className={cn("relative w-full max-w-lg group", className)}>
                <div className="absolute inset-0 -z-10 rounded-xl bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 opacity-0 blur-xl transition-opacity duration-500 group-focus-within:opacity-100" />
                <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <input
                    className={cn(
                        "flex h-12 w-full rounded-xl border border-input/50 bg-background/50 px-4 py-2 pl-11 text-base shadow-sm backdrop-blur-md transition-all placeholder:text-muted-foreground hover:bg-background/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:bg-background",
                        className
                    )}
                    ref={ref}
                    placeholder="輸入股票代號 (例如 2330)"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    {...props}
                />
            </form>
        )
    }
)
StockSearch.displayName = "StockSearch"

export { StockSearch }
