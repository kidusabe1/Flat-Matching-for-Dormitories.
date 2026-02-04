import { useQuery } from "@tanstack/react-query";
import client from "../api/client";
import type { Room } from "../types";

export function useRooms(params?: {
  building?: string;
  category?: string;
  is_active?: boolean;
}) {
  return useQuery<Room[]>({
    queryKey: ["rooms", params],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/rooms", { params });
      return data;
    },
  });
}

export function useRoom(id: string | undefined) {
  return useQuery<Room>({
    queryKey: ["rooms", id],
    queryFn: async () => {
      const { data } = await client.get(`/api/v1/rooms/${id}`);
      return data;
    },
    enabled: !!id,
  });
}
