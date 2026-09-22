# expedia-copy — Part 1

## Repository and commit

Repository: [github.com/Vinnyfio04/expedia-copy](https://github.com/Vinnyfio04/expedia-copy)

Part 1 implementation checkpoint: [`9227f0548bab06e6edc6e9ea814f8a3bedb3d00e`](https://github.com/Vinnyfio04/expedia-copy/commit/9227f0548bab06e6edc6e9ea814f8a3bedb3d00e)

Commit message: `Added basic working expedia...`

Documentation commit: `88c7b96b8627bf1d603bf5915181e2c951ca9178`

## Implementation

In part 1, we had the general project framework set up along with a basic implementation of the application. The user could search hotels but they could not schedule any kind of trip. Since then, we implemented the bookings tab so the user can now select the hotel and plan a trip with the appropriate information.

## Verification

- **Initial page load**
  - Action: Starting both the server and front end and inputting the URL
  - Expected: The stays page loads and the hotels listed below showing the total number of hotels available.
  - Observed: The stays page loaded with confirmation of "8 hotels found."

- **Switching from stays to bookings tab**
  - Action: Scrolling from the top and clicking "Trips" to enter the page
  - Expected: The trips page gets loaded with all of the trips on the SQLite file.
  - Observed: The trips page loaded and the list of bookings is visible. Confirmation of 10 bookings is listed on the site.

- **Successful search**
  - Action: Go to the stays tab and search up "Metro" to get Metro Garden Hotel.
  - Expected: Metro Garden Hotel shows up.
  - Observed: Metro Garden Hotel shows up with confirmation of "1 hotel found."

- **Booking a trip**
  - Action: Select Metro Garden Hotel, input any date and the appropriate information, select confirm and see the confirmation message. Then go into trips to find the booking there.
  - Expected: Hitting confirm sends the confirmation message and the trip is located under the trips tab.
  - Observed: The scheduling page is loaded with the appropriate hotel information. When the proper information is entered and confirmed, a little message confirming the success appears. When switching to the booking history tab, I can see the trip I had just made.

- **Canceling a trip**
  - Action: In the bookings tab, go down to the trip I just made and cancel it.
  - Expected: The trip gets cancelled but remains in the list and the proper .csv file is updated.
  - Observed: After the cancel button is hit, the booking is grayed out and the cancel button says Cancelled. Confirmation of the cancellation is present.

## Verification screenshots

- Initial stays page: [initial page test](images/08-initial-page-test.jpg)
- Hotel-name search: [hotel search test](images/07-hotel-search-test.jpg)
- Booking creation: [booking test](images/05-booking-test.jpg)
- Trips and booking history: [trips page test](images/09-trips-page-test.jpg)
- Persistent cancellation: [cancellation test](images/06-cancellation-test.jpg)

## Project context and next steps

- [README.md](https://github.com/Vinnyfio04/expedia-copy/blob/main/README.md)
- [AGENTS.md](https://github.com/Vinnyfio04/expedia-copy/blob/main/AGENTS.md)
- [Design and request pipeline](https://github.com/Vinnyfio04/expedia-copy/blob/main/docs/design-pipeline.md)
- [Selected project prompts](https://github.com/Vinnyfio04/expedia-copy/tree/main/prompts)
- [Current handoff](https://github.com/Vinnyfio04/expedia-copy/blob/main/handoffs/current.md)
- [Assignment instructions](https://github.com/Vinnyfio04/expedia-copy/blob/main/docs/assignment_instructions.md)

The design note, selected prompts, current handoff, and this report were added in
documentation commit `88c7b96b8627bf1d603bf5915181e2c951ca9178`.
That commit is currently local and must be pushed before its GitHub links will be
accessible to the instructor.

Current limitation: There is no account system implemented.

The next task would be to create account creation and management if we were to continue this further.

## Demo Video
