🛢️ ORM-Drilling-Application—OGDCL
This project is a full-stack web application for OGDCL (Oil & Gas Development Company Limited) designed to manage, update, and present data related to oil well operations in Pakistan.

<img width="1323" height="481" alt="image" src="https://github.com/user-attachments/assets/36299a6d-e223-4f0d-8bb8-cc16bd301c7c" />

🧩 Components
🌐 Frontend (React)
Developed in client/ directory

Communicates with Flask backend via REST API

Key Features:

Dynamic forms for well updates

Tables & cards to present drilling data

Clean, responsive UI for field engineers or analysts

⚙️ Backend (Flask)
Developed in server/ or backend/ directory

Manages API routes such as:

GET /drilling-operations – retrieve drilling data

PUT /drilling-operations/:id – update well info

Handles connection to MS SQL Server using pyodbc or SQLAlchemy

🗄️ Database (Microsoft SQL Server)
Stores:

Well IDs

Spud dates

Depth data

Test durations

Actual vs. planned timelines

Tables include:

DrillingOperation

ActualRigDays

Block

etc.

🧪 Use Cases
OGDCL engineers can update drilling timelines after field operations.

Managers can view performance deviations between planned and actual rig days.

Provides a structured interface for real-time drilling operation monitoring.

📌 Coming Soon / Future Work
Authentication (admin vs. viewer roles)

Graphs and analytics dashboard

Export to Excel/PDF feature

