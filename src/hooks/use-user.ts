"use client"

import { useState, useEffect } from 'react'
import { toast } from 'sonner'

export function useUser() {
    const [user, setUser] = useState<{ id: string, nickname: string } | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const storedUser = localStorage.getItem('tw_stock_user')
        if (storedUser) {
            setUser(JSON.parse(storedUser))
        }
        setLoading(false)
    }, [])

    const register = async (nickname: string) => {
        try {
            const res = await fetch('http://127.0.0.1:8000', {
                method: 'POST',
                body: JSON.stringify({ action: 'register', nickname })
            })
            const data = await res.json()
            if (data.id) {
                localStorage.setItem('tw_stock_user', JSON.stringify(data))
                setUser(data)
                toast.success(`歡迎回來, ${data.nickname}!`)
                return true
            }
        } catch (e) {
            console.error(e)
            toast.error("註冊失敗，請稍後再試")
        }
        return false
    }

    return { user, loading, register }
}
