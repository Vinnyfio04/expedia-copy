<script setup>
import { computed, nextTick, ref } from 'vue'

import {
  ApiError,
  removeSavedHotel,
  saveHotelLocally,
  searchNearbyHotels,
  searchSavedHotels,
} from '../api.js'
import { searchHotelsLocalFirst } from '../localHotels.js'
import { isValidUsPostcode } from '../postcode.js'
import HotelMap from './HotelMap.vue'


const postcode = ref('')
const requestedPostcode = ref('')
const center = ref(null)
const hotels = ref([])
const selectedPlaceId = ref(null)
const isLoading = ref(false)
const hasSearched = ref(false)
const resultSource = ref('')
const savedHotelIds = ref(new Set())
const pendingSaveIds = ref(new Set())
const pendingRemoveIds = ref(new Set())
const errorCode = ref('')
const errorMessage = ref('')
const actionFeedback = ref(null)
const cardElements = new Map()
const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

const resultSummary = computed(() => {
  if (!hasSearched.value) {
    return ''
  }

  const count = hotels.value.length
  if (resultSource.value === 'local') {
    if (count === 0) {
      return `No saved local hotels remain for ZIP ${requestedPostcode.value}.`
    }
    const noun = count === 1 ? 'hotel' : 'hotels'
    return `Showing ${count} saved ${noun} for ZIP ${requestedPostcode.value}. This is your saved local subset, not a complete list of hotels in the area.`
  }

  if (count === 0) {
    return `No nearby matches were found within 5 km of ZIP ${requestedPostcode.value}.`
  }

  const noun = count === 1 ? 'match' : 'matches'
  return `Showing ${count} nearby ${noun} within 5 km of ZIP ${requestedPostcode.value}. Geoapify returns up to 20 results.`
})

const resultSourceLabel = computed(() => {
  if (resultSource.value === 'local') {
    return 'Saved locally'
  }
  if (resultSource.value === 'api') {
    return 'API results'
  }
  return ''
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
  resultSource.value = ''
  savedHotelIds.value = new Set()
  errorCode.value = ''
  errorMessage.value = ''
  actionFeedback.value = null
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
    const result = await searchHotelsLocalFirst(postcode.value, {
      loadSavedHotels: searchSavedHotels,
      loadApiHotels: searchNearbyHotels,
    })
    savedHotelIds.value = result.savedHotelIds
    requestedPostcode.value = result.response.requested_postcode
    center.value = result.response.center
    hotels.value = result.response.results
    resultSource.value = result.source
    hasSearched.value = true
  } catch (error) {
    if (error instanceof ApiError) {
      errorCode.value = error.code ?? 'provider_unavailable'
      errorMessage.value = error.message
    } else {
      errorCode.value = 'provider_unavailable'
      errorMessage.value = 'Saved hotels or API results could not be loaded.'
    }
  } finally {
    isLoading.value = false
  }
}

function selectHotel(placeId) {
  selectedPlaceId.value = placeId
}

function updateIdSet(target, placeId, included) {
  const updated = new Set(target.value)
  if (included) {
    updated.add(placeId)
  } else {
    updated.delete(placeId)
  }
  target.value = updated
}

function isSaved(hotel) {
  return savedHotelIds.value.has(hotel.provider_place_id)
}

function isSavePending(hotel) {
  return pendingSaveIds.value.has(hotel.provider_place_id)
}

function isRemovePending(hotel) {
  return pendingRemoveIds.value.has(hotel.provider_place_id)
}

function hotelLabel(hotel) {
  return hotel.name ?? 'This hotel'
}

async function addToLocal(hotel) {
  const placeId = hotel.provider_place_id
  if (!center.value || isSaved(hotel) || isSavePending(hotel)) {
    return
  }

  updateIdSet(pendingSaveIds, placeId, true)
  actionFeedback.value = null
  try {
    await saveHotelLocally(hotel, center.value)
    updateIdSet(savedHotelIds, placeId, true)
    actionFeedback.value = {
      type: 'success',
      message: `${hotelLabel(hotel)} was saved locally.`,
    }
  } catch (error) {
    actionFeedback.value = {
      type: 'error',
      message: error instanceof ApiError
        ? error.message
        : `${hotelLabel(hotel)} could not be saved locally.`,
    }
  } finally {
    updateIdSet(pendingSaveIds, placeId, false)
  }
}

