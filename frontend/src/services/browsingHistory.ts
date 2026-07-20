import type { Property } from '@/types/property'

export interface BrowsingHistoryItem {
  id: number
  title: string
  address: string
  district: string
  price_monthly: number
  bedrooms: number
  bathrooms: number
  area_sqm: number | null
  primary_image_url?: string | null
  viewed_at: string
}

const MAX_HISTORY_ITEMS = 30
const STORAGE_PREFIX = 'rwc_browsing_history'

function getStorageKey(userId?: number | string | null): string {
  return `${STORAGE_PREFIX}:${userId || 'guest'}`
}

function read(key: string): BrowsingHistoryItem[] {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function write(key: string, items: BrowsingHistoryItem[]) {
  localStorage.setItem(key, JSON.stringify(items.slice(0, MAX_HISTORY_ITEMS)))
}

function toHistoryItem(property: Property): BrowsingHistoryItem {
  const primaryImage = property.images?.find((img) => img.is_primary) || property.images?.[0]

  return {
    id: property.id,
    title: property.title,
    address: property.address,
    district: property.district,
    price_monthly: property.price_monthly,
    bedrooms: property.bedrooms,
    bathrooms: property.bathrooms,
    area_sqm: property.area_sqm,
    primary_image_url: property.primary_image_url || (primaryImage ? `/api/v1/uploads/${primaryImage.filename}` : null),
    viewed_at: new Date().toISOString(),
  }
}

export const browsingHistoryService = {
  list(userId?: number | string | null): BrowsingHistoryItem[] {
    return read(getStorageKey(userId))
  },

  record(property: Property, userId?: number | string | null): BrowsingHistoryItem[] {
    const key = getStorageKey(userId)
    const nextItem = toHistoryItem(property)
    const existing = read(key).filter((item) => item.id !== property.id)
    const next = [nextItem, ...existing].slice(0, MAX_HISTORY_ITEMS)
    write(key, next)
    return next
  },

  remove(propertyId: number, userId?: number | string | null): BrowsingHistoryItem[] {
    const key = getStorageKey(userId)
    const next = read(key).filter((item) => item.id !== propertyId)
    write(key, next)
    return next
  },

  clear(userId?: number | string | null) {
    localStorage.removeItem(getStorageKey(userId))
  },
}
