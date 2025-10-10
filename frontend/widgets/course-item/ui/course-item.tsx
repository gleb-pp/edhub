import { Button } from '@/shared/ui/button/button'
import { Card } from '@/shared/ui/card/card'
import { ProgressBar } from '@/shared/ui/progress'
import clsx from 'clsx'
import { Archive, ArrowRight, Star, User, Users } from 'lucide-react'
import React from 'react'

interface Props {
  className?: string
  course_id: string
  title: string
  instructor: string
  organization: string
  creation_time: string
}

export const CourseItem: React.FC<Props> = ({ className }) => {
  return (
    <Card
      className={clsx(
        'h-[270px] w-[460px] flex flex-col transition-all duration-300 hover:shadow-lg hover:border-dark/15',
        className,
      )}
    >
      <div className="flex items-center gap-4 pt-8 px-8">
        <div className="size-[50px] bg-zinc-200" />
        <p className="text-4xl text-dark font-medium">Networks</p>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-3 px-8 text-dark/60 text-lg">
        <div className="flex items-center gap-3">
          <User size={22} strokeWidth={1.6} />
          <p className="font-light">Artyom Burmyakov</p>
        </div>
        <div className="flex items-center gap-3">
          <Users size={22} strokeWidth={1.6} />
          <p className="font-light">Innopolis University</p>
        </div>
      </div>

      <div className="relative w-full p-[14px] pl-8 flex items-center justify-between bg-dark/2 rounded-b-xl">
        <div className="absolute left-0 top-[-2px] h-[2px] w-full">
          <ProgressBar
            className="bg-dark w-full h-full"
            value={80}
            maxValue={100}
          />
        </div>
        <div className="flex items-center gap-3">
          <Button
            className="text-dark/70 transition-colors duration-200 hover:text-dark"
            variant="clean"
          >
            <Star strokeWidth={1.8} />
          </Button>
          <Button
            className="text-dark/70 transition-colors duration-200 hover:text-dark"
            variant="clean"
          >
            <Archive strokeWidth={1.6} />
          </Button>
        </div>
        <Button className="px-4 py-2 rounded-lg !bg-dark/95 hover:!bg-dark/85">
          Continue{' '}
          <ArrowRight className="ml-2" size={18} strokeWidth={1.8}></ArrowRight>
        </Button>
      </div>
    </Card>
  )
}
