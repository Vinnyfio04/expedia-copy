import assert from 'node:assert/strict'
import test from 'node:test'

import { expediaHeaderLinks, travelProductLinks } from '../src/travelLinks.js'


test('links each non-stays travel tab to its Expedia product page', () => {
  assert.deepEqual(
    travelProductLinks.map(({ label, href }) => [label, href]),
    [
      ['Flights', 'https://www.expedia.com/Flights'],
      ['Cars', 'https://www.expedia.com/Cars'],
      ['Packages', 'https://www.expedia.com/Vacation-Packages'],
      ['Things to do', 'https://www.expedia.com/Activities'],
      ['Cruises', 'https://www.expedia.com/Cruises'],
    ],
  )
})

test('keeps the Expedia utility destinations external', () => {
  assert.equal(expediaHeaderLinks.home, 'https://www.expedia.com/')
  assert.match(expediaHeaderLinks.property, /^https:\/\/apps\.expediapartnercentral\.com\//)
  assert.equal(expediaHeaderLinks.support, 'https://www.expedia.com/helpcenter/')
  assert.equal(expediaHeaderLinks.signIn, 'https://www.expedia.com/login')
})
