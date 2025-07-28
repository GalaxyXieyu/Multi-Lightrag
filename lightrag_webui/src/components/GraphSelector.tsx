import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { DatabaseIcon, PlusIcon, SettingsIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useGraphState } from '@/stores/state'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '@/components/ui/Select'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip'
import { toast } from 'sonner'
import CreateGraphDialog from '@/components/graph/CreateGraphDialog'

interface GraphInfo {
  graph_id: string
  name: string
  description: string
  is_active: boolean
  entity_count: number
  relation_count: number
  document_count: number
  created_at: string
  updated_at: string
}

interface GraphSelectorProps {
  className?: string
}

export function GraphSelector({ className }: GraphSelectorProps) {
  const { t } = useTranslation()
  const [graphs, setGraphs] = useState<GraphInfo[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Use global graph state
  const currentGraph = useGraphState((state) => state.currentGraph)
  const refreshCurrentGraph = useGraphState((state) => state.refreshCurrentGraph)

  // 加载图谱列表
  const loadGraphs = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/graphs/list')
      if (response.ok) {
        const data = await response.json()
        setGraphs(data.graphs || [])

        // 同时刷新全局当前图谱状态
        await refreshCurrentGraph()
      }
    } catch (error) {
      console.error('Failed to load graphs:', error)
      toast.error(t('graph.loadError', 'Failed to load graphs'))
    } finally {
      setIsLoading(false)
    }
  }

  // 切换图谱
  const switchGraph = async (graphId: string) => {
    // 处理特殊值
    if (graphId === '__manage__') {
      toast.info(t('graph.manageTodo', 'Graph management feature coming soon'))
      return
    }

    try {
      const response = await fetch(`/graphs/${graphId}/switch`, {
        method: 'POST',
      })

      if (response.ok) {
        await loadGraphs() // 重新加载图谱列表
        await refreshCurrentGraph() // 刷新全局当前图谱状态
        toast.success(t('graph.switchSuccess', 'Graph switched successfully'))
      } else {
        throw new Error('Failed to switch graph')
      }
    } catch (error) {
      console.error('Failed to switch graph:', error)
      toast.error(t('graph.switchError', 'Failed to switch graph'))
    }
  }

  // 组件挂载时加载图谱
  useEffect(() => {
    loadGraphs()
  }, [])

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <DatabaseIcon className="h-4 w-4 text-muted-foreground" />

      <Select
        value={currentGraph?.graph_id || ''}
        onValueChange={switchGraph}
        disabled={isLoading}
      >
        <SelectTrigger className="w-[180px] h-8 text-sm">
          <SelectValue
            placeholder={t('graph.selectGraph', 'Select Graph')}
          >
            {currentGraph ? (
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{currentGraph.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {t('graph.active', 'Active')}
                </Badge>
              </div>
            ) : (
              t('graph.selectGraph', 'Select Graph')
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>{t('graph.availableGraphs', 'Available Graphs')}</SelectLabel>
            {graphs.map((graph) => (
              <SelectItem key={graph.graph_id} value={graph.graph_id}>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center justify-between w-full">
                        <span className="font-medium">{graph.name}</span>
                        {graph.is_active && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {t('graph.active', 'Active')}
                          </Badge>
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <div className="text-sm">
                        <div className="font-medium">{graph.name}</div>
                        <div className="text-muted-foreground">
                          {graph.entity_count} entities, {graph.relation_count} relations
                        </div>
                        <div className="text-muted-foreground">
                          {graph.document_count} documents
                        </div>
                        <div className="text-muted-foreground">
                          {graph.description || t('graph.noDescription', 'No description')}
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </SelectItem>
            ))}
          </SelectGroup>

          {graphs.length === 0 && !isLoading && (
            <div className="px-2 py-4 text-center text-sm text-muted-foreground">
              {t('graph.noGraphsFound', 'No graphs found')}
            </div>
          )}

          {isLoading && (
            <div className="px-2 py-4 text-center text-sm text-muted-foreground">
              {t('graph.loading', 'Loading...')}
            </div>
          )}

          <SelectSeparator />

          <SelectItem value="__manage__">
            <div className="flex items-center gap-2">
              <SettingsIcon className="h-4 w-4" />
              {t('graph.manage', 'Manage Graphs')}
            </div>
          </SelectItem>
        </SelectContent>
      </Select>

      {/* 创建图谱按钮 */}
      <CreateGraphDialog
        onGraphCreated={loadGraphs}
        trigger={
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" className="h-8 px-2">
                  <PlusIcon className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{t('graph.createNew', 'Create New Graph')}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        }
      />
    </div>
  )
}

export function GraphStatusIndicator() {
  const { t } = useTranslation()

  // Use global graph state
  const currentGraph = useGraphState((state) => state.currentGraph)
  const isLoading = useGraphState((state) => state.isLoading)
  const loadCurrentGraph = useGraphState((state) => state.loadCurrentGraph)

  useEffect(() => {
    // Load current graph on mount
    loadCurrentGraph()

    // 定期更新状态
    const interval = setInterval(loadCurrentGraph, 30000) // 30秒更新一次
    return () => clearInterval(interval)
  }, [loadCurrentGraph])

  if (!currentGraph) {
    return (
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <div className="h-2 w-2 rounded-full bg-gray-400" />
        {t('graph.noGraph', 'No Graph')}
      </div>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-1 text-xs cursor-default">
            <div className={cn(
              "h-2 w-2 rounded-full",
              isLoading ? "bg-yellow-500 animate-pulse" : "bg-green-500"
            )} />
            <span className="font-medium truncate max-w-[100px]">
              {currentGraph.name}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <div className="text-sm">
            <div className="font-medium">{currentGraph.name}</div>
            <div className="text-muted-foreground">
              {currentGraph.entity_count} entities, {currentGraph.relation_count} relations
            </div>
            <div className="text-muted-foreground">
              {currentGraph.document_count} documents
            </div>
            <div className="text-muted-foreground">
              {t('graph.lastUpdated', 'Updated')}: {new Date(currentGraph.updated_at).toLocaleDateString()}
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
