import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { PlusIcon, DatabaseIcon } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/Dialog'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'
import { Label } from '@/components/ui/Label'
import { createGraph } from '@/api/lightrag'
import { useGraphState } from '@/stores/state'

interface CreateGraphDialogProps {
  onGraphCreated?: () => void
  trigger?: React.ReactNode
}

export default function CreateGraphDialog({ onGraphCreated, trigger }: CreateGraphDialogProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const refreshCurrentGraph = useGraphState.use.refreshCurrentGraph()

  // 验证表单
  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = t('graph.create.errors.nameRequired', 'Graph name is required')
    } else if (formData.name.trim().length < 2) {
      newErrors.name = t('graph.create.errors.nameMinLength', 'Graph name must be at least 2 characters')
    } else if (formData.name.trim().length > 50) {
      newErrors.name = t('graph.create.errors.nameMaxLength', 'Graph name must be less than 50 characters')
    } else if (!/^[a-zA-Z0-9\u4e00-\u9fa5_\-\s]+$/.test(formData.name.trim())) {
      newErrors.name = t('graph.create.errors.nameInvalid', 'Graph name contains invalid characters')
    }

    if (formData.description.trim().length > 500) {
      newErrors.description = t('graph.create.errors.descriptionMaxLength', 'Description must be less than 500 characters')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    try {
      const response = await createGraph(formData.name.trim(), formData.description.trim())
      
      if (response.status === 'success') {
        toast.success(t('graph.create.success', 'Graph created successfully'))
        
        // 重置表单
        setFormData({ name: '', description: '' })
        setErrors({})
        setOpen(false)
        
        // 刷新图谱状态
        await refreshCurrentGraph()
        
        // 调用回调函数
        onGraphCreated?.()
      } else {
        throw new Error(response.message || 'Failed to create graph')
      }
    } catch (error) {
      console.error('Failed to create graph:', error)
      toast.error(t('graph.create.error', 'Failed to create graph'))
    } finally {
      setIsLoading(false)
    }
  }

  // 处理输入变化
  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // 清除对应字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  // 处理对话框关闭
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && !isLoading) {
      setOpen(false)
      setFormData({ name: '', description: '' })
      setErrors({})
    }
  }

  const defaultTrigger = (
    <Button variant="outline" size="sm">
      <PlusIcon className="h-4 w-4 mr-2" />
      {t('graph.create.title', 'Create Graph')}
    </Button>
  )

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DatabaseIcon className="h-5 w-5" />
            {t('graph.create.title', 'Create New Graph')}
          </DialogTitle>
          <DialogDescription>
            {t('graph.create.description', 'Create a new knowledge graph to organize your documents and data.')}
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="graph-name">
              {t('graph.create.name', 'Graph Name')} <span className="text-red-500">*</span>
            </Label>
            <Input
              id="graph-name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder={t('graph.create.namePlaceholder', 'Enter graph name')}
              disabled={isLoading}
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="graph-description">
              {t('graph.create.description', 'Description')}
            </Label>
            <Textarea
              id="graph-description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder={t('graph.create.descriptionPlaceholder', 'Enter graph description (optional)')}
              disabled={isLoading}
              rows={3}
              className={errors.description ? 'border-red-500' : ''}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description}</p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !formData.name.trim()}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  {t('graph.create.creating', 'Creating...')}
                </>
              ) : (
                <>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  {t('graph.create.create', 'Create Graph')}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
