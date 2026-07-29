export type ActiveTab = 'emulator' | 'code' | 'keys' | 'files' | 'setup';

export interface LicenseKey {
  id: string;
  key: string;
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED' | 'UNBOUND';
  expiryDate: string; // YYYY-MM-DD
  daysRemaining: number;
  registeredHwid: string | null;
  note: string;
  createdAt: string;
}

export type VerificationStatus = 'SUCCESS' | 'EXPIRED' | 'INVALID' | 'DEVICE_MISMATCH';

export interface VerificationResponse {
  status: VerificationStatus;
  message: string;
  timestamp: string;
  data?: {
    key: string;
    expiry_date: string;
    days_remaining: number;
    registered_hwid: string;
    hwid_matched: boolean;
  };
}

export interface VirtualFile {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  content?: string;
  children?: VirtualFile[];
}

export interface ExecutionLog {
  id: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'cyber';
  text: string;
}
