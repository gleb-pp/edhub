import { useDebaunce } from '@/shared/hooks/useDebaunce'
import { Input } from '@/shared/ui/input/input'
import { Modal } from '@/shared/ui/modal/modal'
import clsx from 'clsx'
import { FC, useState } from 'react'

interface SearchModalProps {
  onClose: () => void
  isOpen: boolean
}

export const SearchModal: FC<SearchModalProps> = ({ onClose, isOpen }) => {
  const [inputData, setInputData] = useState('')
  const [isActive, setActive] = useState(false)

  const debaunce = useDebaunce(300)

  const handleChangeInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    debaunce(() => setInputData(e.target.value))
  }

  const handleCloseModal = () => {
    setInputData('')
    onClose()
  }

  return (
    <Modal
      className="w-200 h-140 flex flex-col !bg-transparent border-none !shadow-none pointer-events-none"
      isOpen={isOpen}
      onClose={handleCloseModal}
      modalId={'input-modal'}
    >
      <Input
        onClick={() => setActive((prev) => !prev)}
        onChange={handleChangeInput}
        className={clsx(
          'w-full px-8 py-6 text-xl !max-h-15 !rounded-xl pointer-events-auto !bg-white transition-all duration-200',
          isActive ? '!rounded-b-none' : '',
        )}
        placeholder="Search something..."
      />
      <div className="flex-1">
        <div
          className={clsx(
            'bg-white p-3 rounded-b-xl transition-all transition-discrete duration-200',
            isActive
              ? 'opacity-100 translate-y-0 rounded-t-none'
              : 'opacity-0 -translate-y-2 rounded-t-xl',
          )}
        >
          {inputData}
        </div>
      </div>
    </Modal>
  )
}
