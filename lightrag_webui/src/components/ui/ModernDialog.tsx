import React, { useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { cn } from '@/lib/utils'

// 弹窗类型定义
export type DialogType = 'success' | 'error' | 'warning' | 'info' | 'confirm' | 'prompt'

interface ModernDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  type: DialogType
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm?: (value?: string) => void
  onCancel?: () => void
  defaultValue?: string
  placeholder?: string
  required?: boolean
}

// 图标映射
const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  confirm: AlertTriangle,
  prompt: Info,
}

// 颜色映射
const colorMap = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-500',
  confirm: 'text-yellow-500',
  prompt: 'text-blue-500',
}

export const ModernDialog: React.FC<ModernDialogProps> = ({
  open,
  onOpenChange,
  type,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  onConfirm,
  onCancel,
  defaultValue = '',
  placeholder = '',
  required = false,
}) => {
  const [inputValue, setInputValue] = useState(defaultValue)
  const [error, setError] = useState('')

  const Icon = iconMap[type]
  const iconColor = colorMap[type]

  const handleConfirm = () => {
    if (type === 'prompt') {
      if (required && !inputValue.trim()) {
        setError('此字段为必填项')
        return
      }
      onConfirm?.(inputValue.trim())
    } else {
      onConfirm?.()
    }
    handleClose()
  }

  const handleCancel = () => {
    onCancel?.()
    handleClose()
  }

  const handleClose = () => {
    setInputValue(defaultValue)
    setError('')
    onOpenChange(false)
  }

  const showButtons = type === 'confirm' || type === 'prompt'
  const showInput = type === 'prompt'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Icon className={cn('h-6 w-6', iconColor)} />
            {title}
          </DialogTitle>
          <DialogDescription className="text-left pl-9">
            {message}
          </DialogDescription>
        </DialogHeader>

        {showInput && (
          <div className="grid gap-4 py-4 pl-9">
            <div className="grid gap-2">
              {placeholder && (
                <Label htmlFor="input-field" className="text-sm text-muted-foreground">
                  {placeholder}
                </Label>
              )}
              <Input
                id="input-field"
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value)
                  if (error) setError('')
                }}
                placeholder={placeholder}
                className={cn(error && 'border-red-500')}
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleConfirm()
                  }
                }}
              />
              {error && (
                <p className="text-sm text-red-500">{error}</p>
              )}
            </div>
          </div>
        )}

        <DialogFooter className={cn(!showButtons && 'justify-center')}>
          {showButtons ? (
            <>
              <Button variant="outline" onClick={handleCancel}>
                {cancelText}
              </Button>
              <Button onClick={handleConfirm}>
                {confirmText}
              </Button>
            </>
          ) : (
            <Button onClick={handleClose} className="min-w-[100px]">
              确定
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Hook for easier usage
export const useModernDialog = () => {
  const [dialogState, setDialogState] = useState<{
    open: boolean
    type: DialogType
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    defaultValue?: string
    placeholder?: string
    required?: boolean
    onConfirm?: (value?: string) => void
    onCancel?: () => void
  }>({
    open: false,
    type: 'info',
    title: '',
    message: '',
  })

  const showDialog = (config: Omit<typeof dialogState, 'open'>) => {
    setDialogState({ ...config, open: true })
  }

  const hideDialog = () => {
    setDialogState(prev => ({ ...prev, open: false }))
  }

  // 便捷方法
  const showSuccess = (title: string, message: string) => {
    showDialog({ type: 'success', title, message })
  }

  const showError = (title: string, message: string) => {
    showDialog({ type: 'error', title, message })
  }

  const showWarning = (title: string, message: string) => {
    showDialog({ type: 'warning', title, message })
  }

  const showInfo = (title: string, message: string) => {
    showDialog({ type: 'info', title, message })
  }

  const showConfirm = (
    title: string,
    message: string,
    onConfirm?: () => void,
    onCancel?: () => void,
    confirmText?: string,
    cancelText?: string
  ) => {
    showDialog({
      type: 'confirm',
      title,
      message,
      onConfirm,
      onCancel,
      confirmText,
      cancelText,
    })
  }

  const showPrompt = (
    title: string,
    message: string,
    onConfirm?: (value: string) => void,
    onCancel?: () => void,
    defaultValue?: string,
    placeholder?: string,
    required?: boolean
  ) => {
    showDialog({
      type: 'prompt',
      title,
      message,
      onConfirm,
      onCancel,
      defaultValue,
      placeholder,
      required,
    })
  }

  const DialogComponent = () => (
    <ModernDialog
      {...dialogState}
      onOpenChange={hideDialog}
    />
  )

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showConfirm,
    showPrompt,
    DialogComponent,
    hideDialog,
  }
}
