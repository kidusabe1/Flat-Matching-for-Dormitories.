import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import client from "../api/client";
import type { TransactionResponse } from "../types";

export function useMyTransactions(status?: string) {
  return useQuery<TransactionResponse[]>({
    queryKey: ["transactions", status],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/transactions/my", {
        params: status ? { status } : undefined,
      });
      return data;
    },
  });
}

export function useTransaction(id: string | undefined) {
  return useQuery<TransactionResponse>({
    queryKey: ["transactions", id],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/transactions/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useConfirmTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post(`/api/v1/transactions/${id}/confirm`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}

export function useCancelTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post(`/api/v1/transactions/${id}/cancel`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["myListings"] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}
