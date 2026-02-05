// ──────────────────────────────────────────────
// Enums (as const objects for erasableSyntaxOnly)
// ──────────────────────────────────────────────

export const RoomCategory = {
  // Park 100 Complex (New Dorms)
  PARK_SHARED_2BR: "PARK_SHARED_2BR",
  PARK_SHARED_3BR: "PARK_SHARED_3BR",
  PARK_STUDIO: "PARK_STUDIO",
  PARK_COUPLES: "PARK_COUPLES",
  // Ilanot Complex (Standard Dorms)
  ILANOT_SHARED_1BR: "ILANOT_SHARED_1BR",
  ILANOT_SHARED_2BR: "ILANOT_SHARED_2BR",
  ILANOT_PRIVATE: "ILANOT_PRIVATE",
  ILANOT_SHARED_LARGE: "ILANOT_SHARED_LARGE",
  ILANOT_STUDIO: "ILANOT_STUDIO",
  ILANOT_COUPLES: "ILANOT_COUPLES",
} as const;
export type RoomCategory = (typeof RoomCategory)[keyof typeof RoomCategory];

export const ListingType = {
  LEASE_TRANSFER: "LEASE_TRANSFER",
  SWAP_REQUEST: "SWAP_REQUEST",
} as const;
export type ListingType = (typeof ListingType)[keyof typeof ListingType];

export const LeaseTransferStatus = {
  OPEN: "OPEN",
  MATCHED: "MATCHED",
  PENDING_APPROVAL: "PENDING_APPROVAL",
  COMPLETED: "COMPLETED",
  CANCELLED: "CANCELLED",
  EXPIRED: "EXPIRED",
} as const;
export type LeaseTransferStatus =
  (typeof LeaseTransferStatus)[keyof typeof LeaseTransferStatus];

export const SwapRequestStatus = {
  OPEN: "OPEN",
  PARTIAL_MATCH: "PARTIAL_MATCH",
  FULLY_MATCHED: "FULLY_MATCHED",
  PENDING_APPROVAL: "PENDING_APPROVAL",
  COMPLETED: "COMPLETED",
  CANCELLED: "CANCELLED",
  EXPIRED: "EXPIRED",
} as const;
export type SwapRequestStatus =
  (typeof SwapRequestStatus)[keyof typeof SwapRequestStatus];

export const MatchStatus = {
  PROPOSED: "PROPOSED",
  ACCEPTED: "ACCEPTED",
  REJECTED: "REJECTED",
  EXPIRED: "EXPIRED",
  CANCELLED: "CANCELLED",
} as const;
export type MatchStatus = (typeof MatchStatus)[keyof typeof MatchStatus];

export const TransactionStatus = {
  PENDING: "PENDING",
  IN_PROGRESS: "IN_PROGRESS",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  CANCELLED: "CANCELLED",
} as const;
export type TransactionStatus =
  (typeof TransactionStatus)[keyof typeof TransactionStatus];

// ──────────────────────────────────────────────
// User models
// ──────────────────────────────────────────────

export interface UserProfile {
  uid: string;
  email: string;
  full_name: string;
  student_id: string;
  phone: string;
  current_room_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserProfilePublic {
  uid: string;
  full_name: string;
  current_room_id?: string;
}

export interface UserProfileCreate {
  full_name: string;
  student_id: string;
  phone: string;
  current_room_id?: string;
}

export interface UserProfileUpdate {
  full_name?: string;
  phone?: string;
  current_room_id?: string;
}

// ──────────────────────────────────────────────
// Room models
// ──────────────────────────────────────────────

export interface Room {
  id: string;
  building: string;
  floor: number;
  room_number: string;
  category: RoomCategory;
  description: string;
  amenities: string[];
  occupant_uid?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RoomCreate {
  building: string;
  floor: number;
  room_number: string;
  category: RoomCategory;
  description?: string;
  amenities?: string[];
}

export interface RoomUpdate {
  description?: string;
  amenities?: string[];
  is_active?: boolean;
}

// ──────────────────────────────────────────────
// Listing models
// ──────────────────────────────────────────────

export interface LeaseTransferCreate {
  room_id: string;
  lease_start_date: string;
  lease_end_date: string;
  move_in_date?: string;
  description?: string;
  asking_price?: number;
}

export interface SwapRequestCreate {
  room_id: string;
  lease_start_date: string;
  lease_end_date: string;
  move_in_date?: string;
  description?: string;
  desired_categories: RoomCategory[];
  desired_buildings?: string[];
  desired_min_start?: string;
  desired_max_end?: string;
}

export interface ListingUpdate {
  description?: string;
  asking_price?: number;
  lease_start_date?: string;
  lease_end_date?: string;
  move_in_date?: string;
  desired_categories?: RoomCategory[];
  desired_buildings?: string[];
}

export interface ListingResponse {
  id: string;
  listing_type: ListingType;
  status: LeaseTransferStatus | SwapRequestStatus;
  owner_uid: string;
  room_id: string;
  room_category: RoomCategory;
  room_building: string;
  lease_start_date: string;
  lease_end_date: string;
  move_in_date?: string;
  description: string;
  asking_price?: number;
  desired_categories?: RoomCategory[];
  desired_buildings?: string[];
  desired_min_start?: string;
  desired_max_end?: string;
  replacement_match_id?: string;
  target_match_id?: string;
  expires_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedListings {
  items: ListingResponse[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

// ──────────────────────────────────────────────
// Match / Claim models
// ──────────────────────────────────────────────

export interface ClaimRequest {
  message?: string;
  claimant_listing_id?: string;
}

export interface ContactResponse {
  name: string;
  phone: string;
}

export interface MatchResponse {
  id: string;
  match_type: ListingType;
  status: MatchStatus;
  listing_id: string;
  claimant_uid: string;
  claimant_listing_id?: string;
  offered_room_id: string;
  offered_room_category: RoomCategory;
  offered_room_building: string;
  paired_match_id?: string;
  message?: string;
  proposed_at?: string;
  responded_at?: string;
  expires_at?: string;
  created_at?: string;
  updated_at?: string;
}

// ──────────────────────────────────────────────
// Transaction models
// ──────────────────────────────────────────────

export interface TransactionResponse {
  id: string;
  transaction_type: ListingType;
  status: TransactionStatus;
  match_id?: string;
  match_ids?: string[];
  from_uid?: string;
  to_uid?: string;
  room_id?: string;
  party_a_uid?: string;
  party_a_room_id?: string;
  party_b_uid?: string;
  party_b_room_id?: string;
  lease_start_date?: string;
  lease_end_date?: string;
  initiated_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}
