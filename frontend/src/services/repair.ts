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

  update(id: string, data: { status: string; result?: string }): Promise<Repair> {
    return api.patch(`/admin-portal/repairs/${id}`, data).then((r) => r.data)
  },
}
