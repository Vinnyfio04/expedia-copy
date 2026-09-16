<script setup>
import { onMounted, ref } from 'vue'

import { fetchBookingHistory } from '../api.js'
import { cancelBookingPreview } from '../history.js'


const bookings = ref([])
const isLoading = ref(true)
const errorMessage = ref('')
const notificationMessage = ref('')

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

function formatDate(date) {
  return dateFormatter.format(new Date(`${date}T00:00:00Z`))
}

function cancelBooking(booking) {
  bookings.value = cancelBookingPreview(bookings.value, booking.booking_id)
  notificationMessage.value = `${booking.booking_id} for ${booking.hotel_name} has been canceled in this preview. Nothing has been saved yet.`
}

async function loadBookingHistory() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    bookings.value = await fetchBookingHistory()
  } catch {
    bookings.value = []
    errorMessage.value = 'Unable to load booking history. Please try again.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadBookingHistory)
</script>

<template>
  <section class="history-layout" aria-labelledby="history-title">
    <header class="history-heading">
      <p class="eyebrow">expedia-copy bookings</p>
      <h1 id="history-title">Your booking history.</h1>
      <p>Review every simulated reservation from the supplied travel data.</p>
    </header>

    <p
      v-if="notificationMessage"
      class="history-notification"
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true">✓</span>
      {{ notificationMessage }}
    </p>

    <p v-if="isLoading" class="history-status" aria-live="polite">
      Loading booking history…
    </p>
    <p v-else-if="errorMessage" class="history-status error-message" role="alert">
      {{ errorMessage }}
    </p>
    <p v-else class="history-status">
      {{ bookings.length }} {{ bookings.length === 1 ? 'booking' : 'bookings' }} found.
    </p>

    <ul v-if="bookings.length" class="history-list" aria-label="Booking history">
      <li v-for="booking in bookings" :key="booking.booking_id">
        <article class="history-card">
          <header class="history-card-header">
            <span class="booking-id">{{ booking.booking_id }}</span>
            <span class="booking-status" :class="`status-${booking.status}`">
              {{ booking.status }}
            </span>
          </header>

          <div class="history-card-body">
            <div class="history-primary">
              <p>{{ booking.city }}, {{ booking.state }}</p>
              <h2>{{ booking.hotel_name }}</h2>
              <strong>{{ booking.trip_name }}</strong>
              <span>Traveler: {{ booking.display_name }}</span>
            </div>

            <dl class="history-details">
              <div>
                <dt>Stay</dt>
                <dd>{{ formatDate(booking.check_in) }} – {{ formatDate(booking.check_out) }}</dd>
              </div>
              <div>
                <dt>Length</dt>
                <dd>{{ booking.nights }} {{ booking.nights === 1 ? 'night' : 'nights' }}</dd>
              </div>
              <div>
                <dt>Booked</dt>
                <dd>{{ formatDate(booking.booked_on) }}</dd>
              </div>
              <div>
                <dt>Estimated total</dt>
                <dd>{{ currencyFormatter.format(booking.stay_price_usd) }}</dd>
              </div>
            </dl>
          </div>

          <footer class="history-card-footer">
            <span>Frontend preview · CSV remains unchanged</span>
            <button
              type="button"
              :disabled="booking.status === 'cancelled'"
              @click="cancelBooking(booking)"
            >
              {{ booking.status === 'cancelled' ? 'Cancelled' : 'Cancel booking' }}
            </button>
          </footer>
        </article>
      </li>
    </ul>
  </section>
</template>
