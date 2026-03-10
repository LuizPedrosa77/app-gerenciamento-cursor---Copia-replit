/**
 * Type definitions for Vite environment variables
 */

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_WS_URL: string;
  readonly VITE_ENABLE_REPLAY: string;
  readonly VITE_ENABLE_AI: string;
  readonly VITE_ENABLE_BROKER_SYNC: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare const importMeta: ImportMeta;
