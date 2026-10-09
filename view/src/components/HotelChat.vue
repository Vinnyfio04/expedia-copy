<script setup>
import { nextTick, ref } from 'vue'

import { ApiError, askHotelQuestion } from '../api.js'
import {
  formatHotelChatDate,
  formatHotelChatMoney,
  hotelChatErrorGuidance,
  hotelChatErrorLabel,
  hotelChatStatusGuidance,
  hotelChatStatusLabel,
  validateHotelQuestion,
} from '../hotelChat.js'


const isOpen = ref(false)
const isLoading = ref(false)
const hasUnreadAnswer = ref(false)
const draft = ref('')
const inputError = ref('')
const messages = ref([])
const conversation = ref(null)
const questionInput = ref(null)
let nextMessageId = 1

async function scrollToLatest() {
  await nextTick()
  if (conversation.value) {
    conversation.value.scrollTop = conversation.value.scrollHeight
  }
}

async function openChat() {
  isOpen.value = true
  hasUnreadAnswer.value = false
  await nextTick()
  questionInput.value?.focus()
  await scrollToLatest()
}

function closeChat() {
  isOpen.value = false
}

function clearInputError() {
  inputError.value = ''
}

function stayLabel(response) {
  if (!response.requested_check_in || !response.requested_check_out) {
    return ''
  }
  return `Check-in ${formatHotelChatDate(response.requested_check_in)} · Checkout ${formatHotelChatDate(response.requested_check_out)} (checkout excluded)`
}

function hotelName(match) {
  return match.name ?? 'Saved hotel name unavailable'
}

function locationLabel(match) {
  return [...new Set([...(match.localities ?? []), ...(match.postcodes ?? [])])].join(' · ')
}

function availabilityLabel(match) {
  if (match.stay_complete === false) {
    return 'Incomplete nightly data'
  }
  if (match.available_for_entire_stay === true) {
    return 'Available for the complete stay'
  }
  if (match.available_for_entire_stay === false) {
    return 'Not available for the complete stay'
  }
  return 'Saved nightly records'
}

function addMessage(
  role,
  text,
  { response = null, isError = false, errorCode = null } = {},
) {
  messages.value.push({
    id: nextMessageId,
    role,
    text,
    response,
    isError,
    errorCode,
  })
  nextMessageId += 1
}

async function submitQuestion() {
  if (isLoading.value) {
    return
  }

  const validation = validateHotelQuestion(draft.value)
  if (validation.error) {
    inputError.value = validation.error
    return
  }

  inputError.value = ''
  addMessage('user', validation.question)
  draft.value = ''
  isLoading.value = true
  await scrollToLatest()

  try {
    const response = await askHotelQuestion(validation.question)
    addMessage('assistant', response.answer, { response })
    if (!isOpen.value) {
      hasUnreadAnswer.value = true
    }
  } catch (error) {
    addMessage(
      'assistant',
      error instanceof ApiError
        ? error.message
        : 'The hotel assistant could not answer right now. Please try again.',
      {
        isError: true,
        errorCode: error instanceof ApiError ? error.code : null,
      },
    )
    if (!isOpen.value) {
      hasUnreadAnswer.value = true
    }
  } finally {
    isLoading.value = false
    await scrollToLatest()
    if (isOpen.value) {
      questionInput.value?.focus()
    }
  }
}
</script>

