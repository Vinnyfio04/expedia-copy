export function isBookingCancelled(status) {
  return status === 'cancelled' || status === 'canceled'
}

export function bookingCountLabel(count) {
  return `${count} ${count === 1 ? 'booking' : 'bookings'}`
}
