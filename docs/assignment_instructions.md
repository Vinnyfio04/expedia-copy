Do not reference any assignment materials as you work. Simply use this doc as a check to ensure the project remains functional in the requirements and scope.

1. Objective
Assignment 2 extends the existing hotel application from supplied local records to information obtained through a public API. A traveler enters a U.S. ZIP code, explores nearby hotels in a synchronized list and map, and saves selected places to a persistent shortlist.

The objective is to integrate an external data source while preserving clear Model–View–Controller responsibilities, honest interface behavior, and repeatable verification. Students continue their Vue, FastAPI, and SQLite project. No Figma work, deployment, payment processing, or actual booking is required.

2. Scope
Research and Early Mockups for Both Parts
Before implementation of each part, students investigate relevant existing applications and API or library documentation. The research notes identify useful interaction patterns, weaknesses or omissions, and decisions adopted for the application, with links to the sources. Each part includes an early mockup showing its intended interaction and relevant states. A sketch or annotated image is sufficient; no specific design tool is required. Part 2 may build on the earlier research and mockup, with the additions or revisions for the shortlist clearly identified.

Part 1 — Live Hotel Search and Map
The application accepts a five-digit U.S. ZIP code, including leading zeros. FastAPI uses Geoapify to resolve it to a U.S. postcode location and obtain hotels within 5 km of the returned point. The search center is that returned location, not the traveler’s position or every address within the ZIP area. A lookup that does not establish the requested U.S. ZIP code must not silently become a different-location search.

Vue presents the returned hotels as a list and on a Leaflet map. Selecting a hotel in either representation identifies the same hotel in the other. The layout and interaction design remain the student’s choices. Available names, locations, and coordinates must correspond to the response; missing fields require an honest label or omission. No invented prices, ratings, room availability, or booking confirmations are permitted.

The interface distinguishes loading, results, invalid input, an unresolved ZIP code, no nearby results, and a failed request. It must not describe a service failure as an empty successful search. Geoapify geocoding and Places requests pass through FastAPI. Store API keys and credentials in a local .env file and add .env to .gitignore; the file must not be tracked or committed to version control. Leaflet displays map imagery from a tile provider. Any browser-visible tile credential must be intended for client use and appropriately restricted; the backend geocoding and Places key must not be copied into frontend configuration.

Part 2 — Persistent Shortlist and Verification
The application can save a returned hotel, display the saved shortlist, and remove a saved hotel. SQLite preserves that state after both browser and backend restarts. Saving the same provider place identifier again must not create duplicate shortlist entries. The saved information remains recognizable when a later live response changes or becomes unavailable. External places need a documented data structure that accommodates their provider identifiers and coordinates without inventing the nightly rate required by the original sample Hotel model.

The project’s AGENTS.md records the MVC responsibilities and verification loop. Before adding a dependency, the agent must CHECK the existing environment, TAKE ACTION only after explaining the exact proposed installation and receiving the student’s approval, and VERIFY the result. Existing working behavior should be preserved.

Provider Information and Limits
Geoapify GeocodingLinks to an external site. documents postcode lookup and country filtering; the Places APILinks to an external site. documents categories and geographic filters. These services provide location data, not proof of bookable rooms. Coverage and available fields vary; students must document result limits and avoid claiming an exhaustive hotel inventory. Map attribution must remain visible. The Leaflet documentationLinks to an external site. and Geoapify pricing and usage termsLinks to an external site. guide implementation and responsible request volume. No paid plan is required by this brief.

3. Subproblems and Points
The two parts are separate graded submissions, each worth 100 raw points. Together they total 200 raw points within the Assignment 2 group, which contributes 15% of the course grade. Each part therefore contributes 7.5% of the course grade.

Assignment 2 submissions, deadlines, and points
Submission	Required outcome	Due, Eastern Time	Points
Part 1 — Live Hotel Search and Map	Research, early mockup, live hotel search and connected map, and recorded demonstration	Tuesday, September 29, 2026, 11:59 PM	100
Part 2 — Persistent Shortlist and Verification	Research, early mockup, persistent shortlist and verification, and recorded demonstration	Tuesday, October 6, 2026, 11:59 PM	100
Part 1 is submitted by September 29. Part 2 extends the same project and is submitted by October 6.

4. Evaluation Criteria
Research and design: Decisions are supported by research and the early mockup; changes made during implementation are explained.
Part 1 functionality: ZIP lookup returns the intended location, hotel results match the API response, list and map selections stay synchronized, and input or request problems receive clear feedback.
Part 2 functionality: The shortlist supports saving and removal, prevents duplicates, and survives browser and backend restarts.
Implementation quality: MVC responsibilities are clear, data is presented accurately, credentials are protected, and search and shortlist controls work with a keyboard.
Verification: Claims are supported by expected-versus-observed results. Both parts include a live demonstration. Part 2 also uses a labeled fixed JSON sample for repeatable checks and SQLite evidence for persistence. Checks cover duplicate saves, removal, restarts, and simulated empty results, API failures, and quota or rate-limit responses without exhausting the service. They must not depend on a fixed live result count.
5. Submission
Part 1 — Submission: Due Tuesday, September 29, 2026, at 11:59 PM ET.
Part 2 — Submission: Due Tuesday, October 6, 2026, at 11:59 PM ET.
For each part, upload one report.md containing:

Project access: Repository link, assessed commit, and startup and configuration instructions.
Research notes: Sources consulted, useful and problematic features observed, and the resulting design decisions.
Early mockup: An image or link to the design prepared before implementation, with a brief explanation of subsequent changes.
Screen-recorded demo video: A link showing the running application and the required behavior of the submitted part.
Verification record: Inputs or actions, expected results, observed results, and corrections or remaining limitations. Identify the tested ZIP and observation date for live searches; for Part 2, link the fixed JSON sample and give instructions for repeating its checks.
AI disclosure and evidence log: Identify each tool, specific model, and its use. Include selected prompt excerpts linked to code changes, verification, and decisions, including at least one failed or revised approach. A full chat export is not required.
All linked artifacts must be accessible to the instructor without an additional access request. Remove credentials and private information from the report, recordings, and evidence. The AI disclosure and evidence log are required under the syllabus policy and do not carry separate points.
