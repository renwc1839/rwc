// Matches backend: app/models/user.py
export type UserRole = 'tenant' | 'landlord' | 'appointment_staff' | 'property_manager' | 'repair_worker' | 'admin'
export type UserStatus = 'active' | 'disabled' | 'deleted'

// Matches backend: app/schemas/user.py UserRead
export interface User {
  id: number
  username: string
  phone: string | null
  wechat_openid: string | null
  email: string | null
  role: UserRole
  status: UserStatus
  created_at: string
  updated_at: string
}

// Matches backend: app/schemas/user.py UserProfileUpdate
export interface UserProfileUpdate {
  username?: string
  phone?: string
  email?: string
}

export interface AdminUserDetail {
  user: User & {
    role_label: string
  }
  tenant_bookings: Array<Record<string, any>>
  handled_bookings: Array<Record<string, any>>
  managed_properties: Array<Record<string, any>>
  appointments: Array<Record<string, any>>
  repairs: Array<Record<string, any>>
  work_orders: Array<Record<string, any>>
  messages: Array<Record<string, any>>
}
