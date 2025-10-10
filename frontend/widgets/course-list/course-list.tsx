import clsx from 'clsx'
import React from 'react'
import { CourseItem } from '../course-item/ui/course-item'

interface Props {
  className?: string
}

export const CourseList: React.FC<Props> = ({ className }) => {
  return (
    <div
      className={clsx('flex flex-col flex-1 overflow-y-auto p-6', className)}
    >
      <div className="mx-auto w-[1442px]">
        <h1 className="text-3xl font-medium text-dark mb-6">Course list</h1>
        <div className={clsx('grid gap-6 auto-rows-min grid-cols-3')}>
          {/* <CourseItem /> */}
          {Array.from({ length: 30 }).map((_, i) => (
            <CourseItem key={i} />
          ))}
        </div>
      </div>
    </div>
  )
}
