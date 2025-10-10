'use client'
import { Button } from '@/shared/ui/button/button'

import { Search } from 'lucide-react'
import React, { useState } from 'react'
import { SearchModal } from './search-modal'

export const SearchButton = () => {
  const [isOpen, setOpen] = useState(false)

  const handleModalOpen = () => {
    setOpen(true)
  }

  const handleModalClose = () => {
    setOpen(false)
  }

  return (
    <>
      <Button
        onClick={handleModalOpen}
        className="h-full w-70 rounded-md justify-start px-3 gap-2 text-dark/50"
        variant="outline"
      >
        <Search size={20} />
        Search here...
      </Button>
      <SearchModal onClose={handleModalClose} isOpen={isOpen} />
    </>
  )
}
