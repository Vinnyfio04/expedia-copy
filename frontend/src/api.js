const API_BASE = '/api'

async function requestJson(path) {
  const response = await fetch(`${API_BASE}${path}`)

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}.`)
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

export async function searchHotels(hotelName) {
  const data = await requestJson(
    `/search?hotel_name=${encodeURIComponent(hotelName)}`,
  )
  const hotelsById = new Map(
    data.results.map((stay) => [stay.hotel_id, hotelFromStay(stay)]),
  )

  return [...hotelsById.values()]
}
