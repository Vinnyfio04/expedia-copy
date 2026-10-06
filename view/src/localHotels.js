export async function searchHotelsLocalFirst(
  postcode,
  { loadSavedHotels, loadApiHotels },
) {
  const savedResponse = await loadSavedHotels(postcode)
  const savedHotelIds = new Set(savedResponse.saved_hotel_ids)

  if (savedResponse.count > 0) {
    return {
      source: 'local',
      response: savedResponse,
      savedHotelIds,
    }
  }

  return {
    source: 'api',
    response: await loadApiHotels(postcode),
    savedHotelIds,
  }
}
