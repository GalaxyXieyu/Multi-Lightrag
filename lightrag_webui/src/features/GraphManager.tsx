import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'
import { 
  listGraphs, 
  createGraph, 
  deleteGraph, 
  switchGraph, 
  getCurrentGraph,
  type GraphInfo 
} from '@/api/lightrag'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/Dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/AlertDialog'
import Badge from '@/components/ui/Badge'
import Separator from '@/components/ui/Separator'
import { ScrollArea } from '@/components/ui/ScrollArea'
import EmptyCard from '@/components/ui/EmptyCard'
import { PlusIcon, TrashIcon, ArrowRightLeftIcon, RefreshCwIcon, DatabaseIcon } from 'lucide-react'

const GraphManager = () => {
  const { t } = useTranslation()
  const [graphs, setGraphs] = useState<GraphInfo[]>([])
  const [currentGraph, setCurrentGraph] = useState<GraphInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newGraphName, setNewGraphName] = useState('')
  const [newGraphDescription, setNewGraphDescription] = useState('')

  // 加载图谱数据
  const loadGraphsData = useCallback(async () => {
    setLoading(true)
    try {
      const [graphsResponse, currentResponse] = await Promise.all([
        listGraphs(),
        getCurrentGraph()
      ])
      
      setGraphs(graphsResponse.graphs || [])
      setCurrentGraph(currentResponse.current_graph)
    } catch (error) {
      console.error('Failed to load graphs:', error)
      toast.error(t('graph.loadError', 'Failed to load graphs'))
    } finally {
      setLoading(false)
    }
  }, [t])

  // 初始加载
  useEffect(() => {
    loadGraphsData()
  }, [loadGraphsData])

  // 创建图谱
  const handleCreateGraph = async () => {
    if (!newGraphName.trim()) {
      toast.error(t('graph.nameRequired', 'Graph name is required'))
      return
    }

    setCreating(true)
    try {
      await createGraph(newGraphName.trim(), newGraphDescription.trim())
      toast.success(t('graph.createSuccess', 'Graph created successfully'))
      setShowCreateDialog(false)
      setNewGraphName('')
      setNewGraphDescription('')
      await loadGraphsData()
    } catch (error) {
      console.error('Failed to create graph:', error)
      toast.error(t('graph.createError', 'Failed to create graph'))
    } finally {
      setCreating(false)
    }
  }

  // 切换图谱
  const handleSwitchGraph = async (graphName: string) => {
    try {
      await switchGraph(graphName)
      toast.success(t('graph.switchSuccess', `Switched to graph: ${graphName}`))
      await loadGraphsData()
    } catch (error) {
      console.error('Failed to switch graph:', error)
      toast.error(t('graph.switchError', 'Failed to switch graph'))
    }
  }

  // 删除图谱
  const handleDeleteGraph = async (graphName: string) => {
    try {
      await deleteGraph(graphName)
      toast.success(t('graph.deleteSuccess', 'Graph deleted successfully'))
      await loadGraphsData()
    } catch (error) {
      console.error('Failed to delete graph:', error)
      toast.error(t('graph.deleteError', 'Failed to delete graph'))
    }
  }

  // 格式化日期
  const formatDate = (dateString: string) => {
    if (!dateString) return t('common.unknown', 'Unknown')
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="flex h-full flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b p-4">
        <div>
          <h1 className="text-2xl font-bold">{t('graph.title', 'Graph Management')}</h1>
          <p className="text-muted-foreground">
            {t('graph.description', 'Manage multiple knowledge graphs')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadGraphsData}
            disabled={loading}
          >
            <RefreshCwIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            {t('common.refresh', 'Refresh')}
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm">
                <PlusIcon className="h-4 w-4" />
                {t('graph.create', 'Create Graph')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('graph.createTitle', 'Create New Graph')}</DialogTitle>
                <DialogDescription>
                  {t('graph.createDescription', 'Create a new knowledge graph with a unique name and description.')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">
                    {t('graph.name', 'Graph Name')} *
                  </label>
                  <Input
                    value={newGraphName}
                    onChange={(e) => setNewGraphName(e.target.value)}
                    placeholder={t('graph.namePlaceholder', 'Enter graph name')}
                    maxLength={100}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('graph.description', 'Description')}
                  </label>
                  <Input
                    value={newGraphDescription}
                    onChange={(e) => setNewGraphDescription(e.target.value)}
                    placeholder={t('graph.descriptionPlaceholder', 'Enter description (optional)')}
                    maxLength={500}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateDialog(false)}
                >
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button
                  onClick={handleCreateGraph}
                  disabled={!newGraphName.trim() || creating}
                >
                  {creating ? t('common.creating', 'Creating...') : t('common.create', 'Create')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* 当前图谱信息 */}
      {currentGraph && (
        <div className="border-b p-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <DatabaseIcon className="h-5 w-5" />
                  {t('graph.current', 'Current Graph')}: {currentGraph.name}
                </CardTitle>
                <Badge variant="default">{t('graph.active', 'Active')}</Badge>
              </div>
              <CardDescription>{currentGraph.description || t('graph.noDescription', 'No description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-6 text-sm text-muted-foreground">
                <span>{t('graph.entities', 'Entities')}: {currentGraph.entity_count}</span>
                <span>{t('graph.relations', 'Relations')}: {currentGraph.relation_count}</span>
                <span>{t('graph.created', 'Created')}: {formatDate(currentGraph.created_at)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 图谱列表 */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4">
            <h2 className="mb-4 text-lg font-semibold">{t('graph.allGraphs', 'All Graphs')}</h2>
            
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCwIcon className="h-6 w-6 animate-spin" />
                <span className="ml-2">{t('common.loading', 'Loading...')}</span>
              </div>
            ) : graphs.length === 0 ? (
              <EmptyCard
                title={t('graph.noGraphs', 'No Graphs')}
                description={t('graph.noGraphsDescription', 'Create your first knowledge graph to get started.')}
                icon={DatabaseIcon}
                action={
                  <Button onClick={() => setShowCreateDialog(true)}>
                    <PlusIcon className="h-4 w-4" />
                    {t('graph.create', 'Create Graph')}
                  </Button>
                }
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {graphs.map((graph) => (
                  <Card key={graph.name} className={graph.is_active ? 'border-primary' : ''}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">{graph.name}</CardTitle>
                          <CardDescription className="mt-1">
                            {graph.description || t('graph.noDescription', 'No description')}
                          </CardDescription>
                        </div>
                        {graph.is_active && (
                          <Badge variant="default" className="ml-2">
                            {t('graph.active', 'Active')}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div className="flex justify-between">
                          <span>{t('graph.entities', 'Entities')}:</span>
                          <span>{graph.entity_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>{t('graph.relations', 'Relations')}:</span>
                          <span>{graph.relation_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>{t('graph.created', 'Created')}:</span>
                          <span>{formatDate(graph.created_at)}</span>
                        </div>
                      </div>
                      
                      <Separator className="my-3" />
                      
                      <div className="flex gap-2">
                        {!graph.is_active && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSwitchGraph(graph.name)}
                            className="flex-1"
                          >
                            <ArrowRightLeftIcon className="h-4 w-4" />
                            {t('graph.switch', 'Switch')}
                          </Button>
                        )}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={graph.is_active}
                              className="text-destructive hover:text-destructive"
                            >
                              <TrashIcon className="h-4 w-4" />
                              {t('common.delete', 'Delete')}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>{t('graph.deleteConfirmTitle', 'Delete Graph')}</AlertDialogTitle>
                              <AlertDialogDescription>
                                {t('graph.deleteConfirmDescription', `Are you sure you want to delete the graph "${graph.name}"? This action cannot be undone.`)}
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>{t('common.cancel', 'Cancel')}</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteGraph(graph.name)}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                {t('common.delete', 'Delete')}
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}

export default GraphManager
