import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useCreateProfile } from "../hooks/useProfile";
import { COUNTRY_CODES, isValidPhoneNumber } from "../utils/phone";

export default function OnboardingPage() {
  const { user, setHasProfile } = useAuth();
  const navigate = useNavigate();
  const createProfile = useCreateProfile();
  const [fullName, setFullName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [countryCode, setCountryCode] = useState("+972");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState("");
  const [phoneTouched, setPhoneTouched] = useState(false);

  const phoneValid = isValidPhoneNumber(phoneNumber);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!phoneValid) {
      setError("Please enter a valid phone number (7-15 digits).");
      return;
    }

    try {
      await createProfile.mutateAsync({
        full_name: fullName,
        student_id: studentId,
        phone: countryCode + phoneNumber.replace(/[\s-]/g, ""),
      });
      setHasProfile(true);
      navigate("/");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create profile";
      setError(message);
    }
  };

  if (!user) return null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-blue-600">Welcome!</h1>
          <p className="mt-2 text-sm text-gray-500">
            Complete your profile to start using the platform
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          <h2 className="mb-6 text-lg font-semibold text-gray-900">
            Your Profile
          </h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700"
              >
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label
                htmlFor="studentId"
                className="block text-sm font-medium text-gray-700"
              >
                Student ID
              </label>
              <input
                id="studentId"
                type="text"
                required
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label
                htmlFor="phoneNumber"
                className="block text-sm font-medium text-gray-700"
              >
                Phone Number
              </label>
              <div className="mt-1 flex gap-2">
                <select
                  id="countryCode"
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  className="w-28 rounded-lg border border-gray-300 px-2 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                >
                  {COUNTRY_CODES.map((cc) => (
                    <option key={cc.code} value={cc.code}>
                      {cc.label}
                    </option>
                  ))}
                </select>
                <input
                  id="phoneNumber"
                  type="tel"
                  required
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  onBlur={() => setPhoneTouched(true)}
                  className={`block flex-1 rounded-lg border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 ${
                    phoneTouched && !phoneValid && phoneNumber.length > 0
                      ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                      : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  }`}
                  placeholder="501234567"
                />
              </div>
              {phoneTouched && !phoneValid && phoneNumber.length > 0 && (
                <p className="mt-1 text-xs text-red-600">
                  Enter a valid phone number (7-15 digits).
                </p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={createProfile.isPending}
            className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {createProfile.isPending ? "Creating..." : "Complete Profile"}
          </button>
        </form>
      </div>
    </div>
  );
}
