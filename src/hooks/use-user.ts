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
            // Generate a random ID if we don't have one (though typically we are registering a NEW user)
            const newId = crypto.randomUUID()

            const res = await fetch('/api/index', {
                method: 'POST',
                body: JSON.stringify({
                    action: 'register_user',
                    nickname,
                    id: newId
                })
            })
            const data = await res.json()

            if (data.status === 'success' && data.user) {
                localStorage.setItem('tw_stock_user', JSON.stringify(data.user))
                setUser(data.user)
                toast.success(`歡迎回來, ${data.user.nickname}!`)
                return data.user
            } else if (data.error) {
                throw new Error(data.error)
            }
        } catch (e) {
            console.error(e)
            toast.error("註冊失敗: " + String(e))
        }
        return null
    }

    return { user, loading, register }
}
