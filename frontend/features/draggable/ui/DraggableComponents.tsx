import React, { ReactNode, createContext, useContext } from 'react'
import {
  useDragAndDrop,
  DraggableList as DraggableListType,
  DraggableItem as DraggableItemType,
} from './useDragAndDrop'

interface DragAndDropContextType {
  draggedItemId: { listId: number; id: number | null } | null
  dragOverItemId: { listId: number; id: number | null } | null
  dropDirection: 'top' | 'bottom' | null
  handleDragStart: (id: number | null, listId: number) => void
  handleDragOver: (
    e: React.DragEvent<HTMLDivElement>,
    id: number | null,
    listId: number,
  ) => void
  handleDrop: (
    e: React.DragEvent<HTMLDivElement>,
    dropId: number | null,
    listId: number,
  ) => void
  handleDragEnd: () => void
}

const DragAndDropContext = createContext<DragAndDropContextType | null>(null)

const useDragAndDropContext = () => {
  const context = useContext(DragAndDropContext)
  if (!context) {
    throw new Error('DragAndDrop components must be used within Draggable')
  }
  return context
}

interface DraggableProps<T = any> {
  children: ReactNode
  items: DraggableListType<T>[]
  onItemsChange?: (items: DraggableListType<T>[]) => void
  className?: string
}

export const Draggable = <T = any,>({
  children,
  items,
  onItemsChange,
  className,
}: DraggableProps<T>) => {
  const dragAndDropHook = useDragAndDrop<T>(items)

  React.useEffect(() => {
    if (onItemsChange) {
      onItemsChange(dragAndDropHook.items)
    }
  }, [dragAndDropHook.items, onItemsChange])

  const contextValue: DragAndDropContextType = {
    draggedItemId: dragAndDropHook.draggedItemId,
    dragOverItemId: dragAndDropHook.dragOverItemId,
    dropDirection: dragAndDropHook.dropDirection,
    handleDragStart: dragAndDropHook.handleDragStart,
    handleDragOver: dragAndDropHook.handleDragOver,
    handleDrop: dragAndDropHook.handleDrop,
    handleDragEnd: dragAndDropHook.handleDragEnd,
  }

  return (
    <DragAndDropContext.Provider value={contextValue}>
      <div className={className}>{children}</div>
    </DragAndDropContext.Provider>
  )
}

interface DraggableListProps {
  children: ReactNode
  listId: number
  className?: string
  isListDragOver?: (
    dragOverItemId: { listId: number; id: number | null } | null,
    currentListId: number,
  ) => boolean
  dragOverClassName?: string
}

export const DraggableList: React.FC<DraggableListProps> = ({
  children,
  listId,
  className,
  isListDragOver,
  dragOverClassName = 'bg-sky-100',
}) => {
  const { dragOverItemId, handleDragOver, handleDrop } = useDragAndDropContext()

  const isDragOver = isListDragOver
    ? isListDragOver(dragOverItemId, listId)
    : dragOverItemId?.listId === listId && dragOverItemId.id === null

  const finalClassName =
    `${className || ''} ${isDragOver ? dragOverClassName : ''}`.trim()

  return (
    <div
      className={finalClassName}
      onDragOver={(e) => {
        e.preventDefault()
        handleDragOver(e, null, listId)
      }}
      onDrop={(e) => {
        handleDrop(e, null, listId)
      }}
    >
      {children}
    </div>
  )
}

interface DraggableTitleProps {
  children: ReactNode
  listId: number
  className?: string
}

export const DraggableTitle: React.FC<DraggableTitleProps> = ({
  children,
  listId,
  className,
}) => {
  const { handleDragStart, handleDragOver, handleDrop, handleDragEnd } =
    useDragAndDropContext()

  return (
    <div
      className={`${className || ''} cursor-grab`.trim()}
      draggable
      onDragStart={(e) => {
        e.stopPropagation()
        handleDragStart(null, listId)
      }}
      onDragOver={(e) => {
        e.preventDefault()
        e.stopPropagation()
        handleDragOver(e, null, listId)
      }}
      onDrop={(e) => {
        e.stopPropagation()
        handleDrop(e, null, listId)
      }}
      onDragEnd={(e) => {
        e.stopPropagation()
        handleDragEnd()
      }}
    >
      {children}
    </div>
  )
}

interface DraggableItemProps<T = any> {
  children: ReactNode
  itemId: number
  listId: number
  className?: string
  isItemDragOver?: (
    dragOverItemId: { listId: number; id: number | null } | null,
    currentItemId: number,
    currentListId: number,
  ) => boolean
  dragOverClassName?: string
  itemData?: T
}

export const DraggableItem = <T = any,>({
  children,
  itemId,
  listId,
  className,
  isItemDragOver,
  dragOverClassName = 'bg-sky-100',
  itemData,
}: DraggableItemProps<T>) => {
  const {
    dragOverItemId,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
  } = useDragAndDropContext()

  const isDragOver = isItemDragOver
    ? isItemDragOver(dragOverItemId, itemId, listId)
    : dragOverItemId?.id === itemId && dragOverItemId.listId === listId

  const finalClassName =
    `${className || ''} ${isDragOver ? dragOverClassName : ''}`.trim()

  return (
    <div
      className={finalClassName}
      draggable
      onDragStart={(e) => {
        e.stopPropagation()
        handleDragStart(itemId, listId)
      }}
      onDragOver={(e) => {
        e.preventDefault()
        e.stopPropagation()
        handleDragOver(e, itemId, listId)
      }}
      onDrop={(e) => {
        e.stopPropagation()
        handleDrop(e, itemId, listId)
      }}
      onDragEnd={(e) => {
        e.stopPropagation()
        handleDragEnd()
      }}
    >
      {children}
    </div>
  )
}
