/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_DATA_MODE?: 'fixture' | 'api'
  readonly VITE_CYCLE_ID?: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
