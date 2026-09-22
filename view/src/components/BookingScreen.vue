<script setup>
import { computed, ref, watch } from 'vue'

import {
  calculateNightCount,
  calculateStayCost,
  validateBookingDetails,
} from '../booking.js'
import { createBooking } from '../api.js'


const props = defineProps({
  hotel: {
    type: Object,
    required: true,
  },
})

defineEmits(['back'])

const fullName = ref('')
const checkIn = ref('')
const checkOut = ref('')
const submitted = ref(false)
const confirmationMessage = ref('')
const submissionError = ref('')
const isSubmitting = ref(false)

const bookingDetails = computed(() => ({
  fullName: fullName.value,
  checkIn: checkIn.value,
  checkOut: checkOut.value,
}))

const errors = computed(() => validateBookingDetails(bookingDetails.value))
const nights = computed(() => calculateNightCount(checkIn.value, checkOut.value))
const totalCost = computed(() =>
  calculateStayCost(props.hotel.nightly_rate_usd, checkIn.value, checkOut.value),
)

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

async function confirmBooking() {
  submitted.value = true
  confirmationMessage.value = ''
  submissionError.value = ''

  if (Object.keys(errors.value).length > 0 || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  try {
    await createBooking({
      hotel_id: props.hotel.hotel_id,
      full_name: fullName.value.trim(),
      check_in: checkIn.value,
      check_out: checkOut.value,
    })
    confirmationMessage.value = 'Booking confirmed'
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

watch([fullName, checkIn, checkOut], () => {
  confirmationMessage.value = ''
  submissionError.value = ''
})
</script>

<template>
  <section class="booking-layout" aria-labelledby="booking-title">
    <button type="button" class="back-button" @click="$emit('back')">
      <span aria-hidden="true">←</span>
      Back to stays
    </button>

    <header class="booking-heading">
      <h1 id="booking-title">Complete your stay.</h1>
      <p>Review the hotel, choose your dates, and enter the traveler name.</p>
    </header>

    <div class="booking-checkout-grid">
      <form class="booking-form" novalidate @submit.prevent="confirmBooking">
        <div class="form-intro">
          <div>
            <p class="section-kicker">Traveler details</p>
            <h2>Who is checking in?</h2>
          </div>
          <span>All fields required</span>
        </div>

        <div class="field-group full-name-field">
          <label for="full-name">First and last name</label>
          <input
            id="full-name"
            v-model="fullName"
            name="full-name"
            type="text"
            autocomplete="name"
            placeholder="Demo Traveler"
            :aria-invalid="submitted && Boolean(errors.fullName)"
            :aria-describedby="submitted && errors.fullName ? 'full-name-error' : undefined"
          />
          <p v-if="submitted && errors.fullName" id="full-name-error" class="field-error">
            {{ errors.fullName }}
          </p>
        </div>

        <div class="date-fields">
          <div class="field-group">
            <label for="check-in">Check-in</label>
            <input
              id="check-in"
              v-model="checkIn"
              name="check-in"
              type="date"
              :aria-invalid="submitted && Boolean(errors.checkIn)"
              :aria-describedby="submitted && errors.checkIn ? 'check-in-error' : 'check-in-hint'"
            />
            <p id="check-in-hint" class="field-hint">Year-month-day</p>
            <p v-if="submitted && errors.checkIn" id="check-in-error" class="field-error">
              {{ errors.checkIn }}
            </p>
          </div>

          <div class="field-group">
            <label for="check-out">Check-out</label>
            <input
              id="check-out"
              v-model="checkOut"
              name="check-out"
              type="date"
              :min="checkIn || undefined"
              :aria-invalid="submitted && Boolean(errors.checkOut)"
              :aria-describedby="submitted && errors.checkOut ? 'check-out-error' : 'check-out-hint'"
            />
            <p id="check-out-hint" class="field-hint">Year-month-day</p>
            <p v-if="submitted && errors.checkOut" id="check-out-error" class="field-error">
              {{ errors.checkOut }}
            </p>
          </div>
        </div>

        <div class="booking-summary" aria-live="polite">
          <div>
            <p>Estimated total</p>
            <strong>
              {{ nights ? currencyFormatter.format(totalCost) : 'Select dates' }}
            </strong>
            <span v-if="nights">
              {{ nights }} {{ nights === 1 ? 'night' : 'nights' }} ×
              {{ currencyFormatter.format(hotel.nightly_rate_usd) }}
            </span>
          </div>
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : 'Confirm' }}
          </button>
        </div>

        <p v-if="confirmationMessage" class="confirmation-message" role="status">
          <span aria-hidden="true">✓</span>
          {{ confirmationMessage }}
        </p>

        <p v-if="submissionError" class="booking-submit-error" role="alert">
          {{ submissionError }}
        </p>
      </form>

      <aside class="booking-hotel-panel" aria-label="Selected hotel and price details">
        <section class="selected-hotel" aria-labelledby="selected-hotel-title">
          <div class="booking-property-image" aria-hidden="true">
            <span>Selected stay</span>
          </div>

          <div class="selected-hotel-copy">
            <p class="section-kicker">Your selected hotel</p>
            <h2 id="selected-hotel-title">{{ hotel.hotel_name }}</h2>
            <p>{{ hotel.city }}, {{ hotel.state }}</p>
            <div class="selected-stay-details">
              <p v-if="checkIn && checkOut">
                {{ checkIn }} – {{ checkOut }}
                <strong v-if="nights">
                  ({{ nights }} {{ nights === 1 ? 'night' : 'nights' }})
                </strong>
              </p>
              <p v-else>Select your stay dates to calculate the trip total.</p>
            </div>
          </div>
        </section>

        <section class="price-details" aria-labelledby="price-details-title">
          <h2 id="price-details-title">Price details</h2>
          <dl>
            <div>
              <dt>Nightly rate</dt>
              <dd>{{ currencyFormatter.format(hotel.nightly_rate_usd) }}</dd>
            </div>
            <div>
              <dt>Length of stay</dt>
              <dd>{{ nights ? `${nights} ${nights === 1 ? 'night' : 'nights'}` : 'Select dates' }}</dd>
            </div>
            <div class="price-total">
              <dt>Estimated total</dt>
              <dd>{{ nights ? currencyFormatter.format(totalCost) : '—' }}</dd>
            </div>
          </dl>
        </section>
      </aside>
    </div>

    <p class="booking-disclaimer">
      Confirming saves the traveler, stay, and booking to the local CSV data.
    </p>
  </section>
</template>
