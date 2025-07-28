import { useCallback } from 'react'
import { QueryMode, QueryRequest } from '@/api/lightrag'
// Removed unused import for Text component
import Checkbox from '@/components/ui/Checkbox'
import NumberInput from '@/components/ui/NumberInput'
import Input from '@/components/ui/Input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/Select'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip'
import { useSettingsStore } from '@/stores/settings'
import { useTranslation } from 'react-i18next'
import { useGraphState } from '@/stores/state'
import Badge from '@/components/ui/Badge'

export default function QuerySettings() {
  const { t } = useTranslation()
  const querySettings = useSettingsStore((state) => state.querySettings)
  const currentGraph = useGraphState.use.currentGraph()

  const handleChange = useCallback((key: keyof QueryRequest, value: any) => {
    useSettingsStore.getState().updateQuerySettings({ [key]: value })
  }, [])

  return (
    <Card className="flex shrink-0 flex-col min-w-[220px]">
      <CardHeader className="px-4 pt-4 pb-2">
        <CardTitle>{t('retrievePanel.querySettings.parametersTitle')}</CardTitle>
        <CardDescription className="sr-only">{t('retrievePanel.querySettings.parametersDescription')}</CardDescription>
      </CardHeader>
      <CardContent className="m-0 flex grow flex-col p-0 text-xs">
        <div className="relative size-full">
          <div className="absolute inset-0 flex flex-col gap-2 overflow-auto px-2">
            {/* Current Graph Info */}
            <>
              <label className="ml-1 text-sm font-medium text-primary">
                {t('retrievePanel.querySettings.currentGraph', '检索图谱')}
              </label>
              <div className={`flex items-center gap-2 p-3 rounded-md text-sm border-2 ${
                currentGraph
                  ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
                  : 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800'
              }`}>
                {currentGraph ? (
                  <>
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="font-semibold text-green-800 dark:text-green-200">
                      {currentGraph.name}
                    </span>
                    {currentGraph.is_active && (
                      <Badge variant="secondary" className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
                        {t('graph.active', 'Active')}
                      </Badge>
                    )}
                    <div className="ml-auto text-xs text-green-600 dark:text-green-400">
                      {currentGraph.entity_count} 实体
                    </div>
                  </>
                ) : (
                  <>
                    <div className="h-2 w-2 rounded-full bg-yellow-500" />
                    <span className="text-yellow-800 dark:text-yellow-200 font-medium">
                      {t('retrievePanel.querySettings.noGraph', '未选择图谱')}
                    </span>
                  </>
                )}
              </div>
            </>

            {/* Query Mode */}
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <label htmlFor="query_mode_select" className="ml-1 cursor-help">
                      {t('retrievePanel.querySettings.queryMode')}
                    </label>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>{t('retrievePanel.querySettings.queryModeTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Select
                value={querySettings.mode}
                onValueChange={(v) => handleChange('mode', v as QueryMode)}
              >
                <SelectTrigger
                  id="query_mode_select"
                  className="hover:bg-primary/5 h-9 cursor-pointer focus:ring-0 focus:ring-offset-0 focus:outline-0 active:right-0"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="naive">{t('retrievePanel.querySettings.queryModeOptions.naive')}</SelectItem>
                    <SelectItem value="local">{t('retrievePanel.querySettings.queryModeOptions.local')}</SelectItem>
                    <SelectItem value="global">{t('retrievePanel.querySettings.queryModeOptions.global')}</SelectItem>
                    <SelectItem value="hybrid">{t('retrievePanel.querySettings.queryModeOptions.hybrid')}</SelectItem>
                    <SelectItem value="mix">{t('retrievePanel.querySettings.queryModeOptions.mix')}</SelectItem>
                    <SelectItem value="bypass">{t('retrievePanel.querySettings.queryModeOptions.bypass')}</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </>

            {/* Response Format */}
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <label htmlFor="response_format_select" className="ml-1 cursor-help">
                      {t('retrievePanel.querySettings.responseFormat')}
                    </label>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>{t('retrievePanel.querySettings.responseFormatTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Select
                value={querySettings.response_type}
                onValueChange={(v) => handleChange('response_type', v)}
              >
                <SelectTrigger
                  id="response_format_select"
                  className="hover:bg-primary/5 h-9 cursor-pointer focus:ring-0 focus:ring-offset-0 focus:outline-0 active:right-0"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="Multiple Paragraphs">{t('retrievePanel.querySettings.responseFormatOptions.multipleParagraphs')}</SelectItem>
                    <SelectItem value="Single Paragraph">{t('retrievePanel.querySettings.responseFormatOptions.singleParagraph')}</SelectItem>
                    <SelectItem value="Bullet Points">{t('retrievePanel.querySettings.responseFormatOptions.bulletPoints')}</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </>

            {/* Top K */}
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <label htmlFor="top_k" className="ml-1 cursor-help">
                      {t('retrievePanel.querySettings.topK')}
                    </label>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>{t('retrievePanel.querySettings.topKTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <div>
                {/* Removed sr-only label */}
                <NumberInput
                  id="top_k"
                  stepper={1}
                  value={querySettings.top_k}
                  onValueChange={(v) => handleChange('top_k', v)}
                  min={1}
                  placeholder={t('retrievePanel.querySettings.topKPlaceholder')}
                />
              </div>
            </>

            {/* Max Tokens */}
            <>
              <>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="max_token_for_text_unit" className="ml-1 cursor-help">
                        {t('retrievePanel.querySettings.maxTokensTextUnit')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.maxTokensTextUnitTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <div>
                  {/* Removed sr-only label */}
                  <NumberInput
                    id="max_token_for_text_unit"
                    stepper={500}
                    value={querySettings.max_token_for_text_unit}
                    onValueChange={(v) => handleChange('max_token_for_text_unit', v)}
                    min={1}
                    placeholder={t('retrievePanel.querySettings.maxTokensTextUnit')}
                  />
                </div>
              </>

              <>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="max_token_for_global_context" className="ml-1 cursor-help">
                        {t('retrievePanel.querySettings.maxTokensGlobalContext')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.maxTokensGlobalContextTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <div>
                  {/* Removed sr-only label */}
                  <NumberInput
                    id="max_token_for_global_context"
                    stepper={500}
                    value={querySettings.max_token_for_global_context}
                    onValueChange={(v) => handleChange('max_token_for_global_context', v)}
                    min={1}
                    placeholder={t('retrievePanel.querySettings.maxTokensGlobalContext')}
                  />
                </div>
              </>

              <>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="max_token_for_local_context" className="ml-1 cursor-help">
                        {t('retrievePanel.querySettings.maxTokensLocalContext')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.maxTokensLocalContextTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <div>
                  {/* Removed sr-only label */}
                  <NumberInput
                    id="max_token_for_local_context"
                    stepper={500}
                    value={querySettings.max_token_for_local_context}
                    onValueChange={(v) => handleChange('max_token_for_local_context', v)}
                    min={1}
                    placeholder={t('retrievePanel.querySettings.maxTokensLocalContext')}
                  />
                </div>
              </>
            </>

            {/* History Turns */}
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <label htmlFor="history_turns" className="ml-1 cursor-help">
                      {t('retrievePanel.querySettings.historyTurns')}
                    </label>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>{t('retrievePanel.querySettings.historyTurnsTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <div>
                {/* Removed sr-only label */}
                <NumberInput
                  className="!border-input"
                  id="history_turns"
                  stepper={1}
                  type="text"
                  value={querySettings.history_turns}
                  onValueChange={(v) => handleChange('history_turns', v)}
                  min={0}
                  placeholder={t('retrievePanel.querySettings.historyTurnsPlaceholder')}
                />
              </div>
            </>

            {/* User Prompt */}
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <label htmlFor="user_prompt" className="ml-1 cursor-help">
                      {t('retrievePanel.querySettings.userPrompt')}
                    </label>
                  </TooltipTrigger>
                  <TooltipContent side="left">
                    <p>{t('retrievePanel.querySettings.userPromptTooltip')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <div>
                <Input
                  id="user_prompt"
                  value={querySettings.user_prompt}
                  onChange={(e) => handleChange('user_prompt', e.target.value)}
                  placeholder={t('retrievePanel.querySettings.userPromptPlaceholder')}
                  className="h-9"
                />
              </div>
            </>

            {/* Toggle Options */}
            <>
              <div className="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="only_need_context" className="flex-1 ml-1 cursor-help">
                        {t('retrievePanel.querySettings.onlyNeedContext')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.onlyNeedContextTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Checkbox
                  className="mr-1 cursor-pointer"
                  id="only_need_context"
                  checked={querySettings.only_need_context}
                  onCheckedChange={(checked) => handleChange('only_need_context', checked)}
                />
              </div>

              <div className="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="only_need_prompt" className="flex-1 ml-1 cursor-help">
                        {t('retrievePanel.querySettings.onlyNeedPrompt')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.onlyNeedPromptTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Checkbox
                  className="mr-1 cursor-pointer"
                  id="only_need_prompt"
                  checked={querySettings.only_need_prompt}
                  onCheckedChange={(checked) => handleChange('only_need_prompt', checked)}
                />
              </div>

              <div className="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <label htmlFor="stream" className="flex-1 ml-1 cursor-help">
                        {t('retrievePanel.querySettings.streamResponse')}
                      </label>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{t('retrievePanel.querySettings.streamResponseTooltip')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Checkbox
                  className="mr-1 cursor-pointer"
                  id="stream"
                  checked={querySettings.stream}
                  onCheckedChange={(checked) => handleChange('stream', checked)}
                />
              </div>
            </>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
