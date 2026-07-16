import api from './api'

export interface Repair {
  id: string
  property: string
  tenant: string
  category: string
  desc: string
  date: string
  status: string
  owner?: string
  assignee?: string
  progressSteps?: Array<{ key: string; label: string; done: boolean; active: boolean }>
  reason?: string
  materials?: string
  evidenceImages?: Array<{ name: string; size: number; dataUrl: string }>
  updateLogs?: Array<{
    time: string
    status: string
    assignee: string
    reason: string
    materials: string
    result: string
    images: Array<{ name: string; size: number; dataUrl: string }>
  }>
  result?: string
}

export interface RepairCreate {
  property: string
  tenant: string
  category: string
  desc: string
}

export const repairService = {
  list(): Promise<Repair[]> {
    return api.get('/admin-portal/repairs').then((r) => r.data)
  },

  create(data: RepairCreate): Promise<Repair> {
    return api.post('/admin-portal/repairs', data).then((r) => r.data)
  },

  update(id: string, data: {
    status?: string
    assignee?: string
    result?: string
    reason?: string
    materials?: string
    evidenceImages?: Array<{ name: string; size: number; dataUrl: string }>
  }): Promise<Repair> {
    return api.patch(`/admin-portal/repairs/${id}`, data).then((r) => r.data)
  },
}
