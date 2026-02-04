import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import client from "../api/client";
import type {
  ListingResponse,
  PaginatedListings,
  LeaseTransferCreate,
  SwapRequestCreate,
  ListingUpdate,
  ClaimRequest,
} from "../types";

export function useListings(params?: {
  listing_type?: string;
  category?: string;
  status?: string;
  building?: string;
  page?: number;
  limit?: number;
}) {
  return useQuery<PaginatedListings>({
    queryKey: ["listings", params],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/listings", { params });
      return data;
    },
  });
}

export function useMyListings(status?: string) {
  return useQuery<ListingResponse[]>({
    queryKey: ["myListings", status],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/listings/my", {
        params: status ? { status } : undefined,
      });
      return data;
    },
  });
}

export function useListing(id: string | undefined) {
  return useQuery<ListingResponse>({
    queryKey: ["listings", id],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/listings/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCompatibleSwaps(id: string | undefined) {
  return useQuery<ListingResponse[]>({
    queryKey: ["listings", id, "compatible"],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/listings/${id}/compatible`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateLeaseTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (listing: LeaseTransferCreate) => {
      const { data } = await client.post(
        "/api/v1/listings/lease-transfer",
        listing
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
    },
  });
}

export function useCreateSwapRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (listing: SwapRequestCreate) => {
      const { data } = await client.post(
        "/api/v1/listings/swap-request",
        listing
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
    },
  });
}

export function useUpdateListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      update,
    }: {
      id: string;
      update: ListingUpdate;
    }) => {
      const { data } = await client.put(`/api/v1/listings/${id}`, update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
    },
  });
}

export function useCancelListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post(`/api/v1/listings/${id}/cancel`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
    },
  });
}

export function useClaimListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      claim,
    }: {
      id: string;
      claim: ClaimRequest;
    }) => {
      const { data } = await client.post(`/api/v1/listings/${id}/claim`, claim);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}
