<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { fetchHotels, searchHotels } from './api.js'
import BookingScreen from './components/BookingScreen.vue'


const query = ref('')
const hotels = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const selectedHotel = ref(null)

const resultSummary = computed(() => {
  const count = hotels.value.length
  return `${count} ${count === 1 ? 'hotel' : 'hotels'} found.`
})

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

function formatRate(rate) {
  return currencyFormatter.format(rate)
}

async function loadHotels(searchTerm = '') {
  isLoading.value = true
  errorMessage.value = ''

  try {
    hotels.value = searchTerm
      ? await searchHotels(searchTerm)
      : await fetchHotels()
  } catch {
    hotels.value = []
    errorMessage.value = 'Unable to load hotels. Please try again.'
  } finally {
    isLoading.value = false
  }
}

function submitSearch() {
  loadHotels(query.value.trim())
}

async function selectHotel(hotel) {
  selectedHotel.value = hotel
  await nextTick()
  window.scrollTo({ top: 0, left: 0 })
}

async function returnToSearch() {
  selectedHotel.value = null
  await nextTick()
  window.scrollTo({ top: 0, left: 0 })
}

onMounted(() => loadHotels())
</script>

<template>
  <main class="app-shell" :class="{ 'booking-shell': selectedHotel }">
    <BookingScreen
      v-if="selectedHotel"
      :hotel="selectedHotel"
      @back="returnToSearch"
    />

    <template v-else>
      <header class="hero-copy">
        <p class="eyebrow">expedia-copy stays</p>
        <h1>Find a hotel<br />made for the trip.</h1>
        <p class="hero-intro">
          Search our hotel collection and compare nightly rates at a glance.
        </p>
      </header>

      <section class="search-panel" aria-labelledby="page-title">
        <header class="page-header">
          <div class="brand-mark" aria-hidden="true">e</div>
          <div>
            <h2 id="page-title">Choose your stay</h2>
            <p>Hotel stays · Nightly pricing</p>
          </div>
        </header>

        <form class="search-form" @submit.prevent="submitSearch">
          <label class="visually-hidden" for="hotel-name">Hotel name</label>
          <div class="search-controls">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path
                d="m21 21-4.35-4.35m2.35-5.15a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z"
              />
            </svg>
            <input
              id="hotel-name"
              v-model="query"
              name="hotel-name"
              type="search"
              placeholder="Try Harbor Lantern Hotel"
            />
            <button type="submit" :disabled="isLoading">
              {{ isLoading ? 'Searching…' : 'Search' }}
            </button>
          </div>
        </form>

        <p v-if="errorMessage" class="status-message error-message" role="alert">
          {{ errorMessage }}
        </p>
        <p v-else class="status-message" aria-live="polite">
          {{ isLoading ? 'Loading hotels…' : resultSummary }}
        </p>

        <ul v-if="hotels.length" class="result-list" aria-label="Hotel results">
          <li v-for="hotel in hotels" :key="hotel.hotel_id">
            <button
              type="button"
              class="hotel-card"
              :aria-label="`Book a stay at ${hotel.hotel_name}`"
              @click="selectHotel(hotel)"
            >
              <div class="property-image" aria-hidden="true">
                <span class="sun"></span>
                <span class="building building-one"></span>
                <span class="building building-two"></span>
                <span class="hotel-id">{{ hotel.hotel_id }}</span>
              </div>

              <div class="property-details">
                <p class="location">{{ hotel.city }}, {{ hotel.state }}</p>
                <h3>{{ hotel.hotel_name }}</h3>
                <div class="property-tags" aria-label="Hotel details">
                  <span>Hotel stay</span>
                  <span>Rate in USD</span>
                </div>
                <p class="rate-note">
                  <span aria-hidden="true"></span>
                  Nightly rate available
                </p>
              </div>

              <span class="price-module" :aria-label="`${hotel.hotel_name} price`">
                <span class="price-kicker">Nightly rate</span>
                <span class="price">{{ formatRate(hotel.nightly_rate_usd) }}</span>
                <span class="price-period">per night</span>
                <span class="select-stay">Select stay <span aria-hidden="true">→</span></span>
              </span>
            </button>
          </li>
        </ul>

        <div
          v-else-if="!isLoading && !errorMessage"
          class="empty-state"
          role="status"
        >
          <span aria-hidden="true">⌕</span>
          <h3>No hotels found</h3>
          <p>No hotels match that name. Try another search.</p>
        </div>
      </section>
    </template>
  </main>
</template>
