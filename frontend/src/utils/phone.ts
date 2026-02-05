export const COUNTRY_CODES = [
  { code: "+972", label: "IL +972" },
  { code: "+1", label: "US +1" },
  { code: "+44", label: "UK +44" },
  { code: "+33", label: "FR +33" },
  { code: "+49", label: "DE +49" },
  { code: "+7", label: "RU +7" },
  { code: "+380", label: "UA +380" },
  { code: "+91", label: "IN +91" },
  { code: "+86", label: "CN +86" },
  { code: "+55", label: "BR +55" },
  { code: "+34", label: "ES +34" },
  { code: "+39", label: "IT +39" },
  { code: "+61", label: "AU +61" },
  { code: "+81", label: "JP +81" },
  { code: "+82", label: "KR +82" },
  { code: "+90", label: "TR +90" },
  { code: "+971", label: "AE +971" },
  { code: "+20", label: "EG +20" },
  { code: "+27", label: "ZA +27" },
  { code: "+251", label: "ET +251" },
];

/** Try to split a full phone string like "+972501234567" into country code + local number. */
export function parsePhone(phone: string): { countryCode: string; number: string } {
  if (!phone) return { countryCode: "+972", number: "" };
  // Try longest codes first to avoid ambiguity (e.g. +971 vs +97 vs +9)
  const sorted = [...COUNTRY_CODES].sort((a, b) => b.code.length - a.code.length);
  for (const cc of sorted) {
    if (phone.startsWith(cc.code)) {
      return { countryCode: cc.code, number: phone.slice(cc.code.length) };
    }
  }
  return { countryCode: "+972", number: phone.replace(/^\+/, "") };
}

/** Validate that a local phone number (without country code) has 7-15 digits. */
export function isValidPhoneNumber(number: string): boolean {
  const digits = number.replace(/[\s-]/g, "");
  return /^\d{7,15}$/.test(digits);
}
