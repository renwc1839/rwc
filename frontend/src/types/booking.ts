export type BookingStatus = 'pending' | 'approved' | 'rejected' | 'cancelled' | 'completed'

// Matches backend: app/schemas/booking.py BookingRead
export interface Booking {
  id: number
  tenant_id: number
  property_id: number
  landlord_id: number
  status: BookingStatus
  message: string | null
  scheduled_date: string | null
  deposit_amount: number | null
  service_fee: number | null
  deposit_status: string | null
  payment_transaction_id: string | null
  tenant_profile?: Record<string, any> | null
  progress_steps?: Array<{ key: string; label: string; done: boolean; active: boolean }> | null
  room_number?: string | null
  lease_start?: string | null
  lease_end?: string | null
  contract_status?: string | null
  admin_note?: string | null
  created_at: string
  updated_at: string
}

export interface BookingCreate {
  property_id: number
  message?: string
  scheduled_date?: string
  tenant_profile?: Record<string, any>
  room_number?: string
  lease_start?: string
  lease_end?: string
}

export type NotificationType = 'booking_created' | 'booking_approved' | 'booking_rejected' | 'booking_cancelled'

export interface Notification {
  id: number
  user_id: number
  type: NotificationType
  title: string
  content: string | null
  is_read: boolean
  created_at: string
  updated_at: string
}

export interface UnreadCount {
  count: number
}
