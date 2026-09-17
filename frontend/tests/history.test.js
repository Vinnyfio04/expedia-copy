import assert from 'node:assert/strict'
import test from 'node:test'

import { isBookingCancelled } from '../src/history.js'


test('recognizes both supplied and newly persisted cancellation spellings', () => {
  assert.equal(isBookingCancelled('cancelled'), true)
  assert.equal(isBookingCancelled('canceled'), true)
  assert.equal(isBookingCancelled('confirmed'), false)
})
