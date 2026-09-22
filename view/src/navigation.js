export function getTopbarTravelAction(currentView) {
  return currentView === 'history' || currentView === 'booking'
    ? { label: 'Stays', view: 'stays' }
    : { label: 'Trips', view: 'history' }
}
