<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { cancelBooking as cancelBookingRequest, fetchBookingHistory } from '../api.js'
import { bookingCountLabel, isBookingCancelled } from '../history.js'


defineEmits(['plan-trip'])

const bookings = ref([])
const isLoading = ref(true)
const errorMessage = ref('')
const notificationMessage = ref('')
const cancellationError = ref('')
const cancellingBookingId = ref('')
let notificationTimer

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

function statusClass(status) {
  return isBookingCancelled(status) ? 'status-cancelled' : `status-${status}`
}

function clearNotification() {
  notificationMessage.value = ''
  if (notificationTimer) {
    window.clearTimeout(notificationTimer)
    notificationTimer = undefined
  }
}

function showNotification(message) {
  clearNotification()
  notificationMessage.value = message
  notificationTimer = window.setTimeout(clearNotification, 4000)
}

async function cancelBooking(booking) {
  if (isBookingCancelled(booking.status) || cancellingBookingId.value) {
    return
  }

  clearNotification()
  cancellationError.value = ''
  cancellingBookingId.value = booking.booking_id

  try {
    const updatedBooking = await cancelBookingRequest(booking.booking_id)
    bookings.value = bookings.value.map((item) =>
      item.booking_id === updatedBooking.booking_id ? updatedBooking : item,
    )
    showNotification('Trip has been successfully canceled.')
  } catch (error) {
    cancellationError.value = error.message
  } finally {
    cancellingBookingId.value = ''
  }
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
onBeforeUnmount(clearNotification)
</script>

<template>
  <section class="history-layout" aria-labelledby="history-title">
    <header class="history-heading">
      <div>
        <p class="eyebrow">expedia-copy travel</p>
        <h1 id="history-title">Trips</h1>
      </div>
      <button type="button" class="plan-trip-link" @click="$emit('plan-trip')">
        <span aria-hidden="true">+</span>
        Plan a trip
      </button>
    </header>

    <nav class="history-tabs" aria-label="Trip sections">
      <span aria-current="page">Bookings</span>
    </nav>

    <p
      v-if="notificationMessage"
      class="history-notification"
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true">✓</span>
      {{ notificationMessage }}
    </p>

    <p
      v-if="cancellationError"
      class="history-notification history-notification-error"
      role="alert"
    >
      {{ cancellationError }}
    </p>

    <div class="history-summary">
      <div>
        <p>Booked stays</p>
        <h2>Your bookings</h2>
      </div>
      <p v-if="isLoading" class="history-status" aria-live="polite">
        Loading booking history…
      </p>
      <p v-else-if="errorMessage" class="history-status error-message" role="alert">
        {{ errorMessage }}
      </p>
      <p v-else class="history-status">
        {{ bookingCountLabel(bookings.length) }}
      </p>
    </div>

    <ul v-if="bookings.length" class="history-list" aria-label="Booking history">
      <li v-for="booking in bookings" :key="booking.booking_id">
        <article class="history-card">
          <header class="history-card-header">
            <span class="booking-id">Booking {{ booking.booking_id }}</span>
            <span class="booking-status" :class="statusClass(booking.status)">
              {{ booking.status }}
            </span>
          </header>

          <div class="history-card-body">
            <div class="history-property-visual" aria-hidden="true">
              <span class="history-sun"></span>
              <span class="history-mountain history-mountain-back"></span>
              <span class="history-mountain history-mountain-front"></span>
              <span class="history-hotel"></span>
            </div>

            <div class="history-booking-content">
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
          </div>

          <footer class="history-card-footer">
            <span>Manage this reservation without leaving your trip history.</span>
            <button
              type="button"
              :disabled="isBookingCancelled(booking.status) || Boolean(cancellingBookingId)"
              @click="cancelBooking(booking)"
            >
              {{
                isBookingCancelled(booking.status)
                  ? 'Cancelled'
                  : cancellingBookingId === booking.booking_id
                    ? 'Canceling...'
                    : 'Cancel booking'
              }}
            </button>
          </footer>
        </article>
      </li>
    </ul>

    <section class="trip-planning-card" aria-labelledby="plan-trip-title">
      <div>
        <p>Plan your next trip</p>
        <h2 id="plan-trip-title">Find another stay for the journey ahead.</h2>
        <button type="button" @click="$emit('plan-trip')">Plan a trip</button>
      </div>
      <div class="trip-planning-visual" aria-hidden="true">
        <span class="planning-sun"></span>
        <span class="planning-ridge planning-ridge-back"></span>
        <span class="planning-ridge planning-ridge-front"></span>
        <span class="planning-route"></span>
      </div>
    </section>
  </section>
</template>
