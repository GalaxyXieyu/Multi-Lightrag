import { useState, useCallback, useEffect } from 'react'
import { FileRejection } from 'react-dropzone'
import Button from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import FileUploader from '@/components/ui/FileUploader'
import { toast } from 'sonner'
import { errorMessage } from '@/lib/utils'
import { uploadDocument, listGraphs } from '@/api/lightrag'
import { useGraphState } from '@/stores/state'

import { UploadIcon, DatabaseIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface UploadDocumentsDialogProps {
  onDocumentsUploaded?: () => Promise<void>
}

interface GraphInfo {
  graph_id: string
  name: string
  description: string
  is_active: boolean
}

export default function UploadDocumentsDialog({ onDocumentsUploaded }: UploadDocumentsDialogProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [progresses, setProgresses] = useState<Record<string, number>>({})
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({})
  const [selectedGraphId, setSelectedGraphId] = useState<string>('')
  const [graphs, setGraphs] = useState<GraphInfo[]>([])
  const [isLoadingGraphs, setIsLoadingGraphs] = useState(false)

  // 获取当前图谱状态
  const currentGraph = useGraphState.use.currentGraph()

  // 加载图谱列表
  const loadGraphs = useCallback(async () => {
    setIsLoadingGraphs(true)
    try {
      const data = await listGraphs()
      setGraphs(data.graphs || [])

      // 优先使用当前活跃图谱，否则使用第一个图谱
      if (currentGraph?.graph_id) {
        setSelectedGraphId(currentGraph.graph_id)
      } else {
        const activeGraph = data.graphs?.find((g: GraphInfo) => g.is_active)
        if (activeGraph) {
          setSelectedGraphId(activeGraph.graph_id)
        } else if (data.graphs?.length > 0) {
          setSelectedGraphId(data.graphs[0].graph_id)
        }
      }
    } catch (error) {
      console.error('Failed to load graphs:', error)
      toast.error(t('graph.loadError', 'Failed to load graphs'))
    } finally {
      setIsLoadingGraphs(false)
    }
  }, [t, currentGraph])

  // 组件挂载时加载图谱
  useEffect(() => {
    if (open) {
      loadGraphs()
    }
  }, [open, loadGraphs])

  const handleRejectedFiles = useCallback(
    (rejectedFiles: FileRejection[]) => {
      // Process rejected files and add them to fileErrors
      rejectedFiles.forEach(({ file, errors }) => {
        // Get the first error message
        let errorMsg = errors[0]?.message || t('documentPanel.uploadDocuments.fileUploader.fileRejected', { name: file.name })

        // Simplify error message for unsupported file types
        if (errorMsg.includes('file-invalid-type')) {
          errorMsg = t('documentPanel.uploadDocuments.fileUploader.unsupportedType')
        }

        // Set progress to 100% to display error message
        setProgresses((pre) => ({
          ...pre,
          [file.name]: 100
        }))

        // Add error message to fileErrors
        setFileErrors(prev => ({
          ...prev,
          [file.name]: errorMsg
        }))
      })
    },
    [setProgresses, setFileErrors, t]
  )

  const handleDocumentsUpload = useCallback(
    async (filesToUpload: File[]) => {
      setIsUploading(true)
      let hasSuccessfulUpload = false

      // Only clear errors for files that are being uploaded, keep errors for rejected files
      setFileErrors(prev => {
        const newErrors = { ...prev };
        filesToUpload.forEach(file => {
          delete newErrors[file.name];
        });
        return newErrors;
      });

      // Show uploading toast
      const toastId = toast.loading(t('documentPanel.uploadDocuments.batch.uploading'))

      try {
        // Track errors locally to ensure we have the final state
        const uploadErrors: Record<string, string> = {}

        // Create a collator that supports Chinese sorting
        const collator = new Intl.Collator(['zh-CN', 'en'], {
          sensitivity: 'accent',  // consider basic characters, accents, and case
          numeric: true           // enable numeric sorting, e.g., "File 10" will be after "File 2"
        });
        const sortedFiles = [...filesToUpload].sort((a, b) =>
          collator.compare(a.name, b.name)
        );

        // Upload files in sequence, not parallel
        for (const file of sortedFiles) {
          try {
            // Initialize upload progress
            setProgresses((pre) => ({
              ...pre,
              [file.name]: 0
            }))

            const result = await uploadDocument(file, (percentCompleted: number) => {
              console.debug(t('documentPanel.uploadDocuments.single.uploading', { name: file.name, percent: percentCompleted }))
              setProgresses((pre) => ({
                ...pre,
                [file.name]: percentCompleted
              }))
            }, selectedGraphId || undefined)

            if (result.status === 'duplicated') {
              uploadErrors[file.name] = t('documentPanel.uploadDocuments.fileUploader.duplicateFile')
              setFileErrors(prev => ({
                ...prev,
                [file.name]: t('documentPanel.uploadDocuments.fileUploader.duplicateFile')
              }))
            } else if (result.status !== 'success') {
              uploadErrors[file.name] = result.message
              setFileErrors(prev => ({
                ...prev,
                [file.name]: result.message
              }))
            } else {
              // Mark that we had at least one successful upload
              hasSuccessfulUpload = true
            }
          } catch (err) {
            console.error(`Upload failed for ${file.name}:`, err)

            // Handle HTTP errors, including 400 errors
            let errorMsg = errorMessage(err)

            // If it's an axios error with response data, try to extract more detailed error info
            if (err && typeof err === 'object' && 'response' in err) {
              const axiosError = err as { response?: { status: number, data?: { detail?: string } } }
              if (axiosError.response?.status === 400) {
                // Extract specific error message from backend response
                errorMsg = axiosError.response.data?.detail || errorMsg
              }

              // Set progress to 100% to display error message
              setProgresses((pre) => ({
                ...pre,
                [file.name]: 100
              }))
            }

            // Record error message in both local tracking and state
            uploadErrors[file.name] = errorMsg
            setFileErrors(prev => ({
              ...prev,
              [file.name]: errorMsg
            }))
          }
        }

        // Check if any files failed to upload using our local tracking
        const hasErrors = Object.keys(uploadErrors).length > 0

        // Update toast status
        if (hasErrors) {
          toast.error(t('documentPanel.uploadDocuments.batch.error'), { id: toastId })
        } else {
          toast.success(t('documentPanel.uploadDocuments.batch.success'), { id: toastId })
        }

        // Only update if at least one file was uploaded successfully
        if (hasSuccessfulUpload) {
          // Refresh document list
          if (onDocumentsUploaded) {
            onDocumentsUploaded().catch(err => {
              console.error('Error refreshing documents:', err)
            })
          }
        }
      } catch (err) {
        console.error('Unexpected error during upload:', err)
        toast.error(t('documentPanel.uploadDocuments.generalError', { error: errorMessage(err) }), { id: toastId })
      } finally {
        setIsUploading(false)
      }
    },
    [setIsUploading, setProgresses, setFileErrors, t, onDocumentsUploaded]
  )

  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        if (isUploading) {
          return
        }
        if (!open) {
          setProgresses({})
          setFileErrors({})
        }
        setOpen(open)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="default" side="bottom" tooltip={t('documentPanel.uploadDocuments.tooltip')} size="sm">
          <UploadIcon /> {t('documentPanel.uploadDocuments.button')}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl" onCloseAutoFocus={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>{t('documentPanel.uploadDocuments.title')}</DialogTitle>
          <DialogDescription>
            {t('documentPanel.uploadDocuments.description')}
          </DialogDescription>
        </DialogHeader>

        {/* 图谱选择器 */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <DatabaseIcon className="h-4 w-4" />
            {t('documentPanel.uploadDocuments.targetGraph', 'Target Graph')}
          </label>
          <Select
            value={selectedGraphId}
            onValueChange={setSelectedGraphId}
            disabled={isLoadingGraphs || isUploading}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  isLoadingGraphs
                    ? t('graph.loading', 'Loading...')
                    : t('documentPanel.uploadDocuments.selectGraph', 'Select a graph')
                }
              />
            </SelectTrigger>
            <SelectContent>
              {graphs.map((graph) => (
                <SelectItem key={graph.graph_id} value={graph.graph_id}>
                  <div className="flex items-center justify-between w-full">
                    <div className="flex flex-col">
                      <span className="font-medium">{graph.name}</span>
                      {graph.description && (
                        <span className="text-xs text-muted-foreground">
                          {graph.description}
                        </span>
                      )}
                    </div>
                    {graph.is_active && (
                      <span className="ml-2 text-xs text-green-600">
                        {t('graph.active', 'Active')}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
              {graphs.length === 0 && !isLoadingGraphs && (
                <SelectItem value="" disabled>
                  {t('graph.noGraphsFound', 'No graphs found')}
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <FileUploader
          maxFileCount={Infinity}
          maxSize={200 * 1024 * 1024}
          description={t('documentPanel.uploadDocuments.fileTypes')}
          onUpload={handleDocumentsUpload}
          onReject={handleRejectedFiles}
          progresses={progresses}
          fileErrors={fileErrors}
          disabled={isUploading}
        />
      </DialogContent>
    </Dialog>
  )
}
