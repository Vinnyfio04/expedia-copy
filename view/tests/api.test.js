import assert from 'node:assert/strict'
import test from 'node:test'

import {
  cancelBooking,
  createBooking,
  fetchBookingHistory,
  fetchHotels,
  searchHotels,
} from '../src/api.js'


function jsonResponse(data) {
  return {
    ok: true,
    json: async () => data,
  }
}

test('fetchHotels requests the hotel table', async (context) => {
  const rows = [{ hotel_id: 'H001', hotel_name: 'Harbor Lantern Hotel' }]
  const fetchMock = context.mock.fn(async () => jsonResponse(rows))
  globalThis.fetch = fetchMock

  assert.deepEqual(await fetchHotels(), rows)
  assert.equal(fetchMock.mock.calls[0].arguments[0], '/api/hotels')
})

test('fetchBookingHistory requests the joined read-only history', async (context) => {
  const rows = [{ booking_id: 'B001', hotel_name: 'Harbor Lantern Hotel' }]
  const fetchMock = context.mock.fn(async () => jsonResponse(rows))
  globalThis.fetch = fetchMock

  assert.deepEqual(await fetchBookingHistory(), rows)
  assert.equal(fetchMock.mock.calls[0].arguments[0], '/api/bookings/history')
})

test('createBooking posts the booking form details', async (context) => {
  const created = { booking_id: 'B007', status: 'confirmed' }
  const fetchMock = context.mock.fn(async () => jsonResponse(created))
  globalThis.fetch = fetchMock
  const details = {
    hotel_id: 'H001',
    full_name: 'Demo traveler 21457',
    check_in: '2026-11-21',
    check_out: '2026-11-28',
  }

  assert.deepEqual(await createBooking(details), created)
  assert.equal(fetchMock.mock.calls[0].arguments[0], '/api/bookings')
  assert.deepEqual(fetchMock.mock.calls[0].arguments[1], {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(details),
  })
})

test('cancelBooking patches the selected booking', async (context) => {
  const cancelled = { booking_id: 'B007', status: 'canceled' }
  const fetchMock = context.mock.fn(async () => jsonResponse(cancelled))
  globalThis.fetch = fetchMock

  assert.deepEqual(await cancelBooking('B007'), cancelled)
  assert.equal(fetchMock.mock.calls[0].arguments[0], '/api/bookings/B007/cancel')
  assert.deepEqual(fetchMock.mock.calls[0].arguments[1], { method: 'PATCH' })
})

test('searchHotels returns unique hotel rows from matching stays', async (context) => {
  const fetchMock = context.mock.fn(async () =>
    jsonResponse({
      results: [
        {
          hotel_id: 'H001',
          hotel_name: 'Harbor Lantern Hotel',
          city: 'Boston',
          state: 'MA',
          nightly_rate_usd: 150,
        },
        {
          hotel_id: 'H001',
          hotel_name: 'Harbor Lantern Hotel',
          city: 'Boston',
          state: 'MA',
          nightly_rate_usd: 150,
        },
      ],
    }),
  )
  globalThis.fetch = fetchMock

  const hotels = await searchHotels('Harbor Lantern')

  assert.equal(hotels.length, 1)
  assert.equal(hotels[0].hotel_id, 'H001')
  assert.equal(
    fetchMock.mock.calls[0].arguments[0],
    '/api/search?hotel_name=Harbor%20Lantern',
  )
})
