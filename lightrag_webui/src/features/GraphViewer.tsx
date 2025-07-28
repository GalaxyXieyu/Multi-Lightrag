import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react'
// import { MiniMap } from '@react-sigma/minimap'
import { SigmaContainer, useRegisterEvents, useSigma } from '@react-sigma/core'
import { Settings as SigmaSettings } from 'sigma/settings'
import { GraphSearchOption, OptionItem } from '@react-sigma/graph-search'
import { EdgeArrowProgram, NodePointProgram, NodeCircleProgram } from 'sigma/rendering'
import { NodeBorderProgram } from '@sigma/node-border'
import EdgeCurveProgram, { EdgeCurvedArrowProgram } from '@sigma/edge-curve'
import { Edit, Trash2 } from 'lucide-react'

import FocusOnNode from '@/components/graph/FocusOnNode'
import LayoutsControl from '@/components/graph/LayoutsControl'
import GraphControl from '@/components/graph/GraphControl'
// import ThemeToggle from '@/components/ThemeToggle'
import ZoomControl from '@/components/graph/ZoomControl'
import FullScreenControl from '@/components/graph/FullScreenControl'
import Settings from '@/components/graph/Settings'
import GraphSearch from '@/components/graph/GraphSearch'
import GraphLabels from '@/components/graph/GraphLabels'
import PropertiesView from '@/components/graph/PropertiesView'
import SettingsDisplay from '@/components/graph/SettingsDisplay'
import Legend from '@/components/graph/Legend'
import LegendButton from '@/components/graph/LegendButton'

import { useSettingsStore } from '@/stores/settings'
import { useGraphStore } from '@/stores/graph'
import { useGraphState } from '@/stores/state'
import { useModernDialog } from '@/components/ui/ModernDialog'
import { toast } from 'sonner'
// import NodeCreationModal from '@/components/graph/NodeCreationModal'

import '@react-sigma/core/lib/style.css'
import '@react-sigma/graph-search/lib/style.css'

// Sigma settings
const defaultSigmaSettings: Partial<SigmaSettings> = {
  allowInvalidContainer: true,
  defaultNodeType: 'default',
  defaultEdgeType: 'curvedNoArrow',
  renderEdgeLabels: false,
  edgeProgramClasses: {
    arrow: EdgeArrowProgram,
    curvedArrow: EdgeCurvedArrowProgram,
    curvedNoArrow: EdgeCurveProgram
  },
  nodeProgramClasses: {
    default: NodeBorderProgram,
    circel: NodeCircleProgram,
    point: NodePointProgram
  },
  labelGridCellSize: 60,
  labelRenderedSizeThreshold: 12,
  enableEdgeEvents: true,
  labelColor: {
    color: '#000',
    attribute: 'labelColor'
  },
  edgeLabelColor: {
    color: '#000',
    attribute: 'labelColor'
  },
  edgeLabelSize: 8,
  labelSize: 12
  // minEdgeThickness: 2
  // labelFont: 'Lato, sans-serif'
}

