/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Raw file imports (Vite's ?raw suffix)
declare module "*.svg?raw" {
  const content: string
  export default content
}

declare module "*.html?raw" {
  const content: string
  export default content
}

declare module "*.md?raw" {
  const content: string
  export default content
}
