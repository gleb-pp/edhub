import { useState } from 'react'

export interface DraggableItem<T = any> {
  id: number
  parentId: number
  content: T
}

export interface DraggableList<T = any> {
  id: number
  children: DraggableItem<T>[]
}

export interface DragState {
  listId: number
  id: number | null
}

export const useDragAndDrop = <T = any>(initialItems: DraggableList<T>[]) => {
  const [items, setItems] = useState<DraggableList<T>[]>(initialItems)
  const [draggedItemId, setDraggedItemId] = useState<DragState | null>(null)
  const [dragOverItemId, setDragOverItemId] = useState<DragState | null>(null)
  const [dropDirection, setDropDirection] = useState<'top' | 'bottom' | null>(
    null,
  )

  const resetDragState = () => {
    setDraggedItemId(null)
    setDragOverItemId(null)
    setDropDirection(null)
  }

  const handleDragStart = (id: number | null, listId: number) => {
    setDraggedItemId({ listId, id })
  }

  const handleDragOver = (
    e: React.DragEvent<HTMLDivElement>,
    id: number | null,
    listId: number,
  ) => {
    e.preventDefault()

    const element = e.currentTarget
    const rect = element.getBoundingClientRect()
    const hoverMiddleY = rect.height / 2
    const hoverClientY = e.clientY - rect.top

    const isTopHalf = hoverClientY < hoverMiddleY

    setDragOverItemId({ listId, id })
    setDropDirection(isTopHalf ? 'top' : 'bottom')
  }

  const handleDropItem = (dropId: number | null, listId: number) => {
    if (draggedItemId === null || draggedItemId.id === null) return

    const newItems = items.map((l) => ({ ...l, children: [...l.children] }))

    const fromListIndex = newItems.findIndex(
      (l) => l.id === draggedItemId.listId,
    )
    const toListIndex = newItems.findIndex((l) => l.id === listId)
    if (fromListIndex === -1 || toListIndex === -1) {
      resetDragState()
      return
    }

    const draggedIndex = newItems[fromListIndex].children.findIndex(
      (c) => c.id === draggedItemId.id,
    )
    if (draggedIndex === -1) {
      resetDragState()
      return
    }

    const [removed] = newItems[fromListIndex].children.splice(draggedIndex, 1)

    const dir = dropDirection ?? 'bottom'
    let dropIndex: number

    if (dropId === null) {
      dropIndex = dir === 'top' ? 0 : newItems[toListIndex].children.length
    } else {
      const foundIndex = newItems[toListIndex].children.findIndex(
        (c) => c.id === dropId,
      )
      if (foundIndex === -1) {
        dropIndex = newItems[toListIndex].children.length
      } else {
        dropIndex = dir === 'top' ? foundIndex : foundIndex + 1
      }
    }

    dropIndex = Math.max(
      0,
      Math.min(dropIndex, newItems[toListIndex].children.length),
    )

    newItems[toListIndex].children.splice(dropIndex, 0, {
      ...removed,
      parentId: newItems[toListIndex].id,
    })

    setItems(newItems)
    resetDragState()
  }

  const handleDropList = (dropListId: number) => {
    if (draggedItemId === null || draggedItemId.id !== null) return

    const newItems = [...items]
    const draggedIndex = newItems.findIndex(
      (l) => l.id === draggedItemId.listId,
    )
    const targetIndex = newItems.findIndex((l) => l.id === dropListId)
    if (draggedIndex === -1 || targetIndex === -1) {
      resetDragState()
      return
    }

    const [removed] = newItems.splice(draggedIndex, 1)

    let insertIndex = targetIndex
    if (draggedIndex < targetIndex) insertIndex = insertIndex - 1

    insertIndex =
      dropDirection === 'top'
        ? insertIndex
        : Math.min(insertIndex + 1, newItems.length)
    insertIndex = Math.max(0, Math.min(insertIndex, newItems.length))

    newItems.splice(insertIndex, 0, removed)

    setItems(newItems)
    resetDragState()
  }

  const handleDrop = (
    e: React.DragEvent<HTMLDivElement>,
    dropId: number | null,
    listId: number,
  ) => {
    e.preventDefault()
    if (draggedItemId === null) return

    if (draggedItemId.id === null) handleDropList(listId)
    else handleDropItem(dropId, listId)
  }

  const handleDragEnd = () => resetDragState()

  return {
    items,
    draggedItemId,
    dragOverItemId,
    dropDirection,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
    setItems,
  }
}
