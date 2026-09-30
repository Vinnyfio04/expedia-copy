const US_POSTCODE_PATTERN = /^[0-9]{5}$/


export function isValidUsPostcode(value) {
  return typeof value === 'string' && US_POSTCODE_PATTERN.test(value)
}
