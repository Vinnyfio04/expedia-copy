import assert from 'node:assert/strict'
import test from 'node:test'

import { getTopbarTravelAction } from '../src/navigation.js'


test('shows Trips on stays and routes to booking history', () => {
  assert.deepEqual(getTopbarTravelAction('stays'), {
    label: 'Trips',
    view: 'history',
  })
})

test('shows Stays on booking history and routes to stays', () => {
  assert.deepEqual(getTopbarTravelAction('history'), {
    label: 'Stays',
    view: 'stays',
  })
})

test('shows Stays while creating a booking and routes to stays', () => {
  assert.deepEqual(getTopbarTravelAction('booking'), {
    label: 'Stays',
    view: 'stays',
  })
})
