# expedia-copy — Assignment 2 part 1

## Project Access

## Research Notes

 - ### What API?
   - Geoapify
 - ### Useful Interaction Patterns
   - ZIP-code search bar above the map with search button
   - Clear loading message when search is running
   - When the user selects a hotel, the map is centered at the marker with its information listed
   - List hotel cards of resulting hotels
   - Highlight hotel cards when their marker is selected

 - ### Weaknesses / Omissions
   - Has access to place info but nothing about room availability
   - Some data such as names, addresses, and other fields may be missing due to place-data coverage variability
   - Geoapify free plan is 3,000 credits/day
   - Leaflet requires tile provider
     - OpenStreetMap is public intended for low-volume use

   - #### Sources
     - Geoapify Docs: https://apidocs.geoapify.com/docs/places/
     - Geoapify Pricing: https://www.geoapify.com/pricing/
     - OpenTileMap Tile Policy: https://operations.osmfoundation.org/policies/tiles/

 - ### Design Decisions
   - Geoapify converts ZIP code into coordinates
     - Only accept result when it is accurate
   - Search with Geoapify's built in hotel results with a hard coded 5 km circle filter
   - Utilize FastAPI so API key is never exposed
   - Display only information returned by the provider
     - Display honest tags when data is missing
   - Do not display
     - invented prices, ratings, availability, or booking claims
   - Utilize Leaflet with OpenStreetMap tiles

   - #### Sources
     - Geoapify Geocoding: https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/
     - Geoapify Places Filters and Categories: https://apidocs.geoapify.com/docs/places/
     - Leaflet Documentation: https://leafletjs.com/reference.html


## Early Mockup

## Screen-recorded demo video

## Verification Record

## AI Disclosure and Evidence Log
