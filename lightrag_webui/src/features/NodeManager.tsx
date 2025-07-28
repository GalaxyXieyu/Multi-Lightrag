import { useState, useCallback } from 'react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'
import { 
  createNode, 
  createNodesBatch, 
  deleteNode, 
  getNode,
  type NodeCreateRequest,
  type NodeInfo 
} from '@/api/lightrag'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/Dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/AlertDialog'
import Badge from '@/components/ui/Badge'
import Separator from '@/components/ui/Separator'
import { ScrollArea } from '@/components/ui/ScrollArea'
import Textarea from '@/components/ui/Textarea'
import { PlusIcon, TrashIcon, SearchIcon, PackageIcon, FileTextIcon } from 'lucide-react'

const NodeManager = () => {
  const { t } = useTranslation()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showBatchDialog, setBatchDialog] = useState(false)
  const [showSearchDialog, setShowSearchDialog] = useState(false)
  const [creating, setCreating] = useState(false)
  const [searching, setSearching] = useState(false)
  const [searchResult, setSearchResult] = useState<NodeInfo | null>(null)
  
  // 单个节点创建表单
  const [nodeForm, setNodeForm] = useState<NodeCreateRequest>({
    entity_name: '',
    entity_type: '',
    description: '',
    source_id: 'manual',
    file_path: 'manual_input'
  })

  // 批量节点创建表单
  const [batchText, setBatchText] = useState('')
  const [searchNodeName, setSearchNodeName] = useState('')

  // 重置表单
  const resetForm = useCallback(() => {
    setNodeForm({
      entity_name: '',
      entity_type: '',
      description: '',
      source_id: 'manual',
      file_path: 'manual_input'
    })
  }, [])

  // 创建单个节点
  const handleCreateNode = async () => {
    if (!nodeForm.entity_name.trim()) {
      toast.error(t('node.nameRequired', 'Node name is required'))
      return
    }

    setCreating(true)
    try {
      await createNode(nodeForm)
      toast.success(t('node.createSuccess', 'Node created successfully'))
      setShowCreateDialog(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create node:', error)
      toast.error(t('node.createError', 'Failed to create node'))
    } finally {
      setCreating(false)
    }
  }

  // 批量创建节点
  const handleBatchCreate = async () => {
    if (!batchText.trim()) {
      toast.error(t('node.batchTextRequired', 'Batch text is required'))
      return
    }

    // 解析批量文本（每行一个节点，格式：名称|类型|描述）
    const lines = batchText.trim().split('\n').filter(line => line.trim())
    const nodes: NodeCreateRequest[] = lines.map(line => {
      const parts = line.split('|').map(p => p.trim())
      return {
        entity_name: parts[0] || '',
        entity_type: parts[1] || '',
        description: parts[2] || '',
        source_id: 'manual_batch',
        file_path: 'manual_input'
      }
    }).filter(node => node.entity_name)

    if (nodes.length === 0) {
      toast.error(t('node.noValidNodes', 'No valid nodes found'))
      return
    }

    setCreating(true)
    try {
      const result = await createNodesBatch(nodes)
      toast.success(
        t('node.batchCreateSuccess', 
          `Batch creation completed: ${result.successful_count} successful, ${result.failed_count} failed`
        )
      )
      setBatchDialog(false)
      setBatchText('')
    } catch (error) {
      console.error('Failed to batch create nodes:', error)
      toast.error(t('node.batchCreateError', 'Failed to batch create nodes'))
    } finally {
      setCreating(false)
    }
  }

  // 搜索节点
  const handleSearchNode = async () => {
    if (!searchNodeName.trim()) {
      toast.error(t('node.searchNameRequired', 'Node name is required for search'))
      return
    }

    setSearching(true)
    try {
      const result = await getNode(searchNodeName.trim())
      setSearchResult(result.node_data)
      if (!result.exists) {
        toast.info(t('node.notFound', 'Node not found'))
      }
    } catch (error) {
      console.error('Failed to search node:', error)
      toast.error(t('node.searchError', 'Failed to search node'))
      setSearchResult(null)
    } finally {
      setSearching(false)
    }
  }

  // 删除节点
  const handleDeleteNode = async (nodeName: string) => {
    try {
      await deleteNode(nodeName)
      toast.success(t('node.deleteSuccess', 'Node deleted successfully'))
      if (searchResult && searchResult.entity_name === nodeName) {
        setSearchResult(null)
      }
    } catch (error) {
      console.error('Failed to delete node:', error)
      toast.error(t('node.deleteError', 'Failed to delete node'))
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b p-4">
        <div>
          <h1 className="text-2xl font-bold">{t('node.title', 'Node Management')}</h1>
          <p className="text-muted-foreground">
            {t('node.description', 'Manually create, search, and manage nodes in the knowledge graph')}
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showSearchDialog} onOpenChange={setShowSearchDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <SearchIcon className="h-4 w-4" />
                {t('node.search', 'Search Node')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('node.searchTitle', 'Search Node')}</DialogTitle>
                <DialogDescription>
                  {t('node.searchDescription', 'Search for a node by its name to view details.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('node.name', 'Node Name')} *
                  </label>
                  <Input
                    value={searchNodeName}
                    onChange={(e) => setSearchNodeName(e.target.value)}
                    placeholder={t('node.searchPlaceholder', 'Enter node name to search')}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearchNode()}
                  />
                </div>
                {searchResult && (
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">{searchResult.entity_name}</CardTitle>
                      {searchResult.entity_type && (
                        <Badge variant="secondary">{searchResult.entity_type}</Badge>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        {searchResult.description && (
                          <div>
                            <span className="font-medium">{t('node.description', 'Description')}:</span>
                            <p className="text-muted-foreground">{searchResult.description}</p>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="font-medium">{t('node.sourceId', 'Source ID')}:</span>
                          <span className="text-muted-foreground">{searchResult.source_id || 'N/A'}</span>
                        </div>
                      </div>
                      <Separator className="my-3" />
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">
                            <TrashIcon className="h-4 w-4" />
                            {t('common.delete', 'Delete')}
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>{t('node.deleteConfirmTitle', 'Delete Node')}</AlertDialogTitle>
                            <AlertDialogDescription>
                              {t('node.deleteConfirmDescription', 
                                `Are you sure you want to delete the node "${searchResult.entity_name}"? This will also delete all related relationships.`
                              )}
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>{t('common.cancel', 'Cancel')}</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteNode(searchResult.entity_name)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              {t('common.delete', 'Delete')}
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </CardContent>
                  </Card>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowSearchDialog(false)}>
                  {t('common.close', 'Close')}
                </Button>
                <Button onClick={handleSearchNode} disabled={!searchNodeName.trim() || searching}>
                  {searching ? t('common.searching', 'Searching...') : t('common.search', 'Search')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showBatchDialog} onOpenChange={setBatchDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <PackageIcon className="h-4 w-4" />
                {t('node.batchCreate', 'Batch Create')}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{t('node.batchCreateTitle', 'Batch Create Nodes')}</DialogTitle>
                <DialogDescription>
                  {t('node.batchCreateDescription', 'Create multiple nodes at once. Format: Name|Type|Description (one per line)')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('node.batchText', 'Batch Text')} *
                  </label>
                  <Textarea
                    value={batchText}
                    onChange={(e) => setBatchText(e.target.value)}
                    placeholder={`${t('node.batchPlaceholder', 'Example')}:
阿司匹林|药物|解热镇痛药
心脏病|疾病|影响心脏功能的疾病
高血压|疾病|血压持续升高`}
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
                {t('node.create', 'Create Node')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('node.createTitle', 'Create New Node')}</DialogTitle>
                <DialogDescription>
                  {t('node.createDescription', 'Add a new node to the knowledge graph.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('node.name', 'Node Name')} *
                  </label>
                  <Input
                    value={nodeForm.entity_name}
                    onChange={(e) => setNodeForm(prev => ({ ...prev, entity_name: e.target.value }))}
                    placeholder={t('node.namePlaceholder', 'Enter node name')}
                    maxLength={200}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('node.type', 'Node Type')}
                  </label>
                  <Input
                    value={nodeForm.entity_type}
                    onChange={(e) => setNodeForm(prev => ({ ...prev, entity_type: e.target.value }))}
                    placeholder={t('node.typePlaceholder', 'Enter node type (optional)')}
                    maxLength={100}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('node.description', 'Description')}
                  </label>
                  <Textarea
                    value={nodeForm.description}
                    onChange={(e) => setNodeForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder={t('node.descriptionPlaceholder', 'Enter description (optional)')}
                    rows={3}
                    maxLength={1000}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button onClick={handleCreateNode} disabled={!nodeForm.entity_name.trim() || creating}>
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
                    <FileTextIcon className="h-5 w-5" />
                    {t('node.features', 'Node Management Features')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li>• {t('node.feature1', 'Create individual nodes with custom properties')}</li>
                    <li>• {t('node.feature2', 'Batch create multiple nodes from text')}</li>
                    <li>• {t('node.feature3', 'Search and view node details')}</li>
                    <li>• {t('node.feature4', 'Delete nodes and their relationships')}</li>
                  </ul>
                </CardContent>
              </Card>

              {/* 使用说明卡片 */}
              <Card>
                <CardHeader>
                  <CardTitle>{t('node.usage', 'Usage Instructions')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm text-muted-foreground">
                    <div>
                      <span className="font-medium">{t('node.singleCreate', 'Single Create')}:</span>
                      <p>{t('node.singleCreateDesc', 'Use the "Create Node" button to add individual nodes with detailed information.')}</p>
                    </div>
                    <div>
                      <span className="font-medium">{t('node.batchCreate', 'Batch Create')}:</span>
                      <p>{t('node.batchCreateDesc', 'Use the "Batch Create" button to add multiple nodes. Format: Name|Type|Description (one per line).')}</p>
                    </div>
                    <div>
                      <span className="font-medium">{t('node.search', 'Search')}:</span>
                      <p>{t('node.searchDesc', 'Use the "Search Node" button to find and manage existing nodes.')}</p>
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

export default NodeManager
