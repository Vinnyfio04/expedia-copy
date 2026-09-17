export function isBookingCancelled(status) {
  return status === 'cancelled' || status === 'canceled'
}
