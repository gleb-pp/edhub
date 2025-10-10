import { Button } from '@/shared/ui/button/button'
import { EllipsisVertical } from 'lucide-react'

export default function Main() {
  return (
    <div className="h-full flex flex-col">
      <div className="py-8 bg-white border-b border-outline">
        <div className="w-[1442px] h-full mx-auto flex items-center justify-between">
          <div className="text-dark flex items-center">
            <div className="size-20 bg-[#D9D9D9]" />
            <div className="ml-6">
              <p className="text-4xl font-bold">Math</p>
              <p className="text-2xl font-light text-dark/60 pt-1">
                Innopolis University
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 font-light">
            <Button className="px-6 py-3 text-lg rounded-lg">Course</Button>
            <Button variant="outline" className="px-6 py-3 text-lg rounded-lg">
              Participants
            </Button>
            <Button variant="outline" className="px-6 py-3 text-lg rounded-lg">
              Grades
            </Button>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-scroll py-10">
        <div className="w-[1442px] mx-auto">
          <div className="flex items-center justify-between text-4xl pb-4 px-6 font-light w-full border-b border-dark/10">
            General
            <EllipsisVertical />
          </div>

          <div className="pt-8"></div>
        </div>
      </div>
    </div>
  )
}
