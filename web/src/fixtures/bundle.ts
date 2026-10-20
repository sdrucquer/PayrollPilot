// Fixture bundle used when VITE_DATA_MODE=fixture. Validated by `npm run check:contracts`.
import raw from './bundle.json'
import type {
  Health, PayrollCycle, PayrollException, PPEvent, ReadinessResponse, Worker,
} from '../contracts'

export interface FixtureBundle {
  health: Health
  cycle: PayrollCycle
  workers: Worker[]
  readiness: ReadinessResponse
  readiness_after_t02: ReadinessResponse
  replies: { name: string; batch_exception_ids: string[]; raw_text: string; expect: Record<string, unknown> }[]
  exceptions: PayrollException[]
  events: PPEvent[]
}

const bundle = raw as unknown as FixtureBundle
export default bundle
