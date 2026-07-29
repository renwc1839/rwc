import api from './api'

export interface PortalState {
  appointments: any[]
  properties: any[]
  staff: any[]
  exceptions: any[]
  complaints: any[]
  workOrders: any[]
  repairs: any[]
  messages: any[]
  financeItems: any[]
  warnings: any[]
  rules: Record<string, any>
  permissionCatalog: any[]
  roleProfiles: any[]
  schedules: any[]
  workFeedbacks: any[]
  reports: any[]
  exportRequests: any[]
  actionHistory: any[]
  accounts: any[]
  settings: Record<string, any>
  logs: any[]
}

export interface PortalOverview {
  metrics: any[]
  cityRanks: any[]
  trend: any[]
}

export interface ComplaintCreate {
  category: string
  title: string
  description: string
  complainantName: string
  contact: string
  city: string
  property?: string
}

export interface CustomerContactCreate {
  sender: string
  contact: string
  summary: string
  property?: string
  propertyId?: number
  channel?: string
}

export interface ChatState {
  me: any
  contacts: any[]
  conversations: any[]
  unreadTotal?: number
}

export const adminPortalService = {
  getPublicOptions(): Promise<{ categories: string[]; cities: string[] }> {
    return api.get('/admin-portal/public/options').then((r) => r.data)
  },

  getState(): Promise<PortalState> {
    return api.get('/admin-portal/state').then((r) => r.data)
  },

  getWorkspaceState(): Promise<Partial<PortalState>> {
    return api.get('/admin-portal/workspace-state').then((r) => r.data)
  },

  getOverview(): Promise<PortalOverview> {
    return api.get('/admin-portal/overview').then((r) => r.data)
  },

  createComplaint(data: ComplaintCreate): Promise<any> {
    return api.post('/admin-portal/complaints', data).then((r) => r.data)
  },

  createCustomerMessage(data: CustomerContactCreate): Promise<any> {
    return api.post('/admin-portal/messages', data).then((r) => r.data)
  },

  handleMessage(
    id: string,
    data: { action: 'claim' | 'reply' | 'resolve'; reply?: string; assignee?: string },
  ): Promise<any> {
    return api.patch(`/admin-portal/messages/${id}/handle`, data).then((r) => r.data)
  },

  getChatState(): Promise<ChatState> {
    return api.get('/admin-portal/chat').then((r) => r.data)
  },

  sendChatMessage(data: { conversationId: string; content: string }): Promise<any> {
    return api.post('/admin-portal/chat/messages', data).then((r) => r.data)
  },

  markChatRead(conversationId: string): Promise<any> {
    return api.patch(`/admin-portal/chat/${encodeURIComponent(conversationId)}/read`).then((r) => r.data)
  },

  updateComplaint(id: string, data: { status: string; result?: string }): Promise<any> {
    return api.patch(`/admin-portal/complaints/${id}`, data).then((r) => r.data)
  },

  assignAppointment(id: string, assignee: string): Promise<any> {
    return api.patch(`/admin-portal/appointments/${id}/assign`, { assignee }).then((r) => r.data)
  },

  updateItem(collection: string, id: string, data: { status: string; result?: string }): Promise<any> {
    return api.patch(`/admin-portal/items/${collection}/${id}`, data).then((r) => r.data)
  },

  updateAccount(id: string, data: { roleKey?: string; permissions?: string[]; status?: string }): Promise<any> {
    return api.patch(`/admin-portal/accounts/${id}`, data).then((r) => r.data)
  },

  updateRoleProfile(roleKey: string, data: { permissions: string[] }): Promise<any> {
    return api.patch(`/admin-portal/roles/${roleKey}`, data).then((r) => r.data)
  },

  recordAction(data: { action: string; target: string; content: string }): Promise<any> {
    return api.post('/admin-portal/actions', data).then((r) => r.data)
  },
}
