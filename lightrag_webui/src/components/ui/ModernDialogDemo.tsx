import React from 'react'
import { useModernDialog } from '@/components/ui/ModernDialog'
import Button from '@/components/ui/Button'

const ModernDialogDemo: React.FC = () => {
  const {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showConfirm,
    showPrompt,
    DialogComponent
  } = useModernDialog()

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-2xl font-bold mb-6">现代化弹窗组件演示</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <Button
          onClick={() => showSuccess('操作成功', '您的操作已成功完成！')}
          className="bg-green-500 hover:bg-green-600"
        >
          成功提示
        </Button>

        <Button
          onClick={() => showError('操作失败', '抱歉，操作执行失败，请重试。')}
          variant="destructive"
        >
          错误提示
        </Button>

        <Button
          onClick={() => showWarning('注意', '此操作可能会影响系统性能。')}
          className="bg-yellow-500 hover:bg-yellow-600"
        >
          警告提示
        </Button>

        <Button
          onClick={() => showInfo('信息', '这是一条重要的信息提示。')}
          className="bg-blue-500 hover:bg-blue-600"
        >
          信息提示
        </Button>

        <Button
          onClick={() => showConfirm(
            '确认删除',
            '您确定要删除这个项目吗？此操作不可撤销。',
            () => showSuccess('已删除', '项目已成功删除'),
            () => showInfo('已取消', '删除操作已取消'),
            '删除',
            '取消'
          )}
          variant="outline"
        >
          确认对话框
        </Button>

        <Button
          onClick={() => showPrompt(
            '输入名称',
            '请输入新的项目名称：',
            (value) => showSuccess('创建成功', `项目 "${value}" 已创建`),
            () => showInfo('已取消', '创建操作已取消'),
            '我的项目',
            '请输入项目名称',
            true
          )}
          variant="outline"
        >
          输入对话框
        </Button>
      </div>

      {/* 弹窗组件 */}
      <DialogComponent />
    </div>
  )
}

export default ModernDialogDemo
