import { useState, useCallback } from 'react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'
import { 
  createRelation, 
  createRelationsBatch, 
  deleteRelation, 
  updateRelationByEntities,
  type RelationCreateRequest 
} from '@/api/lightrag'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/Dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/AlertDialog'
import Separator from '@/components/ui/Separator'
import { ScrollArea } from '@/components/ui/ScrollArea'
import Textarea from '@/components/ui/Textarea'
import NumberInput from '@/components/ui/NumberInput'
import { PlusIcon, TrashIcon, EditIcon, PackageIcon, LinkIcon, FileTextIcon } from 'lucide-react'

const RelationManager = () => {
  const { t } = useTranslation()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showBatchDialog, setBatchDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showUpdateDialog, setShowUpdateDialog] = useState(false)
  const [creating, setCreating] = useState(false)
  
  // 单个关系创建表单
  const [relationForm, setRelationForm] = useState<RelationCreateRequest>({
    source_entity: '',
    target_entity: '',
    description: '',
    keywords: '',
    weight: 1.0,
    source_id: 'manual',
    file_path: 'manual_input'
  })

  // 批量关系创建表单
  const [batchText, setBatchText] = useState('')
  
  // 删除关系表单
  const [deleteForm, setDeleteForm] = useState({
    source_entity: '',
    target_entity: ''
  })

  // 更新关系表单
  const [updateForm, setUpdateForm] = useState({
    source_entity: '',
    target_entity: '',
    description: '',
    keywords: '',
    weight: 1.0
  })

  // 重置表单
  const resetForm = useCallback(() => {
    setRelationForm({
      source_entity: '',
      target_entity: '',
      description: '',
      keywords: '',
      weight: 1.0,
      source_id: 'manual',
      file_path: 'manual_input'
    })
  }, [])

  // 创建单个关系
  const handleCreateRelation = async () => {
    if (!relationForm.source_entity.trim() || !relationForm.target_entity.trim()) {
      toast.error(t('relation.entitiesRequired', 'Source and target entities are required'))
      return
    }

    setCreating(true)
    try {
      await createRelation(relationForm)
      toast.success(t('relation.createSuccess', 'Relation created successfully'))
      setShowCreateDialog(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create relation:', error)
      toast.error(t('relation.createError', 'Failed to create relation'))
    } finally {
      setCreating(false)
    }
  }

  // 批量创建关系
  const handleBatchCreate = async () => {
    if (!batchText.trim()) {
      toast.error(t('relation.batchTextRequired', 'Batch text is required'))
      return
    }

    // 解析批量文本（每行一个关系，格式：源实体|目标实体|描述|关键词|权重）
    const lines = batchText.trim().split('\n').filter(line => line.trim())
    const relations: RelationCreateRequest[] = lines.map(line => {
      const parts = line.split('|').map(p => p.trim())
      return {
        source_entity: parts[0] || '',
        target_entity: parts[1] || '',
        description: parts[2] || '',
        keywords: parts[3] || '',
        weight: parseFloat(parts[4]) || 1.0,
        source_id: 'manual_batch',
        file_path: 'manual_input'
      }
    }).filter(relation => relation.source_entity && relation.target_entity)

    if (relations.length === 0) {
      toast.error(t('relation.noValidRelations', 'No valid relations found'))
      return
    }

    setCreating(true)
    try {
      const result = await createRelationsBatch(relations)
      toast.success(
        t('relation.batchCreateSuccess', 
          `Batch creation completed: ${result.successful_count} successful, ${result.failed_count} failed`
        )
      )
      setBatchDialog(false)
      setBatchText('')
    } catch (error) {
      console.error('Failed to batch create relations:', error)
      toast.error(t('relation.batchCreateError', 'Failed to batch create relations'))
    } finally {
      setCreating(false)
    }
  }

  // 删除关系
  const handleDeleteRelation = async () => {
    if (!deleteForm.source_entity.trim() || !deleteForm.target_entity.trim()) {
      toast.error(t('relation.entitiesRequired', 'Source and target entities are required'))
      return
    }

    try {
      await deleteRelation(deleteForm.source_entity.trim(), deleteForm.target_entity.trim())
      toast.success(t('relation.deleteSuccess', 'Relation deleted successfully'))
      setShowDeleteDialog(false)
      setDeleteForm({ source_entity: '', target_entity: '' })
    } catch (error) {
      console.error('Failed to delete relation:', error)
      toast.error(t('relation.deleteError', 'Failed to delete relation'))
    }
  }

  // 更新关系
  const handleUpdateRelation = async () => {
    if (!updateForm.source_entity.trim() || !updateForm.target_entity.trim()) {
      toast.error(t('relation.entitiesRequired', 'Source and target entities are required'))
      return
    }

    try {
      await updateRelationByEntities(
        updateForm.source_entity.trim(),
        updateForm.target_entity.trim(),
        {
          description: updateForm.description,
          keywords: updateForm.keywords,
          weight: updateForm.weight
        }
      )
      toast.success(t('relation.updateSuccess', 'Relation updated successfully'))
      setShowUpdateDialog(false)
      setUpdateForm({
        source_entity: '',
        target_entity: '',
        description: '',
        keywords: '',
        weight: 1.0
      })
    } catch (error) {
      console.error('Failed to update relation:', error)
      toast.error(t('relation.updateError', 'Failed to update relation'))
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b p-4">
        <div>
          <h1 className="text-2xl font-bold">{t('relation.title', 'Relation Management')}</h1>
          <p className="text-muted-foreground">
            {t('relation.description', 'Manually create, update, and manage relationships between entities')}
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <TrashIcon className="h-4 w-4" />
                {t('relation.delete', 'Delete Relation')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('relation.deleteTitle', 'Delete Relation')}</DialogTitle>
                <DialogDescription>
                  {t('relation.deleteDescription', 'Delete a relationship between two entities.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.sourceEntity', 'Source Entity')} *
                  </label>
                  <Input
                    value={deleteForm.source_entity}
                    onChange={(e) => setDeleteForm(prev => ({ ...prev, source_entity: e.target.value }))}
                    placeholder={t('relation.sourceEntityPlaceholder', 'Enter source entity name')}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.targetEntity', 'Target Entity')} *
                  </label>
                  <Input
                    value={deleteForm.target_entity}
                    onChange={(e) => setDeleteForm(prev => ({ ...prev, target_entity: e.target.value }))}
                    placeholder={t('relation.targetEntityPlaceholder', 'Enter target entity name')}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button 
                  onClick={handleDeleteRelation} 
                  disabled={!deleteForm.source_entity.trim() || !deleteForm.target_entity.trim()}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {t('common.delete', 'Delete')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showUpdateDialog} onOpenChange={setShowUpdateDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <EditIcon className="h-4 w-4" />
                {t('relation.update', 'Update Relation')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('relation.updateTitle', 'Update Relation')}</DialogTitle>
                <DialogDescription>
                  {t('relation.updateDescription', 'Update the properties of an existing relationship.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">
                      {t('relation.sourceEntity', 'Source Entity')} *
                    </label>
                    <Input
                      value={updateForm.source_entity}
                      onChange={(e) => setUpdateForm(prev => ({ ...prev, source_entity: e.target.value }))}
                      placeholder={t('relation.sourceEntityPlaceholder', 'Enter source entity name')}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">
                      {t('relation.targetEntity', 'Target Entity')} *
                    </label>
                    <Input
                      value={updateForm.target_entity}
                      onChange={(e) => setUpdateForm(prev => ({ ...prev, target_entity: e.target.value }))}
                      placeholder={t('relation.targetEntityPlaceholder', 'Enter target entity name')}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.description', 'Description')}
                  </label>
                  <Textarea
                    value={updateForm.description}
                    onChange={(e) => setUpdateForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder={t('relation.descriptionPlaceholder', 'Enter relation description')}
                    rows={3}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.keywords', 'Keywords')}
                  </label>
                  <Input
                    value={updateForm.keywords}
                    onChange={(e) => setUpdateForm(prev => ({ ...prev, keywords: e.target.value }))}
                    placeholder={t('relation.keywordsPlaceholder', 'Enter keywords (space separated)')}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.weight', 'Weight')}
                  </label>
                  <NumberInput
                    value={updateForm.weight}
                    onChange={(value) => setUpdateForm(prev => ({ ...prev, weight: value }))}
                    min={0}
                    max={10}
                    step={0.1}
                    placeholder="1.0"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowUpdateDialog(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button 
                  onClick={handleUpdateRelation} 
                  disabled={!updateForm.source_entity.trim() || !updateForm.target_entity.trim()}
                >
                  {t('common.update', 'Update')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showBatchDialog} onOpenChange={setBatchDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <PackageIcon className="h-4 w-4" />
                {t('relation.batchCreate', 'Batch Create')}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{t('relation.batchCreateTitle', 'Batch Create Relations')}</DialogTitle>
                <DialogDescription>
                  {t('relation.batchCreateDescription', 'Create multiple relations at once. Format: Source|Target|Description|Keywords|Weight (one per line)')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.batchText', 'Batch Text')} *
                  </label>
                  <Textarea
                    value={batchText}
                    onChange={(e) => setBatchText(e.target.value)}
                    placeholder={`${t('relation.batchPlaceholder', 'Example')}:
阿司匹林|心脏病|用于预防心脏病|预防 治疗|2.5
阿司匹林|高血压|用于心血管保护|保护 预防|2.0`}
                    rows={8}
                    className="font-mono text-sm"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setBatchDialog(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button onClick={handleBatchCreate} disabled={!batchText.trim() || creating}>
                  {creating ? t('common.creating', 'Creating...') : t('common.create', 'Create')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm">
                <PlusIcon className="h-4 w-4" />
                {t('relation.create', 'Create Relation')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('relation.createTitle', 'Create New Relation')}</DialogTitle>
                <DialogDescription>
                  {t('relation.createDescription', 'Create a new relationship between two entities.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">
                      {t('relation.sourceEntity', 'Source Entity')} *
                    </label>
                    <Input
                      value={relationForm.source_entity}
                      onChange={(e) => setRelationForm(prev => ({ ...prev, source_entity: e.target.value }))}
                      placeholder={t('relation.sourceEntityPlaceholder', 'Enter source entity name')}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">
                      {t('relation.targetEntity', 'Target Entity')} *
                    </label>
                    <Input
                      value={relationForm.target_entity}
                      onChange={(e) => setRelationForm(prev => ({ ...prev, target_entity: e.target.value }))}
                      placeholder={t('relation.targetEntityPlaceholder', 'Enter target entity name')}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.description', 'Description')}
                  </label>
                  <Textarea
                    value={relationForm.description}
                    onChange={(e) => setRelationForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder={t('relation.descriptionPlaceholder', 'Enter relation description')}
                    rows={3}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.keywords', 'Keywords')}
                  </label>
                  <Input
                    value={relationForm.keywords}
                    onChange={(e) => setRelationForm(prev => ({ ...prev, keywords: e.target.value }))}
                    placeholder={t('relation.keywordsPlaceholder', 'Enter keywords (space separated)')}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('relation.weight', 'Weight')}
                  </label>
                  <NumberInput
                    value={relationForm.weight || 1.0}
                    onChange={(value) => setRelationForm(prev => ({ ...prev, weight: value }))}
                    min={0}
                    max={10}
                    step={0.1}
                    placeholder="1.0"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button 
                  onClick={handleCreateRelation} 
                  disabled={!relationForm.source_entity.trim() || !relationForm.target_entity.trim() || creating}
                >
                  {creating ? t('common.creating', 'Creating...') : t('common.create', 'Create')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4">
            <div className="grid gap-6 md:grid-cols-2">
              {/* 功能说明卡片 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <LinkIcon className="h-5 w-5" />
                    {t('relation.features', 'Relation Management Features')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li>• {t('relation.feature1', 'Create relationships between entities')}</li>
                    <li>• {t('relation.feature2', 'Batch create multiple relationships')}</li>
                    <li>• {t('relation.feature3', 'Update relationship properties')}</li>
                    <li>• {t('relation.feature4', 'Delete specific relationships')}</li>
                    <li>• {t('relation.feature5', 'Set relationship weights and keywords')}</li>
                  </ul>
                </CardContent>
              </Card>

              {/* 使用说明卡片 */}
              <Card>
                <CardHeader>
                  <CardTitle>{t('relation.usage', 'Usage Instructions')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm text-muted-foreground">
                    <div>
                      <span className="font-medium">{t('relation.create', 'Create')}:</span>
                      <p>{t('relation.createDesc', 'Create individual relationships with detailed properties including description, keywords, and weight.')}</p>
                    </div>
                    <div>
                      <span className="font-medium">{t('relation.batchCreate', 'Batch Create')}:</span>
                      <p>{t('relation.batchCreateDesc', 'Create multiple relationships at once using the format: Source|Target|Description|Keywords|Weight.')}</p>
                    </div>
                    <div>
                      <span className="font-medium">{t('relation.update', 'Update')}:</span>
                      <p>{t('relation.updateDesc', 'Modify existing relationship properties by specifying the source and target entities.')}</p>
                    </div>
                    <div>
                      <span className="font-medium">{t('relation.delete', 'Delete')}:</span>
                      <p>{t('relation.deleteDesc', 'Remove relationships by specifying the source and target entities.')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}

export default RelationManager
