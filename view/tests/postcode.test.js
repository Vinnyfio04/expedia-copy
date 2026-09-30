import assert from 'node:assert/strict'
import test from 'node:test'

import { isValidUsPostcode } from '../src/postcode.js'


test('accepts exactly five ASCII digits including a leading zero', () => {
  assert.equal(isValidUsPostcode('16802'), true)
  assert.equal(isValidUsPostcode('02108'), true)
})

test('rejects malformed and non-ASCII postcode values', () => {
  const invalidValues = [
    '',
    '1680',
    '168020',
    '1680A',
    ' 16802',
    '16802 ',
    '１２３４５',
    16802,
    null,
  ]

  for (const value of invalidValues) {
    assert.equal(isValidUsPostcode(value), false)
  }
})
