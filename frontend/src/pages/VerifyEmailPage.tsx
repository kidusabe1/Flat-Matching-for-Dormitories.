import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import client from "../api/client";

export default function VerifyEmailPage() {
  const { user, setEmailVerified } = useAuth();
  const navigate = useNavigate();
  const [pin, setPin] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const hasSentRef = useRef(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Send PIN on first load (ref prevents double-send in strict mode)
  useEffect(() => {
    if (user && !hasSentRef.current) {
      hasSentRef.current = true;
      handleSendPin();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleSendPin = async () => {
    setSending(true);
    setError("");
    try {
      await client.post("/api/v1/auth/send-verification");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to send verification email";
      setError(message);
    } finally {
      setSending(false);
    }
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...pin];
    next[index] = value.slice(-1);
    setPin(next);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !pin[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pasted) return;
    const next = [...pin];
    for (let i = 0; i < 6; i++) {
      next[i] = pasted[i] ?? "";
    }
    setPin(next);
    const focusIndex = Math.min(pasted.length, 5);
    inputRefs.current[focusIndex]?.focus();
  };

  const handleVerify = async () => {
    const code = pin.join("");
    if (code.length !== 6) {
      setError("Please enter the full 6-digit PIN.");
      return;
    }
    setVerifying(true);
    setError("");
    try {
      await client.post("/api/v1/auth/verify-pin", { pin: code });
      setEmailVerified(true);
      navigate("/onboarding");
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Verification failed";
      // Try to extract detail from axios error
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail ?? msg);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-blue-600">BIU Dorm Exchange</h1>
          <p className="mt-2 text-sm text-gray-500">Verify your email address</p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Check your email
          </h2>
          <p className="mb-6 text-sm text-gray-500">
            We sent a 6-digit PIN to{" "}
            <span className="font-medium text-gray-700">{user?.email}</span>.
            Enter it below to verify your account.
          </p>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* PIN inputs */}
          <div className="flex justify-center gap-1.5 sm:gap-2" onPaste={handlePaste}>
            {pin.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                className="h-11 w-11 rounded-lg border border-gray-300 text-center text-xl font-bold text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none sm:h-12 sm:w-12"
              />
            ))}
          </div>

          <button
            onClick={handleVerify}
            disabled={verifying || pin.join("").length !== 6}
            className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {verifying ? "Verifying..." : "Verify Email"}
          </button>

          <div className="mt-4 text-center">
            <button
              onClick={handleSendPin}
              disabled={sending}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
            >
              {sending ? "Sending..." : "Resend PIN"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
