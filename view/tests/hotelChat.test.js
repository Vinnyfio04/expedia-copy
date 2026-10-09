import assert from 'node:assert/strict'
import test from 'node:test'

import {
  formatHotelChatDate,
  formatHotelChatMoney,
  hotelChatErrorGuidance,
  hotelChatErrorLabel,
  hotelChatStatusGuidance,
  hotelChatStatusLabel,
  validateHotelQuestion,
} from '../src/hotelChat.js'


test('validateHotelQuestion trims a usable stateless question', () => {
  assert.deepEqual(validateHotelQuestion('  Compare my saved hotels.  '), {
    question: 'Compare my saved hotels.',
    error: '',
  })
})

test('validateHotelQuestion rejects blank and oversized input', () => {
  assert.equal(
    validateHotelQuestion('   ').error,
    'Enter a hotel question.',
  )
  assert.equal(
    validateHotelQuestion('x'.repeat(1001)).error,
    'Keep the question under 1001 characters.',
  )
})

test('hotel chat display helpers format grounded evidence', () => {
  assert.equal(formatHotelChatMoney(25_050), '$250.50')
  assert.equal(formatHotelChatMoney(null), 'Not available')
  assert.equal(formatHotelChatDate('2026-10-10'), 'Oct 10, 2026')
  assert.equal(hotelChatStatusLabel('answered'), 'Answer from saved data')
  assert.equal(
    hotelChatStatusLabel('insufficient_data'),
    'Insufficient saved data',
  )
  assert.equal(hotelChatStatusLabel('no_matches'), 'No saved matches')
})

test('hotel chat status guidance explains the local-data outcome', () => {
  assert.equal(
    hotelChatStatusGuidance('answered'),
    'Verified against your saved hotel records.',
  )
  assert.match(
    hotelChatStatusGuidance('no_matches'),
    /ZIP search and Add to Local/,
  )
  assert.match(
    hotelChatStatusGuidance('insufficient_data'),
    /Missing nights are never treated as available/,
  )
})

test('hotel chat error helpers present sanitized failure states', () => {
  assert.equal(hotelChatErrorLabel('llm_not_configured'), 'Assistant setup required')
  assert.equal(hotelChatErrorLabel('llm_rate_limited'), 'Assistant rate limited')
  assert.equal(hotelChatErrorLabel('llm_unavailable'), 'Assistant unavailable')
  assert.equal(hotelChatErrorLabel('invalid_model_query'), 'Unsafe query blocked')
  assert.equal(
    hotelChatErrorLabel('invalid_grounded_answer'),
    'Grounding check failed',
  )
  assert.equal(hotelChatErrorLabel(null), 'Request failed')
  assert.match(hotelChatErrorGuidance('invalid_model_query'), /no database changes/)
  assert.match(hotelChatErrorGuidance('invalid_grounded_answer'), /withheld/)
  assert.match(hotelChatErrorGuidance('llm_not_configured'), /Gemini configuration/)
  assert.match(hotelChatErrorGuidance('llm_unavailable'), /not changed/)
})
