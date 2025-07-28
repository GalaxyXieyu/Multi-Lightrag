import axios, { AxiosError } from 'axios'
import { backendBaseUrl } from '@/lib/constants'
import { errorMessage } from '@/lib/utils'
import { useSettingsStore } from '@/stores/settings'
import { navigationService } from '@/services/navigation'

// Types
export type LightragNodeType = {
  id: string
  labels: string[]
  properties: Record<string, any>
}

export type LightragEdgeType = {
  id: string
  source: string
  target: string
  type: string
  properties: Record<string, any>
}

export type LightragGraphType = {
  nodes: LightragNodeType[]
  edges: LightragEdgeType[]
}

export type LightragStatus = {
  status: 'healthy'
  working_directory: string
  input_directory: string
  configuration: {
    llm_binding: string
    llm_binding_host: string
    llm_model: string
    embedding_binding: string
    embedding_binding_host: string
    embedding_model: string
    max_tokens: number
    kv_storage: string
    doc_status_storage: string
    graph_storage: string
    vector_storage: string
  }
  update_status?: Record<string, any>
  core_version?: string
  api_version?: string
  auth_mode?: 'enabled' | 'disabled'
  pipeline_busy: boolean
  webui_title?: string
  webui_description?: string
}

export type LightragDocumentsScanProgress = {
  is_scanning: boolean
  current_file: string
  indexed_count: number
  total_files: number
  progress: number
}

/**
 * Specifies the retrieval mode:
 * - "naive": Performs a basic search without advanced techniques.
 * - "local": Focuses on context-dependent information.
 * - "global": Utilizes global knowledge.
 * - "hybrid": Combines local and global retrieval methods.
 * - "mix": Integrates knowledge graph and vector retrieval.
 * - "bypass": Bypasses knowledge retrieval and directly uses the LLM.
 */
export type QueryMode = 'naive' | 'local' | 'global' | 'hybrid' | 'mix' | 'bypass'

