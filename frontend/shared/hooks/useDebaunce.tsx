import { useEffect, useRef } from 'react'

export const useDebaunce = (time: number) => {
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  function debaunce(cb: () => void) {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      cb()
      timerRef.current = null
    }, time)
  }

  return debaunce
}
