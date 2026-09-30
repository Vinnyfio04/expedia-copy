<script setup>
import { computed, nextTick, ref } from 'vue'

import { ApiError, searchNearbyHotels } from '../api.js'
import { isValidUsPostcode } from '../postcode.js'
import HotelMap from './HotelMap.vue'


const postcode = ref('')
const requestedPostcode = ref('')
const center = ref(null)
const hotels = ref([])
const selectedPlaceId = ref(null)
const isLoading = ref(false)
const hasSearched = ref(false)
const errorCode = ref('')
const errorMessage = ref('')
const cardElements = new Map()

const resultSummary = computed(() => {
  if (!hasSearched.value) {
    return ''
  }

  const count = hotels.value.length
  if (count === 0) {
    return `No nearby matches were found within 5 km of ZIP ${requestedPostcode.value}.`
  }

  const noun = count === 1 ? 'match' : 'matches'
  return `Showing ${count} nearby ${noun} within 5 km of ZIP ${requestedPostcode.value}. Geoapify returns up to 20 results.`
})

function setCardElement(placeId, element) {
  if (element) {
    cardElements.set(placeId, element)
  } else {
    cardElements.delete(placeId)
  }
}

function clearSearchState() {
  requestedPostcode.value = ''
  center.value = null
  hotels.value = []
  selectedPlaceId.value = null
  hasSearched.value = false
  errorCode.value = ''
  errorMessage.value = ''
}

function clearValidationError() {
  if (errorCode.value === 'invalid_postcode') {
    errorCode.value = ''
    errorMessage.value = ''
  }
}

async function submitSearch() {
  if (isLoading.value) {
    return
  }

  clearSearchState()
  if (!isValidUsPostcode(postcode.value)) {
    errorCode.value = 'invalid_postcode'
    errorMessage.value = 'Enter a five-digit U.S. ZIP code.'
    return
  }

  isLoading.value = true

  try {
    const response = await searchNearbyHotels(postcode.value)
    requestedPostcode.value = response.requested_postcode
    center.value = response.center
    hotels.value = response.results
    hasSearched.value = true
  } catch (error) {
    if (error instanceof ApiError) {
      errorCode.value = error.code ?? 'provider_unavailable'
      errorMessage.value = error.message
    } else {
      errorCode.value = 'provider_unavailable'
      errorMessage.value = 'The hotel provider is unavailable.'
    }
  } finally {
    isLoading.value = false
  }
}

function selectHotel(placeId) {
  selectedPlaceId.value = placeId
}

async function selectHotelFromMap(placeId) {
  selectedPlaceId.value = placeId
  await nextTick()
  cardElements.get(placeId)?.scrollIntoView({
    behavior: 'smooth',
    block: 'nearest',
  })
}

function formatDistance(distance) {
  return `${Math.round(distance).toLocaleString()} m from search center`
}
</script>

<template>
  <section class="nearby-search" aria-labelledby="nearby-search-title">
    <header class="nearby-search-header">
      <p>Explore the area</p>
      <h2 id="nearby-search-title">Find nearby hotel matches</h2>
      <p>Search for up to 20 Geoapify hotel places within 5 km of a U.S. ZIP code.</p>
    </header>

    <form class="nearby-search-form" novalidate @submit.prevent="submitSearch">
      <div class="nearby-search-field">
        <label for="nearby-postcode">ZIP code</label>
        <input
          id="nearby-postcode"
          v-model="postcode"
          name="postcode"
          type="text"
          inputmode="numeric"
          autocomplete="postal-code"
          maxlength="5"
          pattern="[0-9]{5}"
          placeholder="Enter ZIP code"
          :aria-invalid="errorCode === 'invalid_postcode'"
          aria-describedby="nearby-search-feedback"
          @input="clearValidationError"
        />
      </div>
      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Searching…' : 'Search ZIP' }}
      </button>
    </form>

    <div id="nearby-search-feedback" class="nearby-search-feedback">
      <p v-if="errorMessage" class="nearby-search-error" role="alert">
        {{ errorMessage }}
      </p>
      <p v-else-if="isLoading" role="status" aria-live="polite">
        Finding nearby matches…
      </p>
      <p v-else-if="hasSearched" role="status" aria-live="polite">
        {{ resultSummary }}
      </p>
      <p v-else>Enter a ZIP code to search for nearby matches.</p>
    </div>

    <div class="nearby-results-layout">
      <section class="nearby-list-panel" aria-label="Nearby hotel matches">
        <div v-if="isLoading" class="nearby-list-empty" role="status">
          <strong>Searching nearby places</strong>
          <span>Results will appear here when the request finishes.</span>
        </div>

        <ol v-else-if="hotels.length" class="nearby-hotel-list">
          <li v-for="hotel in hotels" :key="hotel.provider_place_id">
            <button
              :ref="(element) => setCardElement(hotel.provider_place_id, element)"
              type="button"
              class="nearby-hotel-card"
              :class="{ selected: selectedPlaceId === hotel.provider_place_id }"
              :aria-pressed="selectedPlaceId === hotel.provider_place_id"
              @click="selectHotel(hotel.provider_place_id)"
            >
              <strong>{{ hotel.name ?? 'Name unavailable' }}</strong>
              <span v-if="hotel.formatted_address">{{ hotel.formatted_address }}</span>
              <small v-if="hotel.distance_meters !== null">
                {{ formatDistance(hotel.distance_meters) }}
              </small>
              <small>View on map <span aria-hidden="true">→</span></small>
            </button>
          </li>
        </ol>

        <div v-else-if="hasSearched" class="nearby-list-empty" role="status">
          <strong>No nearby matches found</strong>
          <span>Geoapify returned no hotel places within the 5 km search area.</span>
        </div>

        <div v-else class="nearby-list-empty">
          <strong>No nearby matches yet</strong>
          <span>Submit a five-digit ZIP code to begin.</span>
        </div>
      </section>

      <HotelMap
        v-if="center"
        :center="center"
        :hotels="hotels"
        :selected-place-id="selectedPlaceId"
        @select="selectHotelFromMap"
      />
      <div v-else class="nearby-map-placeholder" aria-label="Map placeholder">
        <span aria-hidden="true">⌖</span>
        <strong>Map ready for a ZIP search</strong>
        <p>The resolved search area and hotel markers will appear here.</p>
      </div>
    </div>
  </section>
</template>
