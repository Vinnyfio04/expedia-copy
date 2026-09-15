import assert from 'node:assert/strict'
import test from 'node:test'

import {
  calculateNightCount,
  calculateStayCost,
  validateBookingDetails,
} from '../src/booking.js'


test('calculates nights and estimated hotel cost from entered dates', () => {
  assert.equal(calculateNightCount('2026-09-18', '2026-09-20'), 2)
  assert.equal(calculateStayCost(150, '2026-09-18', '2026-09-20'), 300)
})

test('validates the traveler name and required dates', () => {
  assert.deepEqual(
    validateBookingDetails({ fullName: 'Demo', checkIn: '', checkOut: '' }),
    {
      fullName: 'Enter both a first and last name.',
      checkIn: 'Choose a check-in date.',
      checkOut: 'Choose a check-out date.',
    },
  )
})

test('requires check-out to be after check-in', () => {
  assert.deepEqual(
    validateBookingDetails({
      fullName: 'Demo Traveler',
      checkIn: '2026-09-20',
      checkOut: '2026-09-18',
    }),
    { checkOut: 'Check-out must be after check-in.' },
  )
})

test('accepts a complete valid booking form', () => {
  assert.deepEqual(
    validateBookingDetails({
      fullName: 'Demo Traveler',
      checkIn: '2026-09-18',
      checkOut: '2026-09-20',
    }),
    {},
  )
})
