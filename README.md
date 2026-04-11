# DealHunter 🎮💰
**Course:** [Projecte Web - Enginyeria Informatica 2025/26]  
**Professors:** [Roberto Garcia and David Sarrat]

![Logo](Logos/DealHunter.png)

## 1. Project Information
* **Github Public Address:** https://github.com/DealHunterOrgan/DealHunter.git
* **Team Members & Grade Distribution:**
  * Otto Biel Ródenas - 
  * Sergi Arbós Nicolau - 
  * Marc Verdugo Soria
  * Bruno Verdugo Soria
  * Joel Marcet Cruz
  * Marc Prats

## 2. Application Overview
DealHunter is a basic web application developed using Django to access data regarding the best video game deals. The application features a clean and usable user interface that allows users to browse the catalog, view game details, check prices across different stores, and manage a personalized Wishlist. 

## 3. Design Decisions & Data Model
We have correctly implemented the proposed model with a complex relationship involving more than 3 related entities. 
* **Game:** Stores main game information (title, cover, etc.).
* **Shop:** Stores data from provider stores.
* **Availability:** Intermediate table relating `Game` and `Shop`, storing current and historical prices.
* **Platform & Genre:** Many-to-Many relationships with `Game`.
* **Wishlist:** Intermediate table between the authenticated `User` and `Game`, tracking the user's desired games.

**Design Decisions Notes:**
* **API Integration:** [Explain here how you handled the CheapShark API limitations. E.g., "Since the provided API focuses on pricing, we implemented a custom solution to populate 'Genres' and 'Platforms' to ensure a complete data model satisfying the professors' feedback."]
* **Restricted Actions:** Buying features and Wishlist management require user authentication to enhance security and user flow.

## 4. 12-Factor App Guidelines Adherence
The application has been designed keeping the 12-factor methodology in mind. Here is a breakdown of how we fulfill each point:

* **I. Codebase:** **(Fulfilled)** All code is tracked in a single GitHub repository. There is only one codebase deployed across all environments.
* **II. Dependencies:** **(Fulfilled)** All dependencies are explicitly declared in the `requirements.txt` file and isolated using a Python virtual environment and Docker.
* **III. Config:** **(Fulfilled)** Sensitive configuration (like the `SECRET_KEY` and DB settings) is extracted from the code and stored in a `.env` file, which is strictly ignored in version control (`.gitignore`).
* **IV. Backing Services:** **(Fulfilled)** The local database and external APIs (like CheapShark/Steam) are treated as attached resources. Changing the database only requires a config change, not a code change.
* **V. Build, release, run:** **(Fulfilled)** Docker and `docker-compose` strictly separate the build stage (building the Docker image) from the run stage (spinning up the containers).
* **VI. Processes:** **(Fulfilled)** The Django web application executes as a stateless process. All persistent data (users, games, deals) is stored in a stateful backing service (the database).
* **VII. Port binding:** **(Fulfilled)** The application is completely self-contained and exports HTTP as a service by binding to port `8000`.
* **VIII. Concurrency:** **(Fulfilled)** While our Docker setup allows for scaling out, for the scope of this academic project we are relying on Django's built-in server capabilities. For full compliance, a production WSGI server like Gunicorn would be added.
* **IX. Disposability:** **(Fulfilled)** The stateless nature of the app and the use of Docker containers ensure fast startup times and graceful shutdowns.
* **X. Dev/prod parity:** **(Partially Fulfilled)** Docker ensures the environment remains consistent across machines. However, for simplicity and project requirements, we use SQLite as our main database instead of a heavy production-level DB (like PostgreSQL).
* **XI. Logs:** **(Fulfilled)** The application does not attempt to write or manage logfiles. Instead, Django writes its event streams directly to standard output (`stdout`), which are managed and collected by Docker.
* **XII. Admin processes:** **(Fulfilled)** Administrative tasks, such as database migrations (`python manage.py migrate`) and running the data population script (`python manage.py runscript load_deals`), are executed as one-off processes in an identical environment to the regular long-running processes.

## 5. How to Run and Deploy

### Option A: Local Execution
1. Clone the repository: `git clone git@github.com:DealHunterOrgan/DealHunter.git`
2. Navigate to the directory: `cd DealHunter`
3. Activate the virtual environment:
   * Mac/Linux: `source dhunter/bin/activate` or `source .env/bin/activate
   * Windows: `dhunter\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Apply migrations: `python manage.py migrate`
6. Run the script to load data: `python manage.py runscript load_deals`
7. Start the server: `python manage.py runserver`

### Option B: Docker Deployment
The application includes the required files to run as a docker container orchestration using docker-compose.
1. Ensure Docker and Docker Compose are installed on your system.
2. In the root directory, run: `docker-compose up --build`
3. Access the application at `http://localhost:8000`.
4. To stop the containers, run: `docker-compose down`

## 6. Key Features Checklist
* [x] Implementation of the proposed model.
* [x] Django admin interface activated to add, modify, and delete instances.
* [x] User authentication and registration implemented.
* [x] Included required files for Docker/docker-compose orchestration.
* [x] Web pages displaying and allowing basic navigation (list/detail pages).
* [x] Clean and usable UI.