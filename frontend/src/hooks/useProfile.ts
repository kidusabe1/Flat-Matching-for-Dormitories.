import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import client from "../api/client";
import type {
  UserProfile,
  UserProfileCreate,
  UserProfileUpdate,
} from "../types";

export function useProfile() {
  return useQuery<UserProfile>({
    queryKey: ["profile"],
    queryFn: async () => {
      const { data } = await client.get("/api/v1/users/me");
      return data;
    },
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profile: UserProfileCreate) => {
      const { data } = await client.post("/api/v1/users/profile", profile);
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["profile"], data);
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profile: UserProfileUpdate) => {
      const { data } = await client.put("/api/v1/users/me", profile);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}
