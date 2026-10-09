const API_BASE = '/api'

export class ApiError extends Error {
  constructor(message, { status, code = null }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function requestJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options)

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    const detail = errorBody?.detail
    const message = typeof detail === 'string' ? detail : detail?.message
    const code = typeof detail === 'object' ? detail?.code : null
    throw new ApiError(
      message ?? `Request failed with status ${response.status}.`,
      {
        status: response.status,
        code: typeof code === 'string' ? code : null,
      },
    )
  }

  return response.json()
}

function hotelFromStay(stay) {
  return {
    hotel_id: stay.hotel_id,
    hotel_name: stay.hotel_name,
    city: stay.city,
    state: stay.state,
    nightly_rate_usd: stay.nightly_rate_usd,
  }
}

export async function fetchHotels() {
  return requestJson('/hotels')
}

export async function searchNearbyHotels(postcode) {
  return requestJson(
    `/hotels/nearby?postcode=${encodeURIComponent(postcode)}`,
  )
}

export async function searchSavedHotels(postcode) {
  return requestJson(
    `/hotels/saved?postcode=${encodeURIComponent(postcode)}`,
  )
}

export async function saveHotelLocally(hotel, searchLocation) {
  return requestJson('/hotels/saved', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      hotel,
      search_location: searchLocation,
    }),
  })
}

export async function removeSavedHotel(hotelId) {
  return requestJson(
    `/hotels/saved?hotel_id=${encodeURIComponent(hotelId)}`,
    { method: 'DELETE' },
  )
}

export async function askHotelQuestion(question) {
  return requestJson('/hotels/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })
}

export async function fetchBookingHistory() {
  return requestJson('/bookings/history')
}

export async function createBooking(bookingDetails) {
  return requestJson('/bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(bookingDetails),
  })
}

export async function cancelBooking(bookingId) {
  return requestJson(`/bookings/${encodeURIComponent(bookingId)}/cancel`, {
    method: 'PATCH',
  })
}

export async function searchHotels(hotelName) {
  const data = await requestJson(
    `/search?hotel_name=${encodeURIComponent(hotelName)}`,
  )
  const hotelsById = new Map(
    data.results.map((stay) => [stay.hotel_id, hotelFromStay(stay)]),
  )

  return [...hotelsById.values()]
}
