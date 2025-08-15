TimeWise – Study Session Tracker
INM429 Cloud Computing Resit

Overview
TimeWise is a cloud-based productivity app designed to help users manage focused work sessions using the Pomodoro technique, track completed sessions, and view their performance on a leaderboard.

The app integrates multiple cloud services:
- Flask backend deployed on Render (PaaS)
- PostgreSQL database hosted on Render (DBaaS)
- Firebase Authentication for secure login and sign-up (Identity-as-a-Service)

Features
- User Authentication – Sign-up/login via Firebase Auth.
- Pomodoro Timer – 25-minute work + 5-minute break cycle.
- Session Logging – Completed sessions stored in PostgreSQL with timestamp, duration, and user ID.
- Leaderboard – Displays top users based on points from completed sessions.
- Cloud-Hosted – Backend and database run entirely in the cloud, accessible from anywhere.

Tech Stack
Frontend        : HTML, CSS, JavaScript, Bootstrap
Backend         : Python, Flask, SQLAlchemy
Authentication  : Firebase Authentication 
Database        : PostgreSQL (Render)
Deployment      : Render 
Version Control : Git + GitHub

Quick Start Guide
1. Clone the repository:
   git clone https://github.com/vin270/timewise.git 
   cd timewise

2. Create a virtual environment:
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Environment variables:
   DATABASE_URL=postgresql://timewise_bsar_user:1L0AxWh1p3X4mpLcFohrz7iYY74j2vCL@dpg-d29u83mr433s739sobs0-a.oregon-postgres.render.com/timewise_bsar
   FIREBASE_PROJECT_ID=timewise-f6ae9

5. Run the application locally:
   python app.py
   Then open http://127.0.0.1:5000/ in your browser.

How PostgreSQL is Used
- UserModel Table – Stores each user’s Firebase UID, points, nickname, and last seen timestamp.
- Session Table – Stores each completed Pomodoro session’s user ID, timestamp, and duration.
- Leaderboard – Queries sessions and users tables to calculate and display top scores.

Deployment
1. Backend deployed to Render with PostgreSQL add-on.
2. Environment variables configured in Render dashboard.
3. Firebase Authentication set up via Firebase Console.

Known Issues
- None in current build. (Earlier token/timer sync bug has been fixed.)

Future Improvements
- Push notifications when breaks start/end.
- Detailed streak tracking over weeks/months.
- Mobile-friendly UI or native app.
