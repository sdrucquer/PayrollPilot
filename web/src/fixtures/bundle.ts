// Fixture bundle used when VITE_DATA_MODE=fixture. Validated by `npm run check:contracts`.
import raw from './placeholder_bundle.json'
import type {
  Health, PayrollCycle, PayrollException, PPEvent, ReadinessResponse, Worker,
} from '../contracts'

export interface FixtureBundle {
  health: Health
  cycle: PayrollCycle
  workers: Worker[]
  readiness: ReadinessResponse
  exceptions: PayrollException[]
  events: PPEvent[]
}

const bundle = raw as unknown as FixtureBundle
export default bundle
