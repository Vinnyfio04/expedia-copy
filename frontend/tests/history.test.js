import assert from 'node:assert/strict'
import test from 'node:test'

import { bookingCountLabel, isBookingCancelled } from '../src/history.js'


test('recognizes both supplied and newly persisted cancellation spellings', () => {
  assert.equal(isBookingCancelled('cancelled'), true)
  assert.equal(isBookingCancelled('canceled'), true)
  assert.equal(isBookingCancelled('confirmed'), false)
})

test('formats singular and plural booking counts', () => {
  assert.equal(bookingCountLabel(1), '1 booking')
  assert.equal(bookingCountLabel(10), '10 bookings')
})
