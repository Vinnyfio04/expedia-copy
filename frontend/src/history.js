export function cancelBookingPreview(bookings, bookingId) {
  return bookings.map((booking) =>
    booking.booking_id === bookingId
      ? { ...booking, status: 'cancelled' }
      : booking,
  )
}
