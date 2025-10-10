'use client'
import React, { useEffect, FC, useRef, createContext, useContext } from 'react'
import clsx from 'clsx'
import { Card } from '../card/card'
import './modal.css'
import { useAnimatedPresence } from '@/shared/hooks/useAnimatedPresence'

interface ModalProps {
  isOpen: boolean
  className?: string
  onClose: () => void
  children: React.ReactNode
  modalId: string
}

interface ModalElementProps {
  className?: string
  children: React.ReactNode
}

interface ModalType extends FC<ModalProps> {
  Header: FC<ModalElementProps>
  Body: FC<ModalElementProps>
  Footer: FC<ModalElementProps>
}

const ModalContext = createContext<{ modalId: string }>({ modalId: 'labuba' })

const ModalComponent: FC<ModalProps> = ({
  isOpen,
  onClose,
  children,
  className,
  modalId,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const previouslyFocusedElement = useRef<HTMLElement | null>(null)

  const isVisible = useAnimatedPresence(isOpen, 200) // modal.css -> animation: * 200ms *

  useEffect(() => {
    if (isOpen) {
      previouslyFocusedElement.current = document.activeElement as HTMLElement
      dialogRef.current?.focus()
    } else {
      previouslyFocusedElement.current?.focus()
    }
  }, [isOpen])

  if (!isVisible) return null

  return (
    <ModalContext.Provider value={{ modalId }}>
      <div
        ref={overlayRef}
        className={clsx(
          'fixed inset-0 flex items-center justify-center bg-black/50 z-50 outline-none',
          isOpen ? 'fade-in' : 'fade-out',
        )}
        onClick={onClose}
      >
        <Card
          role="dialog"
          aria-modal="true"
          aria-labelledby={`modal-title-${modalId}`}
          aria-describedby={`modal-body-${modalId}`}
          tabIndex={-1}
          className={clsx(
            'flex flex-col',
            isOpen ? 'scale-in' : 'scale-out',
            className,
          )}
          onClick={(e) => e.stopPropagation()}
          ref={dialogRef}
        >
          {children}
        </Card>
      </div>
    </ModalContext.Provider>
  )
}

const Modal = ModalComponent as ModalType

Modal.Header = ({ className, children }) => {
  const { modalId } = useContext(ModalContext)
  return (
    <div id={`modal-title-${modalId}`} className={className}>
      {children}
    </div>
  )
}
Modal.Header.displayName = 'Modal.Header'

Modal.Body = ({ className, children }) => {
  const { modalId } = useContext(ModalContext)
  return (
    <div
      id={`modal-body-${modalId}`}
      className={clsx('flex-1 overflow-auto', className)}
    >
      {children}
    </div>
  )
}
Modal.Body.displayName = 'Modal.Body'

Modal.Footer = ({ className, children }) => (
  <div className={clsx('gap-2', className)}>{children}</div>
)
Modal.Footer.displayName = 'Modal.Footer'

export { Modal }
