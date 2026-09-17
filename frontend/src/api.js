const API_BASE = '/api'

async function requestJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options)

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    throw new Error(
      errorBody?.detail ?? `Request failed with status ${response.status}.`,
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
