import api from './api'

export interface PortalState {
  appointments: any[]
  properties: any[]
  staff: any[]
  exceptions: any[]
  complaints: any[]
  workOrders: any[]
  messages: any[]
  financeItems: any[]
  warnings: any[]
  rules: Record<string, any>
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

export const adminPortalService = {
  getPublicOptions(): Promise<{ categories: string[]; cities: string[] }> {
    return api.get('/admin-portal/public/options').then((r) => r.data)
  },

  getState(): Promise<PortalState> {
    return api.get('/admin-portal/state').then((r) => r.data)
  },

  getOverview(): Promise<PortalOverview> {
    return api.get('/admin-portal/overview').then((r) => r.data)
  },

  createComplaint(data: ComplaintCreate): Promise<any> {
    return api.post('/admin-portal/complaints', data).then((r) => r.data)
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

}
