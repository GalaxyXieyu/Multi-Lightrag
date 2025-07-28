import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  PlusIcon, 
  SaveIcon
} from 'lucide-react'
import { useGraphState } from '@/stores/state'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/Select'
import { Label } from '@/components/ui/Label'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'
import Button from '@/components/ui/Button'
import Checkbox from '@/components/ui/Checkbox'
import { toast } from 'sonner'

// 节点类型定义
const NODE_TYPES = [
  { value: 'entity', label: 'Entity', color: '#3b82f6' },
  { value: 'concept', label: 'Concept', color: '#10b981' },
  { value: 'event', label: 'Event', color: '#f59e0b' },
  { value: 'person', label: 'Person', color: '#ef4444' },
  { value: 'organization', label: 'Organization', color: '#8b5cf6' },
  { value: 'location', label: 'Location', color: '#06b6d4' },
  { value: 'document', label: 'Document', color: '#6b7280' },
  { value: 'custom', label: 'Custom', color: '#ec4899' }
]

// 节点大小选项
const NODE_SIZES = [
  { value: 'small', label: 'Small', size: 8 },
  { value: 'medium', label: 'Medium', size: 12 },
  { value: 'large', label: 'Large', size: 16 }
]

interface NodeFormData {
  name: string
  type: string
  description: string
  labels: string[]
  source: string
  color: string
  size: string
}

interface NodeCreationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onNodeCreated: () => void
  existingNodes: Array<{ id: string; label: string }>
  position?: { x: number; y: number }
}

const NodeCreationModal: React.FC<NodeCreationModalProps> = ({
  open,
  onOpenChange,
  onNodeCreated,
  existingNodes,
  position
}) => {
  const { t } = useTranslation()
  const currentGraph = useGraphState.use.currentGraph()
  
  const [formData, setFormData] = useState<NodeFormData>({
    name: '',
    type: 'entity',
    description: '',
    labels: [],
    source: 'manual_input',
    color: '#3b82f6',
    size: 'medium'
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [createAnother, setCreateAnother] = useState(false)
  const [labelInput, setLabelInput] = useState('')

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      type: 'entity',
      description: '',
      labels: [],
      source: 'manual_input',
      color: '#3b82f6',
      size: 'medium'
    })
    setErrors({})
    setLabelInput('')
  }

  // 表单验证
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Node name is required'
    }
    
    if (formData.name.trim().length > 100) {
      newErrors.name = 'Node name must be less than 100 characters'
    }
    
    if (formData.description.length > 1000) {
      newErrors.description = 'Description must be less than 1000 characters'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // 添加标签
  const addLabel = () => {
    const label = labelInput.trim()
    if (label && !formData.labels.includes(label)) {
      setFormData(prev => ({
        ...prev,
        labels: [...prev.labels, label]
      }))
      setLabelInput('')
    }
  }

  // 移除标签
  const removeLabel = (labelToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      labels: prev.labels.filter(label => label !== labelToRemove)
    }))
  }

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    try {
      const graphId = currentGraph?.graph_id || 'default'
      const nodeSize = NODE_SIZES.find(s => s.value === formData.size)?.size || 12
      
      // 创建节点
      const nodeResponse = await fetch(`/graphs/nodes?graph_id=${encodeURIComponent(graphId)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_name: formData.name.trim(),
          entity_type: formData.type,
          description: formData.description,
          labels: formData.labels,
          source_id: 'manual_creation',
          file_path: formData.source,
          // 扩展属性
          color: formData.color,
          size: nodeSize,
          position: position
        })
      })

      if (!nodeResponse.ok) {
        throw new Error('Failed to create node')
      }

      toast.success('Node created successfully')
      
      if (createAnother) {
        resetForm()
      } else {
        onOpenChange(false)
      }
      
      onNodeCreated()
      
    } catch (error) {
      console.error('Failed to create node:', error)
      toast.error('Failed to create node')
    } finally {
      setIsLoading(false)
    }
  }

  // 处理对话框关闭
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && !isLoading) {
      onOpenChange(false)
      resetForm()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PlusIcon className="h-5 w-5" />
            Create New Node
          </DialogTitle>
          <DialogDescription>
            Create a new node with custom properties.
          </DialogDescription>
        </DialogHeader>
        
        <div className="max-h-[60vh] overflow-y-auto pr-4 space-y-4">
          {/* 节点名称 */}
          <div className="space-y-2">
            <Label htmlFor="node-name">
              Node Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="node-name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter node name"
              disabled={isLoading}
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          {/* 节点类型和大小 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="node-type">Node Type</Label>
              <Select
                value={formData.type}
                onValueChange={(value) => {
                  setFormData(prev => ({ ...prev, type: value }))
                  // 自动设置对应的颜色
                  const nodeType = NODE_TYPES.find(t => t.value === value)
                  if (nodeType) {
                    setFormData(prev => ({ ...prev, color: nodeType.color }))
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {NODE_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: type.color }}
                        />
                        {type.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="node-size">Size</Label>
              <Select
                value={formData.size}
                onValueChange={(value) => setFormData(prev => ({ ...prev, size: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {NODE_SIZES.map(size => (
                    <SelectItem key={size.value} value={size.value}>
                      {size.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 描述 */}
          <div className="space-y-2">
            <Label htmlFor="node-description">Description</Label>
            <Textarea
              id="node-description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Enter detailed description of the node"
              disabled={isLoading}
              rows={3}
              className={errors.description ? 'border-red-500' : ''}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description}</p>
            )}
          </div>

          {/* 标签 */}
          <div className="space-y-2">
            <Label htmlFor="node-labels">Labels</Label>
            <div className="flex gap-2">
              <Input
                id="node-labels"
                value={labelInput}
                onChange={(e) => setLabelInput(e.target.value)}
                placeholder="Add a label"
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addLabel()
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={addLabel}
                disabled={isLoading || !labelInput.trim()}
              >
                Add
              </Button>
            </div>
            {formData.labels.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.labels.map((label, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-sm"
                  >
                    <span>{label}</span>
                    <button
                      type="button"
                      onClick={() => removeLabel(label)}
                      className="text-blue-600 hover:text-blue-800"
                      disabled={isLoading}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 来源 */}
          <div className="space-y-2">
            <Label htmlFor="node-source">Source</Label>
            <Input
              id="node-source"
              value={formData.source}
              onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
              placeholder="Source file or origin"
              disabled={isLoading}
            />
          </div>
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="create-another"
              checked={createAnother}
              onCheckedChange={setCreateAnother}
              disabled={isLoading}
            />
            <Label htmlFor="create-another" className="text-sm">
              Create another node
            </Label>
          </div>
          
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isLoading || !formData.name.trim()}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Creating...
                </>
              ) : (
                <>
                  <SaveIcon className="h-4 w-4 mr-2" />
                  Create Node
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default NodeCreationModal
