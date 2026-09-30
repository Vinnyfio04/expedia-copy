<script setup>
import L from 'leaflet'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'


const OPENSTREETMAP_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const DEFAULT_ZOOM = 13

const props = defineProps({
  center: {
    type: Object,
    required: true,
  },
  hotels: {
    type: Array,
    required: true,
  },
  selectedPlaceId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['select'])
const mapElement = ref(null)

let map = null
const markersByPlaceId = new Map()

function popupContent(hotel) {
  const content = document.createElement('div')
  content.className = 'nearby-map-popup'

  const name = document.createElement('strong')
  name.textContent = hotel.name ?? 'Name unavailable'
  content.append(name)

  if (hotel.formatted_address) {
    const address = document.createElement('span')
    address.textContent = hotel.formatted_address
    content.append(address)
  }

  return content
}

function clearMarkers() {
  for (const marker of markersByPlaceId.values()) {
    marker.remove()
  }
  markersByPlaceId.clear()
}

function applySelection() {
  if (!map) {
    return
  }

  for (const [placeId, marker] of markersByPlaceId) {
    marker.setZIndexOffset(placeId === props.selectedPlaceId ? 1000 : 0)
  }

  if (!props.selectedPlaceId) {
    map.closePopup()
    return
  }

  const marker = markersByPlaceId.get(props.selectedPlaceId)
  if (!marker) {
    return
  }

  map.panTo(marker.getLatLng(), { animate: true })
  marker.openPopup()
  marker.getElement()?.focus({ preventScroll: true })
}

function renderMarkers() {
  if (!map) {
    return
  }

  clearMarkers()

  for (const hotel of props.hotels) {
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      alt: hotel.name ?? 'Hotel location',
      keyboard: true,
      title: hotel.name ?? 'Name unavailable',
    })
      .bindPopup(popupContent(hotel))
      .on('click', () => emit('select', hotel.provider_place_id))
      .addTo(map)

    markersByPlaceId.set(hotel.provider_place_id, marker)
  }

  if (props.hotels.length) {
    const bounds = L.latLngBounds(
      props.hotels.map((hotel) => [hotel.latitude, hotel.longitude]),
    )
    map.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 })
  } else {
    map.setView(
      [props.center.latitude, props.center.longitude],
      DEFAULT_ZOOM,
    )
  }

  applySelection()
}

onMounted(async () => {
  await nextTick()
  map = L.map(mapElement.value).setView(
    [props.center.latitude, props.center.longitude],
    DEFAULT_ZOOM,
  )
  L.tileLayer(OPENSTREETMAP_TILE_URL, {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  renderMarkers()
})

watch(
  [() => props.center, () => props.hotels],
  () => renderMarkers(),
  { deep: true },
)

watch(
  () => props.selectedPlaceId,
  () => applySelection(),
)

onBeforeUnmount(() => {
  clearMarkers()
  map?.remove()
  map = null
})
</script>

<template>
  <div
    ref="mapElement"
    class="nearby-map"
    role="region"
    aria-label="Map of nearby hotel matches"
  ></div>
</template>
