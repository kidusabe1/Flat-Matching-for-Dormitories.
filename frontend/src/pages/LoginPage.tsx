import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "../firebase";
import { useAuth } from "../hooks/useAuth";

type Mode = "signIn" | "signUp" | "forgotPassword";

export default function LoginPage() {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("signIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const switchMode = (next: Mode) => {
    setMode(next);
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      if (mode === "forgotPassword") {
        await sendPasswordResetEmail(auth, email, {
          url: window.location.origin + "/login",
          handleCodeInApp: false,
        });
        setSuccess("Password reset link sent! Check your email.");
      } else if (mode === "signUp") {
        await signUp(email, password);
        navigate("/verify-email");
      } else {
        await signIn(email, password);
        navigate("/");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Authentication failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const title =
    mode === "forgotPassword"
      ? "Reset Password"
      : mode === "signUp"
      ? "Create Account"
      : "Sign In";

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-blue-600">BIU Dorm Exchange</h1>
          <p className="mt-2 text-sm text-gray-500">
            Bar-Ilan University Dormitory Exchange Platform
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          <h2 className="mb-6 text-lg font-semibold text-gray-900">{title}</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
              {success}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                placeholder="you@biu.ac.il"
              />
            </div>

            {mode !== "forgotPassword" && (
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  placeholder="At least 6 characters"
                />
              </div>
            )}
          </div>

          {mode === "signIn" && (
            <div className="mt-2 text-right">
              <button
                type="button"
                onClick={() => switchMode("forgotPassword")}
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                Forgot password?
              </button>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading
              ? "Please wait..."
              : mode === "forgotPassword"
              ? "Send Reset Link"
              : mode === "signUp"
              ? "Create Account"
              : "Sign In"}
          </button>

          <p className="mt-4 text-center text-sm text-gray-500">
            {mode === "forgotPassword" ? (
              <>
                Remember your password?{" "}
                <button
                  type="button"
                  onClick={() => switchMode("signIn")}
                  className="font-medium text-blue-600 hover:text-blue-700"
                >
                  Sign In
                </button>
              </>
            ) : mode === "signUp" ? (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => switchMode("signIn")}
                  className="font-medium text-blue-600 hover:text-blue-700"
                >
                  Sign In
                </button>
              </>
            ) : (
              <>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => switchMode("signUp")}
                  className="font-medium text-blue-600 hover:text-blue-700"
                >
                  Sign Up
                </button>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}
