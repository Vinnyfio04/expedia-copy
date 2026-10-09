const MAX_QUESTION_LENGTH = 1000

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

export function validateHotelQuestion(value) {
  const question = typeof value === 'string' ? value.trim() : ''
  if (!question) {
    return {
      question: '',
      error: 'Enter a hotel question.',
    }
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    return {
      question,
      error: `Keep the question under ${MAX_QUESTION_LENGTH + 1} characters.`,
    }
  }
  return { question, error: '' }
}

export function formatHotelChatMoney(cents) {
  return Number.isInteger(cents) && cents >= 0
    ? usdFormatter.format(cents / 100)
    : 'Not available'
}

export function formatHotelChatDate(value) {
  const parsed = new Date(`${value}T00:00:00Z`)
  return Number.isNaN(parsed.valueOf()) ? value : dateFormatter.format(parsed)
}

export function hotelChatStatusLabel(status) {
  if (status === 'answered') {
    return 'Answer from saved data'
  }
  if (status === 'insufficient_data') {
    return 'Insufficient saved data'
  }
  return 'No saved matches'
}

export function hotelChatStatusGuidance(status) {
  if (status === 'answered') {
    return 'Verified against your saved hotel records.'
  }
  if (status === 'insufficient_data') {
    return 'A matching saved hotel is missing one or more requested nightly records. Missing nights are never treated as available.'
  }
  return 'No matching hotel is saved locally. Use ZIP search and Add to Local before asking about rates or availability.'
}

export function hotelChatErrorLabel(code) {
  const labels = {
    invalid_grounded_answer: 'Grounding check failed',
    invalid_model_query: 'Unsafe query blocked',
    llm_not_configured: 'Assistant setup required',
    llm_rate_limited: 'Assistant rate limited',
    llm_unavailable: 'Assistant unavailable',
  }
  return labels[code] ?? 'Request failed'
}

export function hotelChatErrorGuidance(code) {
  if (code === 'invalid_model_query') {
    return 'The proposed query was rejected and no database changes were made.'
  }
  if (code === 'invalid_grounded_answer') {
    return 'The response was withheld because it could not be verified against the retrieved records.'
  }
  if (code === 'llm_not_configured') {
    return 'The backend needs its Gemini configuration before the assistant can answer.'
  }
  return 'Your saved hotel data was not changed. Please try again in a moment.'
}
