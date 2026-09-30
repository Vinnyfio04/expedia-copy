# Expedia-copy — Assignment 2 part 1

## Project Access
- ### Repository Link
  - https://github.com/Vinnyfio04/expedia-copy.git
- ### Assessed Commit
  - 
- ### Startup / Configuration Instructions
  - #### Prerequisites
    - Install the following:
      - [Git](https://git-scm.com/downloads)
      - Python 3.11 or newer (Python 3.12 is recommended)
      - Node.js 22.12 or newer (npm is included with Node.js)
  - #### Download the repository
    - Open PowerShell and run:

      ```powershell
      git clone https://github.com/Vinnyfio04/expedia-copy.git
      cd expedia-copy
      ```

    - Alternatively, download the repository as a ZIP file, extract it, and open PowerShell in the extracted folder.
  - #### Configure Geoapify (optional)
    - The Geoapify API key is required only for the ZIP lookup demonstration. Hotel search, booking, and booking history work without it.
    - To enable ZIP lookup:
      - Create a free API key at [Geoapify MyProjects](https://myprojects.geoapify.com/).
      - Create a file named `.env` in the project root.
      - Add your API key:

        ```env
        GEOAPIFY_API_KEY=replace_with_your_key
        ```

      - Do not commit the `.env` file.
  - #### Start the backend
    - From the project root, run:

      ```powershell
      cd controller
      py -3 -m venv .venv
      .\.venv\Scripts\python.exe -m pip install -r requirements.txt
      .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
      ```

    - Keep this terminal open.
    - The backend will be available at:
      - API: [http://localhost:8000](http://localhost:8000)
      - Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
      - API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
    - On its first startup, the backend creates and seeds `model/expedia.db`. Later restarts preserve database changes instead of reseeding it.
  - #### Start the frontend
    - Open a second PowerShell terminal in the project root and run:

      ```powershell
      cd view
      npm ci
      npm run dev
      ```

    - Keep this terminal open.
    - Open the URL displayed by Vite, usually [http://localhost:5173](http://localhost:5173).
  - #### Stop the application
    - Press `Ctrl+C` in each terminal to stop the frontend and backend servers.

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
- ### Searching ZIP Code
  - <u>**Input:**</u>
  - <u>**Expected:**</u>
  - <u>**Corrections:**</u>
  - <u>**Tested ZIP and Observation Date:**</u>
- ### Searching Incorrect ZIP Code
  - <u>**Input:**</u>
  - <u>**Expected:**</u>
  - <u>**Corrections:**</u>
  - <u>**Tested ZIP and Observation Date:**</u>
- ### Selecting Hotel Card
  - <u>**Input:**</u>
  - <u>**Expected:**</u>
  - <u>**Corrections:**</u>
  - <u>**Tested ZIP and Observation Date:**</u>
- ### Selecting Map Marker
  - <u>**Input:**</u>
  - <u>**Expected:**</u>
  - <u>**Corrections:**</u>
  - <u>**Tested ZIP and Observation Date:**</u>

## AI Disclosure and Evidence Log
- ### Tools Used
  - Codex
    - GPT5.6-Sol High
    - #### Its use
      - Used codex for full agentic development. Used standard ChatGPT chat function to verify prompts and outputs to ensure requirements were met with each step.
    - #### Prompt Exerpts
      - Code Changes
        - g
      - Verification
        - "Write a summary of all the changes made in this branch with a short explanation for each file. (File name - what was changed specifically). Report significant prompts in the /prompts folder. Make sure the appropriate docs are updated with the implemented MVC structure and the general folder structure."
      - Decisions
        - "Thoroughly read handoffs/currend.md before taking any further action to fully understand this next step. Verify requirements in the /docs folder as well as README and AGENTS to ensure the next course of action follows what is stated. We are going to be implementing the zip code search and map implementation. Analyze the zip-search-mockup jpeg in images/. This is what the general layout of this feature will look. It will be located where ZIP lookup demonstration is located in the project as of now. It will be replacing the ZIP lookup. We will follow a clear pipeline to efficiently implement this feature with quality. Ensure to not over-engineer the process. The feature must align with the following workflow: User submits a ZIP code -> Vue validates the input -> the frontend sends the ZIP code to FastAPI -> FastAPI finds the ZIP code’s coordinates -> FastAPI requests hotels within 5 km -> the hotel data is returned to Vue -> Vue displays the hotels in a list and as markers on the Leaflet map -> selecting a hotel updates both the list and map. Generate a plan to follow these requirements. Do not change any files, I will give my go-ahead when I have reviewed it. The first step should be installing dependencies for the required tools for this feature. Ask questions to clarify ambiguity before planning if any appears."
      - Revised Approach
        - g
