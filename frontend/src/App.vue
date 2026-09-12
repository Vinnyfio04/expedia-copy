<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchHotels, searchHotels } from './api.js'


const query = ref('')
const hotels = ref([])
const isLoading = ref(false)
const errorMessage = ref('')

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

onMounted(() => loadHotels())
</script>

<template>
  <main class="app-shell">
    <section class="search-panel" aria-labelledby="page-title">
      <header class="page-header">
        <p class="eyebrow">expedia-copy</p>
        <h1 id="page-title">Find your hotel</h1>
      </header>

      <form class="search-form" @submit.prevent="submitSearch">
        <label for="hotel-name">Hotel name</label>
        <div class="search-controls">
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

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Hotel ID</th>
              <th scope="col">Hotel Name</th>
              <th scope="col">City</th>
              <th scope="col">State</th>
              <th scope="col" class="rate-column">Nightly Rate (USD)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="hotel in hotels" :key="hotel.hotel_id">
              <td class="hotel-id">{{ hotel.hotel_id }}</td>
              <td class="hotel-name">{{ hotel.hotel_name }}</td>
              <td>{{ hotel.city }}</td>
              <td>{{ hotel.state }}</td>
              <td class="rate-column">
                {{ formatRate(hotel.nightly_rate_usd) }}
              </td>
            </tr>
            <tr v-if="!isLoading && hotels.length === 0 && !errorMessage">
              <td class="empty-cell" colspan="5">No hotels match that name.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>
