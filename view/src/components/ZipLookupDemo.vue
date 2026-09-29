<script setup>
import { ref } from 'vue'

import { lookupDemoZip } from '../api.js'


const location = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')

async function lookUpZip() {
  if (isLoading.value) {
    return
  }

  location.value = null
  errorMessage.value = ''
  isLoading.value = true

  try {
    location.value = await lookupDemoZip()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <section class="zip-demo" aria-labelledby="zip-demo-title">
    <div class="zip-demo-copy">
      <p>Location service</p>
      <h2 id="zip-demo-title">ZIP lookup demonstration</h2>
      <p>Resolve the demonstration ZIP through the backend.</p>
    </div>

    <button type="button" :disabled="isLoading" @click="lookUpZip">
      Look up ZIP 16802
    </button>

    <p v-if="isLoading" class="zip-demo-status" role="status" aria-live="polite">
      Looking up ZIP 16802…
    </p>
    <p v-else-if="errorMessage" class="zip-demo-error" role="alert">
      {{ errorMessage }}
    </p>
    <dl v-else-if="location" class="zip-demo-result" aria-live="polite">
      <div>
        <dt>Postcode</dt>
        <dd>{{ location.postcode }}</dd>
      </div>
      <div v-if="location.locality">
        <dt>Locality</dt>
        <dd>{{ location.locality }}</dd>
      </div>
      <div>
        <dt>Latitude</dt>
        <dd>{{ location.latitude }}</dd>
      </div>
      <div>
        <dt>Longitude</dt>
        <dd>{{ location.longitude }}</dd>
      </div>
    </dl>
  </section>
</template>
