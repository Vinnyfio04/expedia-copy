import assert from 'node:assert/strict'
import test from 'node:test'

import { cancelBookingPreview } from '../src/history.js'


test('cancels only the selected booking in the frontend preview', () => {
  const bookings = [
    { booking_id: 'B001', status: 'confirmed' },
    { booking_id: 'B002', status: 'confirmed' },
  ]

  const updated = cancelBookingPreview(bookings, 'B001')

  assert.equal(updated[0].status, 'cancelled')
  assert.equal(updated[1].status, 'confirmed')
  assert.equal(bookings[0].status, 'confirmed')
})
