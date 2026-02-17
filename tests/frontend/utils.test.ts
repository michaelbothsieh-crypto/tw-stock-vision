import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('utils.ts', () => {
    describe('cn', () => {
        it('should merge classes correctly', () => {
            expect(cn('a', 'b')).toBe('a b')
            expect(cn('a', { b: true, c: false })).toBe('a b')
            expect(cn('p-4', 'p-2')).toBe('p-2') // Tailwind merge behavior
        })
    })
})