async function removeFromLocal(hotel) {
  const placeId = hotel.provider_place_id
  if (!isSaved(hotel) || isRemovePending(hotel)) {
    return
  }

  updateIdSet(pendingRemoveIds, placeId, true)
  actionFeedback.value = null
  try {
    await removeSavedHotel(placeId)
    updateIdSet(savedHotelIds, placeId, false)
    if (resultSource.value === 'local') {
      hotels.value = hotels.value.filter(
        (result) => result.provider_place_id !== placeId,
      )
      if (selectedPlaceId.value === placeId) {
        selectedPlaceId.value = null
      }
    }
    actionFeedback.value = {
      type: 'success',
      message: `${hotelLabel(hotel)} was removed from local storage.`,
    }
  } catch (error) {
    actionFeedback.value = {
      type: 'error',
      message: error instanceof ApiError
        ? error.message
        : `${hotelLabel(hotel)} could not be removed from local storage.`,
    }
  } finally {
    updateIdSet(pendingRemoveIds, placeId, false)
  }
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

function formatDemoRate(cents) {
  return `${usdFormatter.format(cents / 100)} per night`
}

function formatDemoDate(stayDate) {
  return new Date(`${stayDate}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
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
      <p v-if="resultSourceLabel" class="nearby-result-source">
        {{ resultSourceLabel }}
      </p>
      <p
        v-if="actionFeedback"
        class="nearby-action-feedback"
        :class="{ error: actionFeedback.type === 'error' }"
        :role="actionFeedback.type === 'error' ? 'alert' : 'status'"
        aria-live="polite"
      >
        {{ actionFeedback.message }}
      </p>
    </div>

    <div class="nearby-results-layout">
      <section class="nearby-list-panel" aria-label="Nearby hotel matches">
        <div v-if="isLoading" class="nearby-list-empty" role="status">
          <strong>Searching nearby places</strong>
          <span>Results will appear here when the request finishes.</span>
        </div>

        <ol v-else-if="hotels.length" class="nearby-hotel-list">
          <li v-for="hotel in hotels" :key="hotel.provider_place_id">
            <article
              :ref="(element) => setCardElement(hotel.provider_place_id, element)"
              class="nearby-hotel-card"
              :class="{ selected: selectedPlaceId === hotel.provider_place_id }"
            >
              <button
                type="button"
                class="nearby-hotel-select"
                :aria-pressed="selectedPlaceId === hotel.provider_place_id"
                @click="selectHotel(hotel.provider_place_id)"
              >
                <strong>{{ hotel.name ?? 'Name unavailable' }}</strong>
                <span v-if="hotel.formatted_address">
                  {{ hotel.formatted_address }}
                </span>
                <small v-if="hotel.distance_meters !== null">
                  {{ formatDistance(hotel.distance_meters) }}
                </small>
                <small>View on map <span aria-hidden="true">→</span></small>
              </button>

              <section
                v-if="resultSource === 'local' && hotel.demo_nights?.length"
                class="nearby-demo-data"
                :aria-label="`Simulated classroom rates for ${hotel.name ?? 'saved hotel'}`"
              >
                <strong>Simulated classroom data</strong>
                <ul>
                  <li
                    v-for="night in hotel.demo_nights"
                    :key="`${night.hotel_id}-${night.stay_date}`"
                  >
                    <time :datetime="night.stay_date">
                      {{ formatDemoDate(night.stay_date) }}
                    </time>
                    <span>{{ formatDemoRate(night.nightly_rate_cents) }}</span>
                    <span>{{ night.rooms_available }} rooms available</span>
                  </li>
                </ul>
              </section>

              <div class="nearby-local-actions">
                <span class="nearby-saved-state">
                  {{ isSaved(hotel) ? 'Saved locally' : 'API result' }}
                </span>
                <button
                  type="button"
                  class="nearby-add-button"
                  :disabled="isSaved(hotel) || isSavePending(hotel)"
                  @click="addToLocal(hotel)"
                >
                  {{
                    isSavePending(hotel)
                      ? 'Saving…'
                      : isSaved(hotel)
                        ? 'Added to Local'
                        : 'Add to Local'
                  }}
                </button>
                <button
                  v-if="isSaved(hotel)"
                  type="button"
                  class="nearby-remove-button"
                  :disabled="isRemovePending(hotel)"
                  @click="removeFromLocal(hotel)"
                >
                  {{ isRemovePending(hotel) ? 'Removing…' : 'Remove from Local' }}
                </button>
              </div>
            </article>
          </li>
        </ol>

        <div v-else-if="hasSearched" class="nearby-list-empty" role="status">
          <strong>
            {{
              resultSource === 'local'
                ? 'No saved local hotels remain'
                : 'No nearby matches found'
            }}
          </strong>
          <span v-if="resultSource === 'local'">
            Search this ZIP again to check the existing API results.
          </span>
          <span v-else>
            Geoapify returned no hotel places within the 5 km search area.
          </span>
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
