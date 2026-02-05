import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { auth } from "../firebase";
import client from "../api/client";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  emailVerified: boolean | null;
  setEmailVerified: (val: boolean) => void;
  hasProfile: boolean | null;
  setHasProfile: (val: boolean) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [emailVerified, setEmailVerified] = useState<boolean | null>(null);
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setLoading(true);
      setUser(firebaseUser);
      if (firebaseUser) {
        // Check verification and profile in parallel
        const [verRes, profRes] = await Promise.allSettled([
          client.get("/api/v1/auth/verification-status"),
          client.get("/api/v1/users/me"),
        ]);

        const verified =
          verRes.status === "fulfilled" && verRes.value.data.verified;
        const profileExists = profRes.status === "fulfilled";

        // Users with a profile are established — treat as verified
        setEmailVerified(verified || profileExists);
        setHasProfile(profileExists);
      } else {
        setEmailVerified(null);
        setHasProfile(null);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  const signUp = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(auth, email, password);
  };

  const signOut = async () => {
    await firebaseSignOut(auth);
    setEmailVerified(null);
    setHasProfile(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        emailVerified,
        setEmailVerified,
        hasProfile,
        setHasProfile,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
