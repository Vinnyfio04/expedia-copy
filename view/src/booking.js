const DAY_IN_MILLISECONDS = 24 * 60 * 60 * 1000
const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/

function dateValue(date) {
  if (!ISO_DATE_PATTERN.test(date)) {
    return Number.NaN
  }

  return Date.parse(`${date}T00:00:00Z`)
}

export function calculateNightCount(checkIn, checkOut) {
  const checkInTime = dateValue(checkIn)
  const checkOutTime = dateValue(checkOut)

  if (!Number.isFinite(checkInTime) || !Number.isFinite(checkOutTime)) {
    return 0
  }

  return Math.max(0, (checkOutTime - checkInTime) / DAY_IN_MILLISECONDS)
}

export function calculateStayCost(nightlyRate, checkIn, checkOut) {
  return calculateNightCount(checkIn, checkOut) * nightlyRate
}

export function validateBookingDetails({ fullName, checkIn, checkOut }) {
  const errors = {}

  if (fullName.trim().split(/\s+/).filter(Boolean).length < 2) {
    errors.fullName = 'Enter both a first and last name.'
  }

  if (!checkIn) {
    errors.checkIn = 'Choose a check-in date.'
  }

  if (!checkOut) {
    errors.checkOut = 'Choose a check-out date.'
  } else if (checkIn && calculateNightCount(checkIn, checkOut) === 0) {
    errors.checkOut = 'Check-out must be after check-in.'
  }

  return errors
}
