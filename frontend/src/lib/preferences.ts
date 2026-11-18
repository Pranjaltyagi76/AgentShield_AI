export type DemoProfile = 'hardened' | 'vulnerable'
const key = 'agentshield.demo-profile'
export function defaultDemoProfile(): DemoProfile {
  return sessionStorage.getItem(key) === 'vulnerable' ? 'vulnerable' : 'hardened'
}
export function saveDemoProfile(profile: DemoProfile) {
  if (profile !== 'hardened' && profile !== 'vulnerable') throw Error('Unsupported demo profile.')
  sessionStorage.setItem(key, profile)
  window.dispatchEvent(new Event('agentshield-preferences'))
}
export function subscribePreferences(listener: () => void) {
  window.addEventListener('agentshield-preferences', listener)
  return () => window.removeEventListener('agentshield-preferences', listener)
}
