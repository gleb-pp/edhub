import { Button } from '@/shared/ui/button/button'
import clsx from 'clsx'
import { Bell, MessageSquareText, Search } from 'lucide-react'
import React from 'react'
import Image from 'next/image'
import { Modal } from '@/shared/ui/modal/modal'
import { SearchButton } from './search/search-button'

interface Props {
  className?: string
}

export const Header: React.FC<Props> = ({ className }) => {
  return (
    <header
      className={clsx(
        'flex items-center justify-between px-6 w-full h-20 text-dark bg-white border-b border-outline shadow-xs',
        className,
      )}
    >
      <p className="text-3xl font-light">Hi, Timur Farizunov</p>
      <div className="flex items-center h-full py-5">
        <SearchButton />

        <div className="mx-5 w-[1px] h-full bg-outline" />

        <div className="flex items-center gap-3 h-full">
          <Button
            className="aspect-square h-full text-dark/80 rounded-md transition-colors hover:text-dark"
            variant="outline"
          >
            <MessageSquareText size={20} />
          </Button>
          <Button
            className="aspect-square h-full text-dark/80 rounded-md transition-colors hover:text-dark"
            variant="outline"
          >
            <Bell size={20} />
          </Button>
          <Button className="aspect-square h-full rounded-md" variant="clean">
            <Image
              className="aspect-square h-full rounded-full shadow-md"
              height={44}
              width={44}
              src={'/userIcon.png'}
              alt={'user'}
            ></Image>
          </Button>
        </div>
      </div>
    </header>
  )
}
