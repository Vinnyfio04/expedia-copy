import assert from 'node:assert/strict'
import test from 'node:test'

import { fetchBookingHistory, fetchHotels, searchHotels } from '../src/api.js'


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
