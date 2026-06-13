export interface ApiKeyBase {
  module_uid: number;
}

export interface ApiKeyRead extends ApiKeyBase {
  id: number;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
  key: string; // Clé complète au lieu de key_preview
}

export interface ApiKeyCreate extends ApiKeyBase {}

export interface ApiKeyResponse extends ApiKeyBase {
  id: number;
  key: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
  message: string;
}

export interface ApiKeyUpdate {
  is_active?: boolean;
}