<template>
  <aside class="hotel-chat-widget" aria-label="Hotel AI assistant">
    <Transition name="hotel-chat-panel">
      <section
        v-if="isOpen"
        id="hotel-chat-panel"
        class="hotel-chat-panel"
        role="dialog"
        aria-modal="false"
        aria-labelledby="hotel-chat-title"
      >
        <header class="hotel-chat-panel-header">
          <span class="hotel-chat-avatar" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M7 8.5h10M7 12h7M5 4.5h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-8l-5 3v-3H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
            </svg>
          </span>
          <div>
            <h2 id="hotel-chat-title">Hotel assistant</h2>
            <p><span aria-hidden="true"></span> Saved-data AI</p>
          </div>
          <button
            type="button"
            class="hotel-chat-close"
            aria-label="Close hotel assistant"
            @click="closeChat"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m7 7 10 10M17 7 7 17" />
            </svg>
          </button>
        </header>

        <div
          ref="conversation"
          class="hotel-chat-conversation"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          <div v-if="messages.length === 0" class="hotel-chat-welcome">
            <span class="hotel-chat-welcome-icon" aria-hidden="true">✦</span>
            <h3>How can I help with your stay?</h3>
            <p>
              Compare hotels you added locally using simulated rates and room
              availability for October 10–14, 2026.
            </p>
            <p class="hotel-chat-read-only">Read-only · No bookings or data changes</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="hotel-chat-message-row"
            :class="`from-${message.role}`"
          >
            <span
              v-if="message.role === 'assistant'"
              class="hotel-chat-message-avatar"
              aria-hidden="true"
            >
              AI
            </span>
            <div
              class="hotel-chat-message"
              :class="{ 'hotel-chat-message-error': message.isError }"
            >
              <p v-if="message.role === 'assistant'" class="hotel-chat-speaker">
                Hotel assistant
              </p>
              <div
                v-if="message.response"
                class="hotel-chat-result-state"
                :class="`status-${message.response.status}`"
              >
                <span class="hotel-chat-state-icon" aria-hidden="true">
                  {{ message.response.status === 'answered' ? '✓' : '!' }}
                </span>
                <div>
                  <strong>{{ hotelChatStatusLabel(message.response.status) }}</strong>
                  <span>{{ hotelChatStatusGuidance(message.response.status) }}</span>
                </div>
              </div>
              <div v-else-if="message.isError" class="hotel-chat-error-state">
                <span class="hotel-chat-state-icon" aria-hidden="true">!</span>
                <div>
                  <strong>{{ hotelChatErrorLabel(message.errorCode) }}</strong>
                  <span>{{ hotelChatErrorGuidance(message.errorCode) }}</span>
                </div>
              </div>
              <p class="hotel-chat-message-copy">{{ message.text }}</p>

              <template v-if="message.response">
                <div
                  v-if="stayLabel(message.response)"
                  class="hotel-chat-response-meta"
                >
                  <span>
                    {{ stayLabel(message.response) }}
                  </span>
                </div>

                <div
                  v-if="message.response.matches.length"
                  class="hotel-chat-match-list"
                >
                  <details
                    v-for="match in message.response.matches"
                    :key="match.hotel_id"
                    class="hotel-chat-match"
                  >
                    <summary>
                      <span>{{ hotelName(match) }}</span>
                      <strong v-if="match.total_cost_cents !== null">
                        {{ formatHotelChatMoney(match.total_cost_cents) }}
                      </strong>
                    </summary>
                    <div class="hotel-chat-match-details">
                      <p v-if="match.address">{{ match.address }}</p>
                      <p v-if="locationLabel(match)">{{ locationLabel(match) }}</p>
                      <p class="hotel-chat-availability">
                        {{ availabilityLabel(match) }}
                      </p>
                      <p v-if="match.distance_meters !== null">
                        {{ Math.round(match.distance_meters).toLocaleString() }} m from saved search center
                      </p>

                      <ul v-if="match.nights.length" class="hotel-chat-night-list">
                        <li v-for="night in match.nights" :key="night.stay_date">
                          <time :datetime="night.stay_date">
                            {{ formatHotelChatDate(night.stay_date) }}
                          </time>
                          <span>{{ formatHotelChatMoney(night.nightly_rate_cents) }}</span>
                          <span>{{ night.rooms_available }} rooms</span>
                        </li>
                      </ul>

                      <p v-if="match.missing_nights.length" class="hotel-chat-missing">
                        Missing nightly data:
                        {{ match.missing_nights.map(formatHotelChatDate).join(', ') }}.
                        This stay is not treated as available.
                      </p>
                    </div>
                  </details>
                </div>

                <p class="hotel-chat-notice">{{ message.response.data_notice }}</p>
              </template>
            </div>
          </article>

          <article v-if="isLoading" class="hotel-chat-message-row from-assistant">
            <span class="hotel-chat-message-avatar" aria-hidden="true">AI</span>
            <div class="hotel-chat-message hotel-chat-typing" role="status">
              <span></span><span></span><span></span>
              <span class="visually-hidden">Searching saved hotel data…</span>
            </div>
          </article>
        </div>

        <form class="hotel-chat-composer" novalidate @submit.prevent="submitQuestion">
          <label class="visually-hidden" for="hotel-chat-question">
            Message hotel assistant
          </label>
          <div class="hotel-chat-input-row">
            <textarea
              id="hotel-chat-question"
              ref="questionInput"
              v-model="draft"
              name="hotel-question"
              rows="1"
              maxlength="1000"
              autocomplete="off"
              placeholder="Type a hotel question…"
              :aria-invalid="Boolean(inputError)"
              :aria-describedby="inputError ? 'hotel-chat-input-error' : undefined"
              @input="clearInputError"
              @keydown.enter.exact.prevent="submitQuestion"
            ></textarea>
            <button type="submit" :disabled="isLoading" aria-label="Send message">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="m4 4 17 8-17 8 3-8-3-8Zm3 8h14" />
              </svg>
            </button>
          </div>
          <p v-if="inputError" id="hotel-chat-input-error" role="alert">
            {{ inputError }}
          </p>
          <small>AI answers use saved local data and may take a moment.</small>
        </form>
      </section>
    </Transition>

    <button
      v-if="!isOpen"
      type="button"
      class="hotel-chat-launcher"
      :class="{ 'has-unread': hasUnreadAnswer }"
      aria-controls="hotel-chat-panel"
      aria-expanded="false"
      @click="openChat"
    >
      <span aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M7 8.5h10M7 12h7M5 4.5h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-8l-5 3v-3H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
        </svg>
      </span>
      <strong>Hotel AI</strong>
      <i v-if="hasUnreadAnswer" aria-label="New assistant response"></i>
    </button>
  </aside>
</template>
