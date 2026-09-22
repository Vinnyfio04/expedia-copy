<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { fetchHotels, searchHotels } from './api.js'
import BookingHistory from './components/BookingHistory.vue'
import BookingScreen from './components/BookingScreen.vue'
import { getTopbarTravelAction } from './navigation.js'
import { expediaHeaderLinks, travelProductLinks } from './travelLinks.js'


const query = ref('')
const hotels = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const selectedHotel = ref(null)
const currentView = ref('stays')

const topbarTravelAction = computed(() => getTopbarTravelAction(currentView.value))

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
  currentView.value = 'booking'
  await nextTick()
  window.scrollTo({ top: 0, left: 0 })
}

async function showView(view) {
  selectedHotel.value = null
  currentView.value = view
  await nextTick()
  window.scrollTo({ top: 0, left: 0 })
}

function returnToSearch() {
  showView('stays')
}

onMounted(() => loadHotels())
</script>

<template>
  <main
    class="app-shell"
    :class="{
      'stays-shell': currentView === 'stays',
      'booking-shell': currentView === 'booking',
      'history-shell': currentView === 'history',
    }"
  >
    <header class="expedia-topbar">
      <div class="topbar-inner">
        <div class="topbar-primary">
          <button
            type="button"
            class="expedia-wordmark"
            aria-label="Return to stays"
            @click="showView('stays')"
          >
            <span class="expedia-mark" aria-hidden="true">↗</span>
            <span>Expedia</span>
          </button>
          <a
            v-if="currentView !== 'booking'"
            class="shop-travel-link"
            :href="expediaHeaderLinks.home"
            target="_blank"
            rel="noreferrer"
          >
            Shop travel <span aria-hidden="true">⌄</span>
          </a>
        </div>

        <nav class="topbar-actions" aria-label="Expedia utility links">
          <template v-if="currentView !== 'booking'">
            <span class="currency-label">USD <span aria-hidden="true">• 🇺🇸</span></span>
            <a :href="expediaHeaderLinks.property" target="_blank" rel="noreferrer">
              List your property
            </a>
            <a :href="expediaHeaderLinks.support" target="_blank" rel="noreferrer">
              Support
            </a>
          </template>
          <button
            type="button"
            @click="showView(topbarTravelAction.view)"
          >
            {{ topbarTravelAction.label }}
          </button>
          <span v-if="currentView !== 'booking'" class="messages-icon" aria-label="Messages">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M5 5.5h14v10H9l-4 3v-13Z" />
              <path d="M9 9h6M9 12h4" />
            </svg>
          </span>
          <a
            v-if="currentView !== 'booking'"
            :href="expediaHeaderLinks.signIn"
            target="_blank"
            rel="noreferrer"
          >
            Sign in
          </a>
        </nav>
      </div>
    </header>

    <BookingScreen
      v-if="currentView === 'booking' && selectedHotel"
      :hotel="selectedHotel"
      @back="returnToSearch"
    />

    <BookingHistory v-else-if="currentView === 'history'" @plan-trip="showView('stays')" />

    <template v-else>
      <section class="stays-hero" aria-labelledby="stays-title">
        <div class="hero-overlay" aria-hidden="true"></div>
        <h1 id="stays-title">The one place you go to go places</h1>

        <section class="travel-search-card" aria-label="Travel search">
          <nav class="product-tabs" aria-label="Travel products">
            <button type="button" class="product-tab active" aria-current="page">
              <span class="product-icon" aria-hidden="true">🛏️</span>
              <span>Stays</span>
            </button>
            <a
              v-for="product in travelProductLinks"
              :key="product.label"
              class="product-tab"
              :href="product.href"
              target="_blank"
              rel="noreferrer"
            >
              <span class="product-icon" aria-hidden="true">{{ product.icon }}</span>
              <span>{{ product.label }}</span>
            </a>
          </nav>

          <form class="stays-search-form" @submit.prevent="submitSearch">
            <div class="hotel-search-field">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z" />
                <circle cx="12" cy="9" r="2.2" />
              </svg>
              <div>
                <label for="hotel-name">Hotel name</label>
                <input
                  id="hotel-name"
                  v-model="query"
                  name="hotel-name"
                  type="search"
                  placeholder="Search by hotel name"
                />
              </div>
            </div>
            <button type="submit" class="hero-search-button" :disabled="isLoading">
              {{ isLoading ? 'Searching…' : 'Search' }}
            </button>
          </form>
        </section>
      </section>

      <section class="hotel-results" aria-labelledby="hotel-results-title">
        <header class="results-heading">
          <div>
            <p>Explore stays</p>
            <h2 id="hotel-results-title">Hotels made for the trip</h2>
          </div>
          <p v-if="errorMessage" class="status-message error-message" role="alert">
            {{ errorMessage }}
          </p>
          <p v-else class="status-message" aria-live="polite">
            {{ isLoading ? 'Loading hotels…' : resultSummary }}
          </p>
        </header>

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
