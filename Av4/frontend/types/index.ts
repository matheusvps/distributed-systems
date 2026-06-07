export interface Promotion {
  id: string
  title?: string
  description?: string
  category?: string
  price?: number
  originalPrice?: number
  store?: string
  storeEmail?: string
  status?: string
  validatedAt?: string
  hot?: boolean
  score?: number
}

export interface PromotionsResponse {
  count: number
  promotions: Promotion[]
}

export interface CreatePromotionPayload {
  title: string
  description: string
  category: string
  price: number
  originalPrice: number
  store: string
  storeEmail: string
}

export interface VotePayload {
  vote: 1 | -1
  consumerId: string
}

export interface InterestsResponse {
  interests: string[]
}

export interface CategoriesResponse {
  categories: string[]
}

export type NotificationType = 'categoria' | 'hotdeal'

export interface NotificationEvent {
  type: NotificationType
  message: string
  promotionId?: string
  title?: string
  category?: string
  price?: number
  store?: string
  score?: number
  tag?: string
}

export interface FeedNotification extends NotificationEvent {
  receivedAt: string
  localId: string
  read: boolean
}

export type SseStatus = 'idle' | 'connecting' | 'open' | 'error' | 'closed'