export type Message = {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export type QueryRequest = {
  query: string
  /** Specifies the retrieval mode. */
  mode: QueryMode
  /** If True, only returns the retrieved context without generating a response. */
  only_need_context?: boolean
  /** If True, only returns the generated prompt without producing a response. */
  only_need_prompt?: boolean
  /** Defines the response format. Examples: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'. */
  response_type?: string
  /** If True, enables streaming output for real-time responses. */
  stream?: boolean
  /** Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode. */
  top_k?: number
  /** Maximum number of tokens allowed for each retrieved text chunk. */
  max_token_for_text_unit?: number
  /** Maximum number of tokens allocated for relationship descriptions in global retrieval. */
  max_token_for_global_context?: number
  /** Maximum number of tokens allocated for entity descriptions in local retrieval. */
  max_token_for_local_context?: number
  /**
   * Stores past conversation history to maintain context.
   * Format: [{"role": "user/assistant", "content": "message"}].
   */
  conversation_history?: Message[]
  /** Number of complete conversation turns (user-assistant pairs) to consider in the response context. */
  history_turns?: number
  /** User-provided prompt for the query. If provided, this will be used instead of the default value from prompt template. */
  user_prompt?: string
}

export type QueryResponse = {
  response: string
}

export type DocActionResponse = {
  status: 'success' | 'partial_success' | 'failure' | 'duplicated'
  message: string
}

export type DeleteDocResponse = {
  status: 'deletion_started' | 'busy' | 'not_allowed'
  message: string
  doc_id: string
}

export type DocStatus = 'pending' | 'processing' | 'processed' | 'failed'

export type DocStatusResponse = {
  id: string
  content_summary: string
  content_length: number
  status: DocStatus
  created_at: string
  updated_at: string
  chunks_count?: number
  error?: string
  metadata?: Record<string, any>
  file_path: string
}

export type DocsStatusesResponse = {
  statuses: Record<DocStatus, DocStatusResponse[]>
}

export type AuthStatusResponse = {
  auth_configured: boolean
  access_token?: string
  token_type?: string
  auth_mode?: 'enabled' | 'disabled'
  message?: string
  core_version?: string
  api_version?: string
  webui_title?: string
  webui_description?: string
}

export type PipelineStatusResponse = {
  autoscanned: boolean
  busy: boolean
  job_name: string
  job_start?: string
  docs: number
  batchs: number
  cur_batch: number
  request_pending: boolean
  latest_message: string
  history_messages?: string[]
  update_status?: Record<string, any>
}

export type LoginResponse = {
  access_token: string
  token_type: string
  auth_mode?: 'enabled' | 'disabled'  // Authentication mode identifier
  message?: string                    // Optional message
  core_version?: string
  api_version?: string
  webui_title?: string
  webui_description?: string
}

export const InvalidApiKeyError = 'Invalid API Key'
export const RequireApiKeError = 'API Key required'

// Axios instance
const axiosInstance = axios.create({
  baseURL: backendBaseUrl,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor: add api key and check authentication
axiosInstance.interceptors.request.use((config) => {
  const apiKey = useSettingsStore.getState().apiKey
  const token = localStorage.getItem('LIGHTRAG-API-TOKEN');

  // Always include token if it exists, regardless of path
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Interceptor：hanle error
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      if (error.response?.status === 401) {
        // For login API, throw error directly
        if (error.config?.url?.includes('/login')) {
          throw error;
        }
        // For other APIs, navigate to login page
        navigationService.navigateToLogin();

        // return a reject Promise
        return Promise.reject(new Error('Authentication required'));
      }
      throw new Error(
        `${error.response.status} ${error.response.statusText}\n${JSON.stringify(
          error.response.data
        )}\n${error.config?.url}`
      )
    }
    throw error
  }
)

// API methods
export const queryGraphs = async (
  label: string,
  maxDepth: number,
  maxNodes: number,
  graphId?: string
): Promise<LightragGraphType> => {
  let url = `/graphs?label=${encodeURIComponent(label)}&max_depth=${maxDepth}&max_nodes=${maxNodes}`
  if (graphId) {
    url += `&graph_id=${encodeURIComponent(graphId)}`
  }
  const response = await axiosInstance.get(url)
  return response.data
}

export const getGraphLabels = async (): Promise<string[]> => {
  const response = await axiosInstance.get('/graph/label/list')
  return response.data
}

export const checkHealth = async (): Promise<
  LightragStatus | { status: 'error'; message: string }
> => {
  try {
    const response = await axiosInstance.get('/health')
    return response.data
  } catch (error) {
    return {
      status: 'error',
      message: errorMessage(error)
    }
  }
}

export const getDocuments = async (graphId?: string): Promise<DocsStatusesResponse> => {
  let url = '/documents'
  if (graphId) {
    url += `?graph_id=${encodeURIComponent(graphId)}`
  }
  const response = await axiosInstance.get(url)
  return response.data
}

export const scanNewDocuments = async (): Promise<{ status: string }> => {
  const response = await axiosInstance.post('/documents/scan')
  return response.data
}

export const getDocumentsScanProgress = async (): Promise<LightragDocumentsScanProgress> => {
  const response = await axiosInstance.get('/documents/scan-progress')
  return response.data
}

export const queryText = async (request: QueryRequest, graphId?: string): Promise<QueryResponse> => {
  let url = '/query'
  if (graphId) {
    url += `?graph_id=${encodeURIComponent(graphId)}`
  }
  const response = await axiosInstance.post(url, request)
  return response.data
}

export const queryTextStream = async (
  request: QueryRequest,
  onChunk: (chunk: string) => void,
  onError?: (error: string) => void,
  graphId?: string
) => {
  const apiKey = useSettingsStore.getState().apiKey;
  const token = localStorage.getItem('LIGHTRAG-API-TOKEN');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/x-ndjson',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  try {
    let url = `${backendBaseUrl}/query/stream`
    if (graphId) {
      url += `?graph_id=${encodeURIComponent(graphId)}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      // Handle 401 Unauthorized error specifically
      if (response.status === 401) {
        // For consistency with axios interceptor, navigate to login page
        navigationService.navigateToLogin();

        // Create a specific authentication error
        const authError = new Error('Authentication required');
        throw authError;
      }

      // Handle other common HTTP errors with specific messages
      let errorBody = 'Unknown error';
      try {
        errorBody = await response.text(); // Try to get error details from body
      } catch { /* ignore */ }

      // Format error message similar to axios interceptor for consistency
      const url = `${backendBaseUrl}/query/stream`;
      throw new Error(
        `${response.status} ${response.statusText}\n${JSON.stringify(
          { error: errorBody }
        )}\n${url}`
      );
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break; // Stream finished
      }

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true }); // stream: true handles multi-byte chars split across chunks

      // Process complete lines (NDJSON)
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep potentially incomplete line in buffer

      for (const line of lines) {
        if (line.trim()) {
          try {
            const parsed = JSON.parse(line);
            if (parsed.response) {
              onChunk(parsed.response);
            } else if (parsed.error && onError) {
              onError(parsed.error);
            }
          } catch (error) {
            console.error('Error parsing stream chunk:', line, error);
            if (onError) onError(`Error parsing server response: ${line}`);
          }
        }
      }
    }

    // Process any remaining data in the buffer after the stream ends
    if (buffer.trim()) {
      try {
        const parsed = JSON.parse(buffer);
        if (parsed.response) {
          onChunk(parsed.response);
        } else if (parsed.error && onError) {
          onError(parsed.error);
        }
      } catch (error) {
        console.error('Error parsing final chunk:', buffer, error);
        if (onError) onError(`Error parsing final server response: ${buffer}`);
      }
    }

  } catch (error) {
    const message = errorMessage(error);

    // Check if this is an authentication error
    if (message === 'Authentication required') {
      // Already navigated to login page in the response.status === 401 block
      console.error('Authentication required for stream request');
      if (onError) {
        onError('Authentication required');
      }
      return; // Exit early, no need for further error handling
    }

    // Check for specific HTTP error status codes in the error message
    const statusCodeMatch = message.match(/^(\d{3})\s/);
    if (statusCodeMatch) {
      const statusCode = parseInt(statusCodeMatch[1], 10);

      // Handle specific status codes with user-friendly messages
      let userMessage = message;

      switch (statusCode) {
      case 403:
        userMessage = 'You do not have permission to access this resource (403 Forbidden)';
        console.error('Permission denied for stream request:', message);
        break;
      case 404:
        userMessage = 'The requested resource does not exist (404 Not Found)';
        console.error('Resource not found for stream request:', message);
        break;
      case 429:
        userMessage = 'Too many requests, please try again later (429 Too Many Requests)';
        console.error('Rate limited for stream request:', message);
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        userMessage = `Server error, please try again later (${statusCode})`;
        console.error('Server error for stream request:', message);
        break;
      default:
        console.error('Stream request failed with status code:', statusCode, message);
      }

      if (onError) {
        onError(userMessage);
      }
      return;
    }

    // Handle network errors (like connection refused, timeout, etc.)
    if (message.includes('NetworkError') ||
        message.includes('Failed to fetch') ||
        message.includes('Network request failed')) {
      console.error('Network error for stream request:', message);
      if (onError) {
        onError('Network connection error, please check your internet connection');
      }
      return;
    }

    // Handle JSON parsing errors during stream processing
    if (message.includes('Error parsing') || message.includes('SyntaxError')) {
      console.error('JSON parsing error in stream:', message);
      if (onError) {
        onError('Error processing response data');
      }
      return;
    }

    // Handle other errors
    console.error('Unhandled stream error:', message);
    if (onError) {
      onError(message);
    } else {
      console.error('No error handler provided for stream error:', message);
    }
  }
};

export const insertText = async (text: string): Promise<DocActionResponse> => {
  const response = await axiosInstance.post('/documents/text', { text })
  return response.data
}

export const insertTexts = async (texts: string[]): Promise<DocActionResponse> => {
  const response = await axiosInstance.post('/documents/texts', { texts })
  return response.data
}

export const uploadDocument = async (
  file: File,
  onUploadProgress?: (percentCompleted: number) => void,
  graphId?: string
): Promise<DocActionResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  // 添加图谱ID参数
  if (graphId) {
    formData.append('graph_id', graphId)
  }

  const response = await axiosInstance.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    // prettier-ignore
    onUploadProgress:
      onUploadProgress !== undefined
        ? (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total!)
          onUploadProgress(percentCompleted)
        }
        : undefined
  })
  return response.data
}

export const batchUploadDocuments = async (
  files: File[],
  onUploadProgress?: (fileName: string, percentCompleted: number) => void
): Promise<DocActionResponse[]> => {
  return await Promise.all(
    files.map(async (file) => {
      return await uploadDocument(file, (percentCompleted) => {
        onUploadProgress?.(file.name, percentCompleted)
      })
    })
  )
}

export const clearDocuments = async (): Promise<DocActionResponse> => {
  const response = await axiosInstance.delete('/documents')
  return response.data
}

export const clearCache = async (modes?: string[]): Promise<{
  status: 'success' | 'fail'
  message: string
}> => {
  const response = await axiosInstance.post('/documents/clear_cache', { modes })
  return response.data
}

export const deleteDocuments = async (docIds: string[], deleteFile: boolean = false): Promise<DeleteDocResponse> => {
  const response = await axiosInstance.delete('/documents/delete_document', {
    data: { doc_ids: docIds, delete_file: deleteFile }
  })
  return response.data
}

export const getAuthStatus = async (): Promise<AuthStatusResponse> => {
  try {
    // Add a timeout to the request to prevent hanging
    const response = await axiosInstance.get('/auth-status', {
      timeout: 5000, // 5 second timeout
      headers: {
        'Accept': 'application/json' // Explicitly request JSON
      }
    });

    // Check if response is HTML (which indicates a redirect or wrong endpoint)
    const contentType = response.headers['content-type'] || '';
    if (contentType.includes('text/html')) {
      console.warn('Received HTML response instead of JSON for auth-status endpoint');
      return {
        auth_configured: true,
        auth_mode: 'enabled'
      };
    }

    // Strict validation of the response data
    if (response.data &&
        typeof response.data === 'object' &&
        'auth_configured' in response.data &&
        typeof response.data.auth_configured === 'boolean') {

      // For unconfigured auth, ensure we have an access token
      if (!response.data.auth_configured) {
        if (response.data.access_token && typeof response.data.access_token === 'string') {
          return response.data;
        } else {
          console.warn('Auth not configured but no valid access token provided');
        }
      } else {
        // For configured auth, just return the data
        return response.data;
      }
    }

    // If response data is invalid but we got a response, log it
    console.warn('Received invalid auth status response:', response.data);

    // Default to auth configured if response is invalid
    return {
      auth_configured: true,
      auth_mode: 'enabled'
    };
  } catch (error) {
    // If the request fails, assume authentication is configured
    console.error('Failed to get auth status:', errorMessage(error));
    return {
      auth_configured: true,
      auth_mode: 'enabled'
    };
  }
}

export const getPipelineStatus = async (): Promise<PipelineStatusResponse> => {
  const response = await axiosInstance.get('/documents/pipeline_status')
  return response.data
}

export const loginToServer = async (username: string, password: string): Promise<LoginResponse> => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  const response = await axiosInstance.post('/login', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data;
}

/**
 * Updates an entity's properties in the knowledge graph
 * @param entityName The name of the entity to update
 * @param updatedData Dictionary containing updated attributes
 * @param allowRename Whether to allow renaming the entity (default: false)
 * @returns Promise with the updated entity information
 */
export const updateEntity = async (
  entityName: string,
  updatedData: Record<string, any>,
  allowRename: boolean = false
): Promise<DocActionResponse> => {
  const response = await axiosInstance.post('/graph/entity/edit', {
    entity_name: entityName,
    updated_data: updatedData,
    allow_rename: allowRename
  })
  return response.data
}

/**
 * Updates a relation's properties in the knowledge graph
 * @param sourceEntity The source entity name
 * @param targetEntity The target entity name
 * @param updatedData Dictionary containing updated attributes
 * @returns Promise with the updated relation information
 */
export const updateRelation = async (
  sourceEntity: string,
  targetEntity: string,
  updatedData: Record<string, any>
): Promise<DocActionResponse> => {
  const response = await axiosInstance.post('/graph/relation/edit', {
    source_id: sourceEntity,
    target_id: targetEntity,
    updated_data: updatedData
  })
  return response.data
}

/**
 * Checks if an entity name already exists in the knowledge graph
 * @param entityName The entity name to check
 * @returns Promise with boolean indicating if the entity exists
 */
export const checkEntityNameExists = async (entityName: string): Promise<boolean> => {
  try {
    const response = await axiosInstance.get(`/graph/entity/exists?name=${encodeURIComponent(entityName)}`)
    return response.data.exists
  } catch (error) {
    console.error('Error checking entity name:', error)
    return false
  }
}

// ==================== 多图谱管理 API ====================

export type GraphCreateRequest = {
  name: string
  description?: string
}

export type GraphInfo = {
  name: string
  description: string
  working_dir: string
  created_at: string
  is_active: boolean
  entity_count: number
  relation_count: number
}

export type GraphListResponse = {
  status: string
  graphs: GraphInfo[]
  total: number
}

export type GraphCreateResponse = {
  status: string
  message: string
  graph_info: GraphInfo
}

export type CurrentGraphResponse = {
  status: string
  current_graph: GraphInfo | null
  message?: string
}

/**
 * 创建新的知识图谱
 * @param name 图谱名称
 * @param description 图谱描述
 * @returns Promise with the creation result
 */
export const createGraph = async (name: string, description: string = ''): Promise<GraphCreateResponse> => {
  const response = await axiosInstance.post('/graphs', {
    name,
    description
  })
  return response.data
}

/**
 * 获取所有图谱列表
 * @returns Promise with the list of graphs
 */
export const listGraphs = async (): Promise<GraphListResponse> => {
  const response = await axiosInstance.get('/graphs/list')
  return response.data
}

/**
 * 删除指定图谱
 * @param graphName 图谱名称
 * @returns Promise with the deletion result
 */
export const deleteGraph = async (graphName: string): Promise<DocActionResponse> => {
  const response = await axiosInstance.delete(`/graphs/${encodeURIComponent(graphName)}`)
  return response.data
}

/**
 * 切换到指定图谱
 * @param graphName 图谱名称
 * @returns Promise with the switch result
 */
export const switchGraph = async (graphName: string): Promise<DocActionResponse> => {
  const response = await axiosInstance.post(`/graphs/${encodeURIComponent(graphName)}/switch`)
  return response.data
}

/**
 * 获取当前活跃图谱信息
 * @returns Promise with the current graph information
 */
export const getCurrentGraph = async (): Promise<CurrentGraphResponse> => {
  const response = await axiosInstance.get('/graphs/current')
  return response.data
}

// ==================== 手动节点管理 API ====================

export type NodeCreateRequest = {
  entity_name: string
  entity_type?: string
  description?: string
  source_id?: string
  file_path?: string
}

export type NodeBatchCreateRequest = {
  nodes: NodeCreateRequest[]
}

export type NodeInfo = {
  entity_name: string
  entity_type?: string
  description?: string
  source_id?: string
  file_path?: string
  [key: string]: any
}

export type NodeCreateResponse = {
  status: string
  message: string
  node_info: NodeInfo
}

export type NodeBatchResult = {
  entity_name: string
  status: 'success' | 'failed'
  data?: NodeInfo
  error?: string
}

export type NodeBatchCreateResponse = {
  status: string
  message: string
  successful_nodes: NodeBatchResult[]
  failed_nodes: NodeBatchResult[]
  total_requested: number
  successful_count: number
  failed_count: number
}

export type NodeGetResponse = {
  status: string
  node_name: string
  node_data: NodeInfo
  exists: boolean
}

/**
 * 创建单个节点
 * @param nodeData 节点数据
 * @returns Promise with the creation result
 */
export const createNode = async (nodeData: NodeCreateRequest): Promise<NodeCreateResponse> => {
  const response = await axiosInstance.post('/graphs/nodes', nodeData)
  return response.data
}

/**
 * 批量创建节点
 * @param nodes 节点数据数组
 * @returns Promise with the batch creation result
 */
export const createNodesBatch = async (nodes: NodeCreateRequest[]): Promise<NodeBatchCreateResponse> => {
  const response = await axiosInstance.post('/graphs/nodes/batch', { nodes })
  return response.data
}

/**
 * 获取节点信息
 * @param nodeName 节点名称
 * @returns Promise with the node information
 */
export const getNode = async (nodeName: string): Promise<NodeGetResponse> => {
  const response = await axiosInstance.get(`/graphs/nodes/${encodeURIComponent(nodeName)}`)
  return response.data
}

/**
 * 删除节点
 * @param nodeName 节点名称
 * @returns Promise with the deletion result
 */
export const deleteNode = async (nodeName: string): Promise<DocActionResponse> => {
  const response = await axiosInstance.delete(`/graphs/nodes/${encodeURIComponent(nodeName)}`)
  return response.data
}

// ==================== 手动关系管理 API ====================

export type RelationCreateRequest = {
  source_entity: string
  target_entity: string
  description?: string
  keywords?: string
  weight?: number
  source_id?: string
  file_path?: string
}

export type RelationBatchCreateRequest = {
  relations: RelationCreateRequest[]
}

export type RelationUpdateRequest = {
  source_id: string
  target_id: string
  updated_data: {
    description?: string
    keywords?: string
    weight?: number
    [key: string]: any
  }
}

export type RelationInfo = {
  source_entity: string
  target_entity: string
  description?: string
  keywords?: string
  weight?: number
  source_id?: string
  file_path?: string
  [key: string]: any
}

export type RelationCreateResponse = {
  status: string
  message: string
  relation_info: RelationInfo
}

export type RelationBatchResult = {
  source_entity: string
  target_entity: string
  status: 'success' | 'failed'
  data?: RelationInfo
  error?: string
}

export type RelationBatchCreateResponse = {
  status: string
  message: string
  successful_relations: RelationBatchResult[]
  failed_relations: RelationBatchResult[]
  total_requested: number
  successful_count: number
  failed_count: number
}

/**
 * 创建单个关系
 * @param relationData 关系数据
 * @returns Promise with the creation result
 */
export const createRelation = async (relationData: RelationCreateRequest): Promise<RelationCreateResponse> => {
  const response = await axiosInstance.post('/graphs/relations', relationData)
  return response.data
}

/**
 * 批量创建关系
 * @param relations 关系数据数组
 * @returns Promise with the batch creation result
 */
export const createRelationsBatch = async (relations: RelationCreateRequest[]): Promise<RelationBatchCreateResponse> => {
  const response = await axiosInstance.post('/graphs/relations/batch', { relations })
  return response.data
}

/**
 * 更新关系
 * @param sourceEntity 源实体名称
 * @param targetEntity 目标实体名称
 * @param updatedData 更新数据
 * @returns Promise with the update result
 */
export const updateRelationByEntities = async (
  sourceEntity: string,
  targetEntity: string,
  updatedData: RelationUpdateRequest['updated_data']
): Promise<DocActionResponse> => {
  const response = await axiosInstance.put(
    `/graphs/relations/${encodeURIComponent(sourceEntity)}/${encodeURIComponent(targetEntity)}`,
    {
      source_id: sourceEntity,
      target_id: targetEntity,
      updated_data: updatedData
    }
  )
  return response.data
}

/**
 * 删除关系
 * @param sourceEntity 源实体名称
 * @param targetEntity 目标实体名称
 * @returns Promise with the deletion result
 */
export const deleteRelation = async (sourceEntity: string, targetEntity: string): Promise<DocActionResponse> => {
  const response = await axiosInstance.delete(
    `/graphs/relations/${encodeURIComponent(sourceEntity)}/${encodeURIComponent(targetEntity)}`
  )
  return response.data
}
