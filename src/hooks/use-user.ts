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

    const loginWithId = async (id: string) => {
        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                body: JSON.stringify({
                    action: 'register_user',
                    id,
                    nickname: 'Recovered User' // Backend will handle if user exists
                })
            })
            const data = await res.json()

            if (data.status === 'success' && data.user) {
                localStorage.setItem('tw_stock_user', JSON.stringify(data.user))
                setUser(data.user)
                toast.success(`帳號恢復成功, ${data.user.nickname}!`)
                return data.user
            } else {
                throw new Error(data.error || "找不到該帳號")
            }
        } catch (e) {
            console.error(e)
            toast.error("恢復失敗: " + String(e))
            return null
        }
    }

    const fetchUsers = async () => {
        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                body: JSON.stringify({ action: 'list_users' })
            })
            const data = await res.json()
            if (data.status === 'success') {
                return data.users as { id: string, nickname: string }[]
            }
        } catch (e) {
            console.error("Failed to fetch users:", e)
        }
        return []
    }

    return { user, loading, register, loginWithId, fetchUsers }
}
