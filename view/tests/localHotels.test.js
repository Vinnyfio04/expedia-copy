import assert from 'node:assert/strict'
import test from 'node:test'

import { searchHotelsLocalFirst } from '../src/localHotels.js'


test('returns matching local hotels without calling the provider', async (context) => {
  const local = {
    count: 1,
    results: [{ provider_place_id: 'saved-1' }],
    saved_hotel_ids: ['saved-1'],
  }
  const loadSavedHotels = context.mock.fn(async () => local)
  const loadApiHotels = context.mock.fn(async () => {
    throw new Error('provider must not be called')
  })

  const result = await searchHotelsLocalFirst('16802', {
    loadSavedHotels,
    loadApiHotels,
  })

  assert.equal(result.source, 'local')
  assert.equal(result.response, local)
  assert.deepEqual([...result.savedHotelIds], ['saved-1'])
  assert.equal(loadApiHotels.mock.callCount(), 0)
})

test('calls the provider only after a successful empty local result', async (context) => {
  const api = { count: 1, results: [{ provider_place_id: 'api-1' }] }
  const loadSavedHotels = context.mock.fn(async () => ({
    count: 0,
    results: [],
    saved_hotel_ids: ['saved-elsewhere'],
  }))
  const loadApiHotels = context.mock.fn(async () => api)

  const result = await searchHotelsLocalFirst('16802', {
    loadSavedHotels,
    loadApiHotels,
  })

  assert.equal(result.source, 'api')
  assert.equal(result.response, api)
  assert.deepEqual([...result.savedHotelIds], ['saved-elsewhere'])
  assert.equal(loadApiHotels.mock.callCount(), 1)
})

test('does not call the provider when the local request fails', async (context) => {
  const localError = new Error('local storage failed')
  const loadSavedHotels = context.mock.fn(async () => {
    throw localError
  })
  const loadApiHotels = context.mock.fn(async () => ({ count: 0, results: [] }))

  await assert.rejects(
    searchHotelsLocalFirst('16802', { loadSavedHotels, loadApiHotels }),
    localError,
  )
  assert.equal(loadApiHotels.mock.callCount(), 0)
})