const GraphEvents = () => {
  const registerEvents = useRegisterEvents()
  const sigma = useSigma()
  const enableNodeDrag = useSettingsStore.use.enableNodeDrag()
  const contextMenu = useGraphStore.use.contextMenu()
  const [draggedNode, setDraggedNode] = useState<string | null>(null)
  const [isCreatingNode, setIsCreatingNode] = useState(false)
  const [isConnectingNodes, setIsConnectingNodes] = useState(false)
  const [sourceNode, setSourceNode] = useState<string | null>(null)
  const [showNodeModal, setShowNodeModal] = useState(false)
  const [nodeCreationPosition, setNodeCreationPosition] = useState<{ x: number; y: number } | undefined>()


  // 使用现代化弹窗
  const {
    showSuccess,
    showError,
    showPrompt,
    showConfirm,
    DialogComponent
  } = useModernDialog()


  // 获取当前图谱
  const currentGraph = useGraphState.use.currentGraph()

  // 获取现有节点列表
  const existingNodes = React.useMemo(() => {
    const graph = sigma.getGraph()
    return graph.nodes().map(nodeId => ({
      id: nodeId,
      label: graph.getNodeAttribute(nodeId, 'label') || nodeId
    }))
  }, [sigma])

  // 打开节点创建模态框
  const openNodeCreationModal = (x: number, y: number) => {
    setNodeCreationPosition({ x, y })
    setShowNodeModal(true)
    setIsCreatingNode(false)
  }

  // 节点创建成功后的回调
  const handleNodeCreated = () => {
    // 刷新图谱数据
    window.location.reload() // 简单的刷新方式，后续可以优化为局部刷新
  }





  // 创建节点间关系的函数
  const createRelation = async (sourceNodeId: string, targetNodeId: string) => {
    showPrompt(
      '创建关系',
      '请输入关系描述:',
      async (relationDescription) => {
        const description = relationDescription || '手动创建的关系'
        await performCreateRelation(sourceNodeId, targetNodeId, description)
      },
      undefined,
      '手动创建的关系',
      '例如：朋友、同事、合作伙伴等',
      false
    )
  }

  // 执行关系创建的实际逻辑
  const performCreateRelation = async (sourceNodeId: string, targetNodeId: string, relationDescription: string) => {
    try {
      const graphId = currentGraph?.graph_id || 'default'
      const response = await fetch(`/graphs/relations?graph_id=${encodeURIComponent(graphId)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_entity: sourceNodeId,
          target_entity: targetNodeId,
          description: relationDescription,
          keywords: relationDescription,
          weight: 1.0,
          source_id: 'manual_creation',
          file_path: 'manual_input'
        })
      })

      console.log('关系创建响应状态:', response.status, response.statusText)
      const responseData = await response.json()
      console.log('关系创建响应数据:', responseData)

      if (response.ok) {
        // 在图谱中添加新边
        const graph = sigma.getGraph()
        const edgeId = `${sourceNodeId}-${targetNodeId}`

        if (!graph.hasEdge(edgeId)) {
          graph.addEdge(sourceNodeId, targetNodeId, {
            label: relationDescription,
            size: 1,
            type: 'curvedNoArrow',
            color: '#6b7280'
          })
        }

        console.log(`关系 "${sourceNodeId}" -> "${targetNodeId}" 创建成功`)
        showSuccess('关系创建成功', responseData.message || '关系已成功创建并添加到图谱中')
        toast.success(`关系 "${sourceNodeId}" -> "${targetNodeId}" 创建成功`)
      } else {
        console.error('创建关系失败，状态码:', response.status)
        console.error('错误详情:', responseData)
        showError('关系创建失败', responseData.detail || responseData.message || '请检查网络连接后重试')
      }
    } catch (error) {
      console.error('创建关系时发生错误:', error)
      showError('创建关系时发生错误', '网络连接异常，请稍后重试')
    }
  }





  useEffect(() => {
    // Register the events
    registerEvents({
      downNode: (e) => {
        // 检查是否为左键点击（button === 0），右键点击不应该触发拖动
        const mouseEvent = e.original as MouseEvent
        if (mouseEvent && mouseEvent.button !== 0) {
          return // 非左键点击，直接返回
        }

        // 如果右键菜单显示，不处理任何拖拽操作
        if (contextMenu.show) {
          return
        }

        if (isConnectingNodes) {
          // 连接模式：选择源节点
          if (!sourceNode) {
            setSourceNode(e.node)
            sigma.getGraph().setNodeAttribute(e.node, 'highlighted', true)
          } else if (sourceNode !== e.node) {
            // 选择目标节点，创建关系
            createRelation(sourceNode, e.node)
            sigma.getGraph().removeNodeAttribute(sourceNode, 'highlighted')
            setSourceNode(null)
            setIsConnectingNodes(false)
          }
        } else if (enableNodeDrag) {
          // 普通拖拽模式（只有在启用拖拽时才执行）
          setDraggedNode(e.node)
          sigma.getGraph().setNodeAttribute(e.node, 'highlighted', true)
        }
      },
      // 双击节点编辑
      doubleClickNode: (e) => {
        editNode(e.node)
      },

      // On mouse move, if the drag mode is enabled, we change the position of the draggedNode
      mousemovebody: (e) => {
        // 如果右键菜单显示，禁用拖动
        if (contextMenu.show) return
        if (!draggedNode || isConnectingNodes || !enableNodeDrag) return
        // Get new position of node
        const pos = sigma.viewportToGraph(e)
        sigma.getGraph().setNodeAttribute(draggedNode, 'x', pos.x)
        sigma.getGraph().setNodeAttribute(draggedNode, 'y', pos.y)

        // Prevent sigma to move camera:
        e.preventSigmaDefault()
        e.original.preventDefault()
        e.original.stopPropagation()
      },
      // On mouse up, we reset the autoscale and the dragging mode
      mouseup: () => {
        // 如果右键菜单显示，不处理拖动结束
        if (contextMenu.show) return
        if (draggedNode && !isConnectingNodes && enableNodeDrag) {
          setDraggedNode(null)
          sigma.getGraph().removeNodeAttribute(draggedNode, 'highlighted')
        }
      },
      // 点击空白区域创建节点
      clickStage: (e) => {
        if (isCreatingNode) {
          const pos = sigma.viewportToGraph(e)
          openNodeCreationModal(pos.x, pos.y)
        } else if (isConnectingNodes && sourceNode) {
          // 取消连接模式
          sigma.getGraph().removeNodeAttribute(sourceNode, 'highlighted')
          setSourceNode(null)
          setIsConnectingNodes(false)
        }
      },

      // Disable the autoscale at the first down interaction
      mousedown: (e) => {
        // Only set custom BBox if it's a drag operation (mouse button is pressed)
        const mouseEvent = e.original as MouseEvent;
        if (mouseEvent && mouseEvent.buttons !== 0 && !sigma.getCustomBBox()) {
          sigma.setCustomBBox(sigma.getBBox())
        }
      }
    })
  }, [registerEvents, sigma, draggedNode, isCreatingNode, isConnectingNodes, sourceNode, enableNodeDrag, contextMenu])

  // 监听键盘事件
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'n' || e.key === 'N') {
        setIsCreatingNode(true)
        console.log('进入节点创建模式，点击空白处创建节点')
      } else if (e.key === 'c' || e.key === 'C') {
        setIsConnectingNodes(true)
        console.log('进入连接模式，点击两个节点创建关系')
      } else if (e.key === 'Escape') {
        setIsCreatingNode(false)
        setIsConnectingNodes(false)
        if (sourceNode) {
          sigma.getGraph().removeNodeAttribute(sourceNode, 'highlighted')
          setSourceNode(null)
        }
        console.log('退出编辑模式')
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [sigma, sourceNode])

  // 当右键菜单显示时，清除拖拽状态
  useEffect(() => {
    if (contextMenu.show && draggedNode) {
      // 清除拖拽状态和高亮
      sigma.getGraph().removeNodeAttribute(draggedNode, 'highlighted')
      setDraggedNode(null)
    }
  }, [contextMenu.show, draggedNode, sigma])

  // 渲染操作提示和模态框
  return (
    <>
      <div className="absolute top-2 left-1/2 transform -translate-x-1/2 z-50">
        {(isCreatingNode || isConnectingNodes) && (
          <div className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg">
            {isCreatingNode && (
              <div className="text-center">
                <div className="font-semibold">节点创建模式</div>
                <div className="text-sm">点击空白处创建节点 | 按 ESC 退出</div>
              </div>
            )}
            {isConnectingNodes && (
              <div className="text-center">
                <div className="font-semibold">连接模式</div>
                <div className="text-sm">
                  {sourceNode ? '点击目标节点创建关系' : '点击源节点开始连接'} | 按 ESC 退出
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {showNodeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-lg font-semibold mb-4">创建新节点</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">节点名称</label>
                <input
                  type="text"
                  className="w-full border rounded px-3 py-2"
                  placeholder="输入节点名称"
                  id="simple-node-name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">节点类型</label>
                <select className="w-full border rounded px-3 py-2">
                  <option value="entity">实体</option>
                  <option value="concept">概念</option>
                  <option value="event">事件</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">描述</label>
                <textarea
                  className="w-full border rounded px-3 py-2"
                  placeholder="输入节点描述"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                className="px-4 py-2 border rounded hover:bg-gray-50"
                onClick={() => setShowNodeModal(false)}
              >
                取消
              </button>
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => {
                  const nameInput = document.getElementById('simple-node-name') as HTMLInputElement
                  if (nameInput?.value) {
                    showSuccess('节点创建成功', `节点 "${nameInput.value}" 已创建`)
                    setShowNodeModal(false)
                  }
                }}
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}


    </>
  )
}

const GraphViewer = () => {
  const [sigmaSettings, setSigmaSettings] = useState(defaultSigmaSettings)
  const sigmaRef = useRef<any>(null)

  const selectedNode = useGraphStore.use.selectedNode()
  const focusedNode = useGraphStore.use.focusedNode()
  const moveToSelectedNode = useGraphStore.use.moveToSelectedNode()
  const isFetching = useGraphStore.use.isFetching()

  const showPropertyPanel = useSettingsStore.use.showPropertyPanel()
  const showNodeSearchBar = useSettingsStore.use.showNodeSearchBar()
  const enableNodeDrag = useSettingsStore.use.enableNodeDrag()
  const showLegend = useSettingsStore.use.showLegend()

  // 获取右键菜单状态
  const contextMenu = useGraphStore.use.contextMenu()
  const setContextMenu = useGraphStore.use.setContextMenu()

  // 使用现代化弹窗
  const {
    showSuccess,
    showError,
    showPrompt,
    showConfirm,
    DialogComponent
  } = useModernDialog()

  // 编辑节点状态
  const [editingNode, setEditingNode] = useState<{
    nodeId: string
    name: string
    type: string
    description: string
  } | null>(null)

  // 编辑关系状态
  const [editingRelation, setEditingRelation] = useState<{
    edgeId: string
    sourceId: string
    targetId: string
    description: string
  } | null>(null)

  // 编辑节点
  const editNode = async (nodeId: string) => {
    try {
      const state = useGraphStore.getState()
      const graph = state.sigmaGraph
      const rawGraph = state.rawGraph

      if (!graph || !rawGraph) return

      // 从sigma图谱获取显示名称
      const currentName = graph.getNodeAttribute(nodeId, 'label') || nodeId

      // 从rawGraph获取原始节点数据
      const rawNode = rawGraph.getNode(nodeId)
      const currentDescription = rawNode?.properties?.description || ''
      const currentType = rawNode?.properties?.entity_type || 'UNKNOWN'

      setEditingNode({
        nodeId,
        name: currentName,
        type: currentType,
        description: currentDescription
      })
    } catch (error) {
      console.error('编辑节点时发生错误:', error)
      showError('编辑节点时发生错误', '无法获取节点信息')
    }
  }

  // 编辑关系
  const editRelation = async (edgeId: string, sourceId: string, targetId: string) => {
    try {
      const graph = useGraphStore.getState().sigmaGraph
      if (!graph) return

      const currentDescription = graph.getEdgeAttribute(edgeId, 'label') || '关系'

      setEditingRelation({
        edgeId,
        sourceId,
        targetId,
        description: currentDescription
      })
    } catch (error) {
      console.error('编辑关系时发生错误:', error)
      showError('编辑关系时发生错误', '无法获取关系信息')
    }
  }

  // 保存节点编辑
  const saveNodeEdit = async () => {
    if (!editingNode) return

    try {
      const state = useGraphStore.getState()
      const graph = state.sigmaGraph
      const rawGraph = state.rawGraph

      if (!graph || !rawGraph) return

      // 从sigma图谱获取显示名称
      const currentName = graph.getNodeAttribute(editingNode.nodeId, 'label') || editingNode.nodeId

      // 从rawGraph获取原始节点数据
      const rawNode = rawGraph.getNode(editingNode.nodeId)
      const currentDescription = rawNode?.properties?.description || ''
      const currentType = rawNode?.properties?.entity_type || 'UNKNOWN'

      // 检查是否有变化
      if (editingNode.name === currentName &&
          editingNode.type === currentType &&
          editingNode.description === currentDescription) {
        setEditingNode(null)
        return
      }

      const response = await fetch('/graph/entity/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_name: editingNode.nodeId,
          updated_data: {
            entity_name: editingNode.name,
            entity_type: editingNode.type,
            description: editingNode.description
          },
          allow_rename: true
        })
      })

      if (response.ok) {
        // 更新sigma图形显示
        graph.setNodeAttribute(editingNode.nodeId, 'label', editingNode.name)

        // 更新rawGraph中的properties
        const rawNode = rawGraph.getNode(editingNode.nodeId)
        if (rawNode) {
          rawNode.properties.description = editingNode.description
          rawNode.properties.entity_type = editingNode.type
          if (editingNode.name !== editingNode.nodeId) {
            rawNode.properties.entity_id = editingNode.name
          }
        }

        setEditingNode(null)
        showSuccess('节点编辑成功', `节点已成功更新`)
      } else {
        const errorData = await response.json()
        showError('编辑节点失败', errorData.detail || '无法更新节点，请检查网络连接后重试')
      }
    } catch (error) {
      console.error('编辑节点时发生错误:', error)
      showError('编辑节点时发生错误', '网络连接异常，请稍后重试')
    }
  }

  // 保存关系编辑
  const saveRelationEdit = async () => {
    if (!editingRelation) return

    try {
      const graph = useGraphStore.getState().sigmaGraph
      if (!graph) return

      const currentDescription = graph.getEdgeAttribute(editingRelation.edgeId, 'label') || '关系'

      // 检查是否有变化
      if (editingRelation.description === currentDescription) {
        setEditingRelation(null)
        return
      }

      const response = await fetch('/graph/relation/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_entity: editingRelation.sourceId,
          target_entity: editingRelation.targetId,
          description: editingRelation.description
        })
      })

      if (response.ok) {
        // 更新图形显示
        graph.setEdgeAttribute(editingRelation.edgeId, 'label', editingRelation.description)

        setEditingRelation(null)
        showSuccess('关系编辑成功', '关系已成功更新')
      } else {
        const errorData = await response.json()
        showError('关系编辑失败', errorData.detail || '无法更新关系，请检查网络连接后重试')
      }
    } catch (error) {
      console.error('编辑关系时发生错误:', error)
      showError('编辑关系时发生错误', '网络连接异常，请稍后重试')
    }
  }

  // 删除节点
  const deleteNodeById = (nodeId: string) => {
    const handleConfirm = async () => {
      try {
        const response = await fetch(`/graphs/nodes/${encodeURIComponent(nodeId)}`, {
          method: 'DELETE'
        })

        if (response.ok) {
          const graph = useGraphStore.getState().sigmaGraph
          if (graph && graph.hasNode(nodeId)) {
            graph.dropNode(nodeId)
          }
          showSuccess('节点删除成功', '节点及其相关关系已被删除')
        } else {
          const errorData = await response.json()
          showError('删除节点失败', errorData.detail || '无法删除节点，请检查网络连接后重试')
        }
      } catch (error) {
        console.error('删除节点时发生错误:', error)
        showError('删除节点时发生错误', '网络连接异常，请稍后重试')
      }
    }

    showConfirm(
      '确认删除节点',
      `确定要删除节点 "${nodeId}" 吗？此操作将同时删除所有相关关系，且无法撤销。`,
      handleConfirm,
      undefined,
      '删除',
      '取消'
    )
  }

  // 删除关系
  const deleteRelationById = (sourceId: string, targetId: string) => {
    const handleConfirm = async () => {
      try {
        const response = await fetch(`/graphs/relations/${encodeURIComponent(sourceId)}/${encodeURIComponent(targetId)}`, {
          method: 'DELETE'
        })

        if (response.ok) {
          const graph = useGraphStore.getState().sigmaGraph
          if (graph) {
            // 找到并删除对应的边
            const edges = graph.edges()
            for (const edgeId of edges) {
              if (graph.source(edgeId) === sourceId && graph.target(edgeId) === targetId) {
                graph.dropEdge(edgeId)
                break
              }
            }
          }
          showSuccess('关系删除成功', '关系已被删除')
        } else {
          const errorData = await response.json()
          showError('删除关系失败', errorData.detail || '无法删除关系，请检查网络连接后重试')
        }
      } catch (error) {
        console.error('删除关系时发生错误:', error)
        showError('删除关系时发生错误', '网络连接异常，请稍后重试')
      }
    }

    showConfirm(
      '确认删除关系',
      `确定要删除 "${sourceId}" 和 "${targetId}" 之间的关系吗？此操作无法撤销。`,
      handleConfirm,
      undefined,
      '删除',
      '取消'
    )
  }

  // 添加全局点击事件来关闭右键菜单
  useEffect(() => {
    const handleGlobalClick = () => {
      setContextMenu({ show: false, x: 0, y: 0 })
    }

    if (contextMenu.show) {
      document.addEventListener('click', handleGlobalClick)
      return () => document.removeEventListener('click', handleGlobalClick)
    }
  }, [contextMenu.show, setContextMenu])



  // Initialize sigma settings once on component mount
  // All dynamic settings will be updated in GraphControl using useSetSettings
  useEffect(() => {
    setSigmaSettings(defaultSigmaSettings)
    console.log('Initialized sigma settings')
  }, [])

  // 防止频繁重新渲染导致的闪烁
  const stableSigmaSettings = useMemo(() => ({
    ...sigmaSettings,
    // 添加一些稳定的设置来减少闪烁
    allowInvalidContainer: true,
    renderEdgeLabels: true,
    enableEdgeClickEvents: true,
    enableEdgeWheelEvents: false,
    enableEdgeHoverEvents: true,
  }), [sigmaSettings])

  // Clean up sigma instance when component unmounts
  useEffect(() => {
    return () => {
      // TAB is mount twice in vite dev mode, this is a workaround

      const sigma = useGraphStore.getState().sigmaInstance;
      if (sigma) {
        try {
          // Destroy sigma，and clear WebGL context
          sigma.kill();
          useGraphStore.getState().setSigmaInstance(null);
          console.log('Cleared sigma instance on Graphviewer unmount');
        } catch (error) {
          console.error('Error cleaning up sigma instance:', error);
        }
      }
    };
  }, []);

  // Note: There was a useLayoutEffect hook here to set up the sigma instance and graph data,
  // but testing showed it wasn't executing or having any effect, while the backup mechanism
  // in GraphControl was sufficient. This code was removed to simplify implementation

  const onSearchFocus = useCallback((value: GraphSearchOption | null) => {
    if (value === null) useGraphStore.getState().setFocusedNode(null)
    else if (value.type === 'nodes') useGraphStore.getState().setFocusedNode(value.id)
  }, [])

  const onSearchSelect = useCallback((value: GraphSearchOption | null) => {
    if (value === null) {
      useGraphStore.getState().setSelectedNode(null)
    } else if (value.type === 'nodes') {
      useGraphStore.getState().setSelectedNode(value.id, true)
    }
  }, [])

  const autoFocusedNode = useMemo(() => focusedNode ?? selectedNode, [focusedNode, selectedNode])
  const searchInitSelectedNode = useMemo(
    (): OptionItem | null => (selectedNode ? { type: 'nodes', id: selectedNode } : null),
    [selectedNode]
  )

  // Always render SigmaContainer but control its visibility with CSS
  return (
    <div className="relative h-full w-full overflow-hidden">
      <SigmaContainer
        settings={stableSigmaSettings}
        className="!bg-background !size-full overflow-hidden"
        ref={sigmaRef}
      >
        <GraphControl />

        <GraphEvents />

        <FocusOnNode node={autoFocusedNode} move={moveToSelectedNode} />

        <div className="absolute top-2 left-2 flex items-start gap-2">
          <GraphLabels />
          {showNodeSearchBar && (
            <GraphSearch
              value={searchInitSelectedNode}
              onFocus={onSearchFocus}
              onChange={onSearchSelect}
            />
          )}
        </div>

        <div className="bg-background/60 absolute bottom-2 left-2 flex flex-col rounded-xl border-2 backdrop-blur-lg">
          <LayoutsControl />
          <ZoomControl />
          <FullScreenControl />
          <LegendButton />
          <Settings />
          {/* <ThemeToggle /> */}
        </div>

        {showPropertyPanel && (
          <div className="absolute top-2 right-2">
            <PropertiesView />
          </div>
        )}

        {showLegend && (
          <div className="absolute bottom-10 right-2">
            <Legend className="bg-background/60 backdrop-blur-lg" />
          </div>
        )}

        {/* 快捷键提示 */}
        <div className="absolute bottom-2 right-2 bg-background/80 backdrop-blur-lg rounded-lg border p-3 text-xs">
          <div className="font-semibold mb-2">交互式编辑</div>
          <div className="space-y-1">
            <div><kbd className="bg-gray-200 px-1 rounded">N</kbd> 高级节点创建</div>
            <div><kbd className="bg-gray-200 px-1 rounded">C</kbd> 连接节点</div>
            <div><kbd className="bg-gray-200 px-1 rounded">双击</kbd> 编辑节点</div>
            <div><kbd className="bg-gray-200 px-1 rounded">ESC</kbd> 退出模式</div>
          </div>
        </div>



        {/* <div className="absolute bottom-2 right-2 flex flex-col rounded-xl border-2">
          <MiniMap width="100px" height="100px" />
        </div> */}

        <SettingsDisplay />
      </SigmaContainer>

      {/* 右键菜单 */}
      {contextMenu.show && (
        <div
          className="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-2 z-50 min-w-[150px]"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {contextMenu.nodeId && (
            <>
              <button
                className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm flex items-center gap-2"
                onClick={() => {
                  editNode(contextMenu.nodeId!)
                  setContextMenu({ show: false, x: 0, y: 0 })
                }}
              >
                <Edit className="h-4 w-4" />
                编辑节点
              </button>
              <button
                className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-red-600 dark:text-red-400 flex items-center gap-2"
                onClick={() => {
                  deleteNodeById(contextMenu.nodeId!)
                  setContextMenu({ show: false, x: 0, y: 0 })
                }}
              >
                <Trash2 className="h-4 w-4" />
                删除节点
              </button>
            </>
          )}
          {contextMenu.edgeId && contextMenu.sourceId && contextMenu.targetId && (
            <>
              <button
                className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm flex items-center gap-2"
                onClick={() => {
                  editRelation(contextMenu.edgeId!, contextMenu.sourceId!, contextMenu.targetId!)
                  setContextMenu({ show: false, x: 0, y: 0 })
                }}
              >
                <Edit className="h-4 w-4" />
                编辑关系
              </button>
              <button
                className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm text-red-600 dark:text-red-400 flex items-center gap-2"
                onClick={() => {
                  deleteRelationById(contextMenu.sourceId!, contextMenu.targetId!)
                  setContextMenu({ show: false, x: 0, y: 0 })
                }}
              >
                <Trash2 className="h-4 w-4" />
                删除关系
              </button>
            </>
          )}
        </div>
      )}

      {/* 编辑节点模态对话框 */}
      {editingNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">编辑节点</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">节点名称</label>
                <input
                  type="text"
                  value={editingNode.name}
                  onChange={(e) => setEditingNode({ ...editingNode, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">节点类型</label>
                <input
                  type="text"
                  value={editingNode.type}
                  onChange={(e) => setEditingNode({ ...editingNode, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">节点描述</label>
                <textarea
                  rows={3}
                  value={editingNode.description}
                  onChange={(e) => setEditingNode({ ...editingNode, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                onClick={() => setEditingNode(null)}
              >
                取消
              </button>
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={saveNodeEdit}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑关系模态对话框 */}
      {editingRelation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">编辑关系</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">源节点</label>
                <input
                  type="text"
                  value={editingRelation.sourceId}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">目标节点</label>
                <input
                  type="text"
                  value={editingRelation.targetId}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">关系描述</label>
                <textarea
                  rows={3}
                  value={editingRelation.description}
                  onChange={(e) => setEditingRelation({ ...editingRelation, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="请输入关系描述..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                onClick={() => setEditingRelation(null)}
              >
                取消
              </button>
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={saveRelationEdit}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 现代化弹窗组件 */}
      <DialogComponent />

      {/* Loading overlay - shown when data is loading */}
      {isFetching && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
          <div className="text-center">
            <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <p>Loading Graph Data...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default GraphViewer
