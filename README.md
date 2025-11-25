# IGS Dashboard – Secure FastAPI + Streamlit Mini-Lab

This project implements a secure FastAPI backend with JWT authentication, loads Mastercard Inclusive Growth Score (IGS) data for 10 California census tracts into a SQLite database, and provides a Streamlit dashboard to visualize the data.

## Features

- Secure FastAPI API with JWT authentication (`/token`, `/tracts/`, `/tracts/{census_tract}`, `/users/me`)
- SQLite database with SQLAlchemy ORM and XSS sanitization via `nh3`
- Streamlit dashboard:
  - Login panel (calls FastAPI)
  - Census tract table
  - Inclusion vs Growth scatter plot
  - Bar chart comparing low- vs high-income tracts
  - Ethics notice and filters
- Unit tests for authentication and endpoints
- Data ethics discussion supported by visualizations

## Requirements

- Python 3.8+
- `pip`
- `git`

## Setup

1. Clone the repository or download the project folder:

   ```bash
   git clone <YOUR_REPO_URL>.git
   cd igs-dashboard
