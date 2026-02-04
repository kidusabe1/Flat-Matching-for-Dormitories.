import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import client from "../api/client";
import type { MatchResponse, ContactResponse } from "../types";

export function useMyMatches(status?: string) {
  return useQuery<MatchResponse[]>({
    queryKey: ["matches", status],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/matches/my", {
        params: status ? { status } : undefined,
      });
      return data;
    },
  });
}

export function useMatch(id: string | undefined) {
  return useQuery<MatchResponse>({
    queryKey: ["matches", id],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/matches/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useAcceptMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post(`/api/v1/matches/${id}/accept`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}

export function useMatchContact(matchId: string | undefined, enabled: boolean) {
  return useQuery<ContactResponse>({
    queryKey: ["matchContact", matchId],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/matches/${matchId}/contact`);
      return data;
    },
    enabled: !!matchId && enabled,
  });
}

export function useRejectMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post(`/api/v1/matches/${id}/reject`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matches"] });
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
    },
  });
}
