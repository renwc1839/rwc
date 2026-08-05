export interface AdminStats {
  total_users: number
  total_properties: number
  total_bookings: number
  pending_bookings: number
  properties_by_district: { district: string; count: number }[]
}

export interface EmbeddingStats {
  total: number
  completed: number
  failed: number
  pending: number
}

export interface AuditLog {
  id: number
  user_id: number | null
  action: string
  resource_type: string | null
  resource_id: number | null
  details: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

export interface ImportTask {
  id: number
  admin_id: number
  source_name: string
  source_type: string
  status: string
  total_records: number
  success_records: number
  failed_records: number
  inspection_level?: ImportInspectionLevel
  abnormal_count?: number
  created_at: string
  updated_at?: string
}

export interface ImportTaskDetail extends ImportTask {
  error_log: ImportErrorEntry[] | null
  inspection?: ImportInspection | null
  updated_at: string
}

export type ImportInspectionLevel = 'normal' | 'notice' | 'warning' | 'critical'

export interface ImportErrorEntry {
  row: number
  error: string
  data?: Record<string, string>
}

export interface ImportInspectionItem {
  level: ImportInspectionLevel
  row: number
  type: string
  message: string
  property_id?: number
}

export interface ImportApiCheck {
  row: number
  property_id?: number
  service: string
  status: 'success' | 'failed' | 'warning' | 'skipped'
  message: string
}

export interface ImportInspection {
  checked_at: string
  level: ImportInspectionLevel
  summary: {
    total: number
    success: number
    failed: number
    abnormal: number
    api_success: number
    api_failed: number
    api_skipped: number
  }
  api_checks: ImportApiCheck[]
  abnormal_items: ImportInspectionItem[]
}

export interface ImportResult {
  id: number
  source_name: string
  source_type: string
  status: string
  total_records: number
  success_records: number
  failed_records: number
  inspection_level?: ImportInspectionLevel
  abnormal_count?: number
  inspection?: ImportInspection | null
  error_log?: ImportErrorEntry[] | null
  created_at?: string
  updated_at?: string
}
