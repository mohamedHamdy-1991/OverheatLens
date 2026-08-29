import '@testing-library/jest-dom/vitest'

// jsdom lacks the clipboard API used by the export bar — provide a stub.
if (!navigator.clipboard) {
  Object.assign(navigator, {
    clipboard: { writeText: async () => undefined },
  })
}
