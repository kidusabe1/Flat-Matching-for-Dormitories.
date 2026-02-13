import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "../firebase";
import { useAuth } from "../hooks/useAuth";

type Mode = "signIn" | "signUp" | "forgotPassword";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const PASSWORD_RULES = [
  { label: "At least 8 characters", test: (p: string) => p.length >= 8 },
  { label: "One uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "One lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { label: "One number", test: (p: string) => /\d/.test(p) },
];

export default function LoginPage() {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("signIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  const emailValid = EMAIL_REGEX.test(email);
  const passwordValid =
    mode !== "signUp" || PASSWORD_RULES.every((r) => r.test(password));

  const switchMode = (next: Mode) => {
    setMode(next);
    setError("");
    setSuccess("");
    setEmailTouched(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!emailValid) {
      setError("Please enter a valid email address.");
      return;
    }
    if (mode === "signUp" && !passwordValid) {
      setError("Password does not meet the requirements.");
      return;
    }

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
                onBlur={() => setEmailTouched(true)}
                className={`mt-1 block w-full rounded-lg border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 ${
                  emailTouched && !emailValid && email.length > 0
                    ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                }`}
                placeholder="you@biu.ac.il"
              />
              {emailTouched && !emailValid && email.length > 0 && (
                <p className="mt-1 text-xs text-red-600">
                  Please enter a valid email address.
                </p>
              )}
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
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  placeholder={
                    mode === "signUp"
                      ? "Min 8 chars, uppercase, number"
                      : "Enter your password"
                  }
                />
                {mode === "signUp" && password.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {PASSWORD_RULES.map((rule) => {
                      const passed = rule.test(password);
                      return (
                        <li
                          key={rule.label}
                          className={`flex items-center gap-1.5 text-xs ${
                            passed ? "text-green-600" : "text-gray-400"
                          }`}
                        >
                          <svg
                            className="h-3.5 w-3.5 flex-shrink-0"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                          >
                            {passed ? (
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M5 13l4 4L19 7"
                              />
                            ) : (
                              <circle cx="12" cy="12" r="9" />
                            )}
                          </svg>
                          {rule.label}
                        </li>
                      );
                    })}
                  </ul>
                )}
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

          {mode === "signUp" && (
            <div className="mt-4 rounded-lg bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
              <p className="font-semibold mb-1">⚠️ Security Disclaimer</p>
              This is a student project in early development. Please use a{" "}
              <strong>new, unique password</strong> (not one you use elsewhere)
              and consider using a <strong>burner email</strong>. The platform
              owner is not liable for any data breaches.
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
