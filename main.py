from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pyodbc
import matplotlib.pyplot as plt
from datetime import datetime
from functools import lru_cache
import time



from fastapi import FastAPI, HTTPException, Request, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pyodbc
import matplotlib.pyplot as plt
from datetime import datetime
from functools import lru_cache
import time
import smtplib
from email.message import EmailMessage
import os
import logging


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection settings
server = r'Liverpool\SQLEXPRESS'
database = 'ORM DRILLING OPERATIONS'
driver = '{ODBC Driver 17 for SQL Server}'

# Connection pool for better performance
_connection_pool = []



def get_db_connection():
    if _connection_pool:
        try:
            conn = _connection_pool.pop()
            # Test if connection is still alive
            conn.cursor().execute("SELECT 1")
            return conn
        except:
            pass

    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    )
    return conn


def return_connection(conn):
    try:
        if len(_connection_pool) < 5:  # Limit pool size
            _connection_pool.append(conn)
        else:
            conn.close()
    except:
        conn.close()


@app.get("/")
def read_root():
    return {"message": "Drilling backend is running!"}


# ... existing code ...
from fastapi import UploadFile, Form, HTTPException
import smtplib
from email.message import EmailMessage
import os
import logging

# Set up logging to see detailed errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ... existing code ...

@app.post("/send-drilling-report")
async def send_drilling_report(
        pdf: UploadFile,
        to: str = Form(...),
        subject: str = Form(...),
        body: str = Form(...)
):
    try:
        # Validate PDF file
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # Read PDF file content
        pdf_bytes = await pdf.read()

        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")

        logger.info(f"PDF file size: {len(pdf_bytes)} bytes")

        # Validate email address format (basic validation)
        if '@' not in to or '.' not in to:
            raise HTTPException(status_code=400, detail="Invalid email address format")

        # Compose email
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = "zakinabeel522@gmail.com"
        msg["To"] = to
        msg.set_content(body)

        # Attach PDF with proper content type
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf.filename or "drilling_report.pdf"
        )

        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "zakinabeel522@gmail.com"
        smtp_pass = "ytdu babt xwte gqas"  # Consider using environment variables

        logger.info(f"Attempting to send email to: {to}")

        # Send via Gmail SMTP with better error handling
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug output
            logger.info("Starting TLS...")
            server.starttls()

            logger.info("Logging in...")
            server.login(smtp_user, smtp_pass)

            logger.info("Sending message...")
            server.send_message(msg)

        logger.info("Email sent successfully!")
        return {"message": "Email sent successfully!"}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        raise HTTPException(status_code=500, detail="Email authentication failed. Check credentials.")

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipients refused: {e}")
        raise HTTPException(status_code=400, detail="Invalid recipient email address")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# ... existing code ...


# Cache drilling operations for 30 seconds
@lru_cache(maxsize=1)
def get_cached_drilling_operations():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                do.DrillingOperationID,
                do.SrNo,
                r.RigNo,
                w.WellName,
                w.WellID,
                b.BlockName,
                w.Latitude,
                w.Longitude,
                do.SpudDate,
                do.PresentDepthM,
                do.TDM,
                ap.DrlgDays,
                ap.TestDays,
                do.MDrld,
                do.WeeklyM,
                ar.DryDays,
                ar.TestWODays,
                do.OperationLog,
                do.StopCard,
                do.LastUpdated
            FROM DrillingOperation do
            JOIN Rig r ON do.RigID = r.RigID
            JOIN Well w ON do.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON do.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON do.ActualRigDaysID = ar.ActualRigDaysID
            ORDER BY do.SrNo
        """)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        return_connection(conn)


@app.get("/drilling-operations")
def get_drilling_operations():
    # Clear cache every 30 seconds to get fresh data
    current_time = int(time.time() / 30)
    get_cached_drilling_operations.cache_clear()
    return get_cached_drilling_operations()

@app.get("/fiscal-year-plans")
def get_fiscal_year_plans(wellId: int = None, fy: str = "2025-26"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if wellId is not None:
            cursor.execute("""
                SELECT FiscalYearPlanID, FY, QTR, WellName, WellDepth, PlanDetails, WellID
                FROM FiscalYearPlan
                WHERE FY = ? AND WellID = ?
                ORDER BY 
                    CASE QTR 
                        WHEN '1st QTR' THEN 1
                        WHEN '2nd QTR' THEN 2
                        WHEN '3rd QTR' THEN 3
                        WHEN '4th QTR' THEN 4
                    END
            """, fy, wellId)
        else:
            return []
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        return_connection(conn)


@app.get("/fiscal-year-plans-by-well")
def get_fiscal_year_plans_by_well(wellName: str, fy: str = "2025-26"):
    """Get fiscal year plans by well name - useful for debugging"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First get the WellID for the given well name
        cursor.execute("SELECT WellID FROM Well WHERE WellName = ?", wellName)
        well_result = cursor.fetchone()

        if well_result:
            well_id = well_result[0]
            cursor.execute("""
                SELECT FiscalYearPlanID, FY, QTR, WellName, WellDepth, PlanDetails, WellID
                FROM FiscalYearPlan
                WHERE FY = ? AND WellID = ?
                ORDER BY 
                    CASE QTR 
                        WHEN '1st QTR' THEN 1
                        WHEN '2nd QTR' THEN 2
                        WHEN '3rd QTR' THEN 3
                        WHEN '4th QTR' THEN 4
                    END
            """, fy, well_id)
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {"wellId": well_id, "wellName": wellName, "plans": results}
        else:
            return {"wellId": None, "wellName": wellName, "plans": [], "error": "Well not found"}
    except Exception as e:
        print(f"Error in get_fiscal_year_plans_by_well: {e}")
        return {"wellId": None, "wellName": wellName, "plans": [], "error": str(e)}
    finally:
        return_connection(conn)



from fastapi import Body

# ... existing code ...
from fastapi import Body, HTTPException
import json


@app.post("/add-fiscal-year-plan")
def add_fiscal_year_plan(plan: dict = Body(...)):
    # Debug logging
    print(f"Received plan data: {json.dumps(plan, indent=2)}")

    required_fields = ["FY", "QTR"]
    for field in required_fields:
        if field not in plan or not plan[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Debug: Check initial WellName and WellID
        print(f"Initial WellName: {plan.get('WellName')}, WellID: {plan.get('WellID')}")

        # Auto-fill WellName or WellID if missing
        if not plan.get("WellName") and plan.get("WellID"):
            print(f"Looking up WellName for WellID: {plan['WellID']}")
            cursor.execute("SELECT WellName FROM Well WHERE WellID = ?", plan["WellID"])
            result = cursor.fetchone()
            if result:
                plan["WellName"] = result[0]
                print(f"Found WellName: {plan['WellName']}")
            else:
                print(f"No well found for WellID: {plan['WellID']}")

        if not plan.get("WellID") and plan.get("WellName"):
            print(f"Looking up WellID for WellName: {plan['WellName']}")
            cursor.execute("SELECT WellID FROM Well WHERE WellName = ?", plan["WellName"])
            result = cursor.fetchone()
            if result:
                plan["WellID"] = result[0]
                print(f"Found WellID: {plan['WellID']}")
            else:
                print(f"No well found for WellName: {plan['WellName']}")

        # Debug: Check final WellName and WellID
        print(f"Final WellName: {plan.get('WellName')}, WellID: {plan.get('WellID')}")

        # Now require both
        if not plan.get("WellName") or not plan.get("WellID"):
            error_msg = f"WellName and WellID are required and could not be auto-filled. WellName: {plan.get('WellName')}, WellID: {plan.get('WellID')}"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Debug: Show what will be inserted
        insert_data = (
            plan["FY"],
            plan["QTR"],
            plan["WellName"],
            plan.get("WellDepth"),
            plan.get("PlanDetails"),
            plan["WellID"]
        )
        print(f"Inserting data: {insert_data}")

        cursor.execute(
            """
              INSERT INTO FiscalYearPlan (FY, QTR, WellName, WellDepth, PlanDetails, WellID)
              OUTPUT INSERTED.FiscalYearPlanID, INSERTED.FY, INSERTED.QTR, INSERTED.WellName, INSERTED.WellDepth, INSERTED.PlanDetails, INSERTED.WellID
              VALUES (?, ?, ?, ?, ?, ?)
              """,
            insert_data
        )
        inserted = cursor.fetchone()
        conn.commit()

        if inserted:
            columns = [column[0] for column in cursor.description]
            result = dict(zip(columns, inserted))
            print(f"Successfully inserted: {result}")
            return result
        else:
            print("Insert failed - no data returned")
            raise HTTPException(status_code=500, detail="Insert failed")

    except Exception as e:
        conn.rollback()
        print(f"Error inserting fiscal year plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        return_connection(conn)
# ... existing code ...


@app.get("/debug/wells")
def debug_wells():
    """Debug endpoint to check WellID values"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT w.WellID, w.WellName, do.DrillingOperationID
            FROM Well w
            LEFT JOIN DrillingOperation do ON w.WellID = do.WellID
            ORDER BY w.WellName
        """)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"wells": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        return_connection(conn)


@app.put("/drilling-operations/{operation_id}")
async def update_drilling_operation(operation_id: int, request: Request):
    data = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Fetch current row (old state) - Updated to handle GeneralNotes properly
        cursor.execute("""
            SELECT SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID, 
                   MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, 
                   LastUpdated, FiscalYearPlanID, GeneralNotes
            FROM DrillingOperation
            WHERE DrillingOperationID = ?
        """, (operation_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Drilling operation not found")

        # 2. Insert old state into history
        cursor.execute("""
            INSERT INTO DrillingOperationHistory (
                DrillingOperationID, SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID,
                MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated, 
                FiscalYearPlanID, GeneralNotes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation_id,
            current[0], current[1], current[2], current[3], current[4], current[5], current[6],
            current[7], current[8], current[9], current[10], current[11], current[12],
            current[13], current[14]  # GeneralNotes
        ))

        # 3. Update related AFEPlan table if needed
        afe_plan_id = current[6]
        if afe_plan_id and ("DrlgDays" in data or "TestDays" in data):
            cursor.execute("""
                UPDATE AFEPlan
                SET DrlgDays = ?, TestDays = ?
                WHERE AFEPlanID = ?
            """, (
                data.get("DrlgDays"),
                data.get("TestDays"),
                afe_plan_id
            ))

        # 4. Update related ActualRigDays table if needed
        actual_rig_days_id = current[9]
        if actual_rig_days_id and ("DryDays" in data or "TestWODays" in data):
            cursor.execute("""
                UPDATE ActualRigDays
                SET DryDays = ?, TestWODays = ?
                WHERE ActualRigDaysID = ?
            """, (
                data.get("DryDays"),
                data.get("TestWODays"),
                actual_rig_days_id
            ))

        # 5. Update the DrillingOperation table (with new data)
        cursor.execute("""
            UPDATE DrillingOperation
            SET
                SrNo = ?,
                PresentDepthM = ?,
                TDM = ?,
                MDrld = ?,
                WeeklyM = ?,
                OperationLog = ?,
                StopCard = ?,
                GeneralNotes = ?,
                LastUpdated = ?
            WHERE DrillingOperationID = ?
        """, (
            data.get("SrNo", current[0]),
            data.get("PresentDepthM", current[4]),
            data.get("TDM", current[5]),
            data.get("MDrld", current[7]),
            data.get("WeeklyM", current[8]),
            data.get("OperationLog", current[10]),
            data.get("StopCard", current[11]),
            data.get("GeneralNotes", current[14] if len(current) > 14 else None),
            # Handle missing GeneralNotes gracefully
            datetime.now(),
            operation_id
        ))

        conn.commit()
        return {"message": "Updated successfully"}

    except Exception as e:
        print("UPDATE ERROR:", e)
        conn.rollback()
        # More detailed error logging
        import traceback
        print("Full traceback:", traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

@app.put("/fiscal-year-plans/{plan_id}")
async def update_fiscal_year_plan(plan_id: int, request: Request):
    data = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE FiscalYearPlan
            SET WellDepth = ?, PlanDetails = ?
            WHERE FiscalYearPlanID = ?
        """, (data["WellDepth"], data["PlanDetails"], plan_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return {"message": "Fiscal year plan updated successfully"}


@app.get("/well-depths-plot")
def well_depths_plot():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT w.WellName, do.PresentDepthM
            FROM DrillingOperation do
            JOIN Well w ON do.WellID = w.WellID
        """)
        data = cursor.fetchall()
        wells = [row[0] for row in data]
        depths = [row[1] for row in data]

        plt.figure(figsize=(8, 4))
        plt.bar(wells, depths, color='#1976d2')
        plt.xlabel('Well')
        plt.ylabel('Present Depth (m)')
        plt.title('Present Depth by Well')
        plt.tight_layout()
        img_path = 'well_depths.png'
        plt.savefig(img_path)
        plt.close()
        return FileResponse(img_path, media_type='image/png')
    finally:
        return_connection(conn)


@app.get("/drilling-operations/{operation_id}/history")
def get_drilling_operation_history(operation_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM DrillingOperationHistory
            WHERE DrillingOperationID = ?
            ORDER BY HistoryTimestamp DESC
        """, (operation_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()



from fastapi import Body

@app.get("/drilling-operations/{operation_id}/history")
def get_drilling_operation_history(operation_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM DrillingOperationHistory
            WHERE DrillingOperationID = ?
            ORDER BY HistoryTimestamp DESC
        """, (operation_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()

@app.post("/drilling-operations")
async def add_drilling_operation(data: dict = Body(...)):
    """
    Add a new well and drilling operation.
    Expects: WellName, RigName, BlockName, Longitude, Latitude, SpudDate, TargetDepth, PlannedAFEDaysDrilling, PlannedAFEDaysActual
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Ensure Block exists or create it
        cursor.execute("SELECT BlockID FROM Block WHERE BlockName = ?", data["BlockName"])
        block = cursor.fetchone()
        if block:
            block_id = block[0]
        else:
            cursor.execute("INSERT INTO Block (BlockName) OUTPUT INSERTED.BlockID VALUES (?)", data["BlockName"])
            block_id = cursor.fetchone()[0]

        # 2. Ensure Well exists or create it
        cursor.execute("SELECT WellID FROM Well WHERE WellName = ?", data["WellName"])
        well = cursor.fetchone()
        if well:
            well_id = well[0]
        else:
            cursor.execute("INSERT INTO Well (WellName, BlockID, Latitude, Longitude) OUTPUT INSERTED.WellID VALUES (?, ?, ?, ?)",
                         (data["WellName"], block_id, data.get("Latitude"), data.get("Longitude")))
            well_id = cursor.fetchone()[0]

        # 3. Ensure Rig exists or create it
        cursor.execute("SELECT RigID FROM Rig WHERE RigNo = ?", data["RigName"])
        rig = cursor.fetchone()
        if rig:
            rig_id = rig[0]
        else:
            cursor.execute("INSERT INTO Rig (RigNo) OUTPUT INSERTED.RigID VALUES (?)", data["RigName"])
            rig_id = cursor.fetchone()[0]

        # 4. Create AFE Plan
        afe_plan_id = None
        if data.get("PlannedAFEDaysDrilling") or data.get("PlannedAFEDaysActual"):
            cursor.execute("""
                INSERT INTO AFEPlan (DrlgDays, TestDays) 
                OUTPUT INSERTED.AFEPlanID 
                VALUES (?, ?)
            """, (data.get("PlannedAFEDaysDrilling"), data.get("PlannedAFEDaysActual")))
            afe_plan_id = cursor.fetchone()[0]

        # 5. Create Actual Rig Days (initially empty)
        actual_rig_days_id = None
        cursor.execute("""
            INSERT INTO ActualRigDays (DryDays, TestWODays) 
            OUTPUT INSERTED.ActualRigDaysID 
            VALUES (NULL, NULL)
        """)
        actual_rig_days_id = cursor.fetchone()[0]

        # 6. Get next SrNo
        cursor.execute("SELECT ISNULL(MAX(SrNo), 0) + 1 FROM DrillingOperation")
        next_sr_no = cursor.fetchone()[0]

        # 7. Insert DrillingOperation
        cursor.execute("""
            INSERT INTO DrillingOperation (
                SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID, 
                MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated
            )
            OUTPUT INSERTED.DrillingOperationID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            next_sr_no,
            rig_id,
            well_id,
            data.get("SpudDate"),
            data.get("PresentDepthM", 0),
            data.get("TargetDepth"),
            afe_plan_id,
            data.get("PlannedAFEDaysDrilling"),
            data.get("PlannedAFEDaysActual"),
            actual_rig_days_id,
            "Well under Drilling. Initial setup completed.",  # Default operation log
            0,  # Default stop card
            datetime.now()
        ))
        drilling_operation_id = cursor.fetchone()[0]

        conn.commit()
        return {"success": True, "DrillingOperationID": drilling_operation_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@app.delete("/drilling-operations/{drilling_operation_id}")
async def delete_drilling_operation(drilling_operation_id: int):
    """
    Delete a drilling operation and store it in PastWell table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First, get the complete drilling operation data
        cursor.execute("""
            SELECT 
                do.DrillingOperationID, do.SrNo, do.RigID, do.WellID, do.SpudDate, 
                do.PresentDepthM, do.TDM, do.AFEPlanID, do.MDrld, do.WeeklyM, 
                do.ActualRigDaysID, do.OperationLog, do.StopCard, do.LastUpdated,
                do.FiscalYearPlanID, do.GeneralNotes,
                r.RigNo, w.WellName, b.BlockName, w.Latitude, w.Longitude,
                ap.DrlgDays, ap.TestDays, ar.DryDays, ar.TestWODays
            FROM DrillingOperation do
            JOIN Rig r ON do.RigID = r.RigID
            JOIN Well w ON do.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON do.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON do.ActualRigDaysID = ar.ActualRigDaysID
            WHERE do.DrillingOperationID = ?
        """, (drilling_operation_id,))

        operation_data = cursor.fetchone()
        if not operation_data:
            raise HTTPException(status_code=404, detail="Drilling operation not found")

        # Create PastWell table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PastWell]') AND type in (N'U'))
            BEGIN
                CREATE TABLE PastWell (
                    PastWellID INT PRIMARY KEY IDENTITY,
                    OriginalDrillingOperationID INT,
                    SrNo INT,
                    RigID INT,
                    WellID INT,
                    SpudDate DATE,
                    PresentDepthM INT,
                    TDM INT,
                    AFEPlanID INT,
                    MDrld VARCHAR(20),
                    WeeklyM VARCHAR(20),
                    ActualRigDaysID INT,
                    OperationLog NVARCHAR(MAX),
                    StopCard INT,
                    LastUpdated DATETIME,
                    FiscalYearPlanID INT,
                    GeneralNotes NVARCHAR(MAX),
                    RigNo VARCHAR(20),
                    WellName VARCHAR(50),
                    BlockName VARCHAR(50),
                    Latitude FLOAT,
                    Longitude FLOAT,
                    DrlgDays INT,
                    TestDays INT,
                    DryDays INT,
                    TestWODays INT,
                    DeletedAt DATETIME DEFAULT GETDATE()
                )
            END
        """)

        # Insert into PastWell table
        cursor.execute("""
            INSERT INTO PastWell (
                OriginalDrillingOperationID, SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM,
                AFEPlanID, MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated,
                FiscalYearPlanID, GeneralNotes, RigNo, WellName, BlockName, Latitude, Longitude,
                DrlgDays, TestDays, DryDays, TestWODays
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation_data[0], operation_data[1], operation_data[2], operation_data[3], operation_data[4],
            operation_data[5], operation_data[6], operation_data[7], operation_data[8], operation_data[9],
            operation_data[10], operation_data[11], operation_data[12], operation_data[13], operation_data[14],
            operation_data[15], operation_data[16], operation_data[17], operation_data[18], operation_data[19],
            operation_data[20], operation_data[21], operation_data[22], operation_data[23], operation_data[24]
        ))

        # Now delete the DrillingOperation
        cursor.execute("DELETE FROM DrillingOperation WHERE DrillingOperationID = ?", drilling_operation_id)

        conn.commit()
        return {"success": True, "message": "Well moved to past wells"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@app.get("/past-wells")
def get_past_wells():
    """
    Get all past wells (deleted wells).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First ensure the table exists
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PastWell]') AND type in (N'U'))
            BEGIN
                CREATE TABLE PastWell (
                    PastWellID INT PRIMARY KEY IDENTITY,
                    OriginalDrillingOperationID INT,
                    SrNo INT,
                    RigID INT,
                    WellID INT,
                    SpudDate DATE,
                    PresentDepthM INT,
                    TDM INT,
                    AFEPlanID INT,
                    MDrld VARCHAR(20),
                    WeeklyM VARCHAR(20),
                    ActualRigDaysID INT,
                    OperationLog NVARCHAR(MAX),
                    StopCard INT,
                    LastUpdated DATETIME,
                    FiscalYearPlanID INT,
                    GeneralNotes NVARCHAR(MAX),
                    RigNo VARCHAR(20),
                    WellName VARCHAR(50),
                    BlockName VARCHAR(50),
                    Latitude FLOAT,
                    Longitude FLOAT,
                    DrlgDays INT,
                    TestDays INT,
                    DryDays INT,
                    TestWODays INT,
                    DeletedAt DATETIME DEFAULT GETDATE()
                )
            END
        """)

        cursor.execute("""
            SELECT 
                PastWellID, OriginalDrillingOperationID, SrNo, RigNo, WellName, BlockName,
                Latitude, Longitude, SpudDate, PresentDepthM, TDM, DrlgDays, TestDays,
                DryDays, TestWODays, OperationLog, StopCard, LastUpdated, DeletedAt
            FROM PastWell
            ORDER BY DeletedAt DESC
        """)

        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching past wells: {e}")
        return []
    finally:
        return_connection(conn)


from fastapi import FastAPI, HTTPException, Request, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pyodbc
import matplotlib.pyplot as plt
from datetime import datetime
from functools import lru_cache
import time
import smtplib
from email.message import EmailMessage
import os
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection settings
server = r'Liverpool\SQLEXPRESS'
database = 'ORM DRILLING OPERATIONS'
driver = '{ODBC Driver 17 for SQL Server}'

# Connection pool for better performance
_connection_pool = []


def get_db_connection():
    if _connection_pool:
        try:
            conn = _connection_pool.pop()
            # Test if connection is still alive
            conn.cursor().execute("SELECT 1")
            return conn
        except:
            pass
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    )
    return conn


def return_connection(conn):
    try:
        if len(_connection_pool) < 5:  # Limit pool size
            _connection_pool.append(conn)
        else:
            conn.close()
    except:
        conn.close()


@app.get("/")
def read_root():
    return {"message": "Drilling backend is running!"}


@app.post("/add-fiscal-year-plan")
def add_fiscal_year_plan(plan: dict = Body(...)):
    required_fields = ["FY", "QTR", "WellName"]
    for field in required_fields:
        if field not in plan or not plan[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO FiscalYearPlan (FY, QTR, WellName, WellDepth, PlanDetails)
            OUTPUT INSERTED.FiscalYearPlanID, INSERTED.FY, INSERTED.QTR, INSERTED.WellName, INSERTED.WellDepth, INSERTED.PlanDetails
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                plan["FY"],
                plan["QTR"],
                plan["WellName"],
                plan.get("WellDepth"),
                plan.get("PlanDetails")
            )
        )
        inserted = cursor.fetchone()
        conn.commit()
        if inserted:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, inserted))
        else:
            raise HTTPException(status_code=500, detail="Insert failed")
    except Exception as e:
        print(f"Error inserting fiscal year plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        return_connection(conn)


@app.post("/send-drilling-report")
async def send_drilling_report(
        pdf: UploadFile,
        to: str = Form(...),
        subject: str = Form(...),
        body: str = Form(...)
):
    try:
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        pdf_bytes = await pdf.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = "zakinabeel522@gmail.com"
        msg["To"] = to
        msg.set_content(body)
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf.filename or "drilling_report.pdf"
        )
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "zakinabeel522@gmail.com"
        smtp_pass = "ytdu babt xwte gqas"
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return {"message": "Email sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@lru_cache(maxsize=1)
def get_cached_drilling_operations():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                do.DrillingOperationID,
                do.SrNo,
                r.RigNo,
                w.WellName,
                w.WellID,
                b.BlockName,
                w.Latitude,
                w.Longitude,
                do.SpudDate,
                do.PresentDepthM,
                do.TDM,
                ap.DrlgDays,
                ap.TestDays,
                do.MDrld,
                do.WeeklyM,
                ar.DryDays,
                ar.TestWODays,
                do.OperationLog,
                do.StopCard,
                do.LastUpdated
            FROM DrillingOperation do
            JOIN Rig r ON do.RigID = r.RigID
            JOIN Well w ON do.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON do.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON do.ActualRigDaysID = ar.ActualRigDaysID
            ORDER BY do.SrNo
        """)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        return_connection(conn)


@app.get("/drilling-operations")
def get_drilling_operations():
    current_time = int(time.time() / 30)
    get_cached_drilling_operations.cache_clear()
    return get_cached_drilling_operations()


@app.get("/fiscal-year-plans")
def get_fiscal_year_plans(wellId: int = None, wellName: str = None, fy: str = "2025-26"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if wellId is not None:
            # First get the well name from Well table using wellId
            cursor.execute("SELECT WellName FROM Well WHERE WellID = ?", wellId)
            well_result = cursor.fetchone()
            if well_result:
                well_name = well_result[0]
                cursor.execute("""
                    SELECT FiscalYearPlanID, FY, QTR, WellName, WellDepth, PlanDetails
                    FROM FiscalYearPlan
                    WHERE FY = ? AND WellName = ?
                    ORDER BY 
                        CASE QTR 
                            WHEN '1st QTR' THEN 1
                            WHEN '2nd QTR' THEN 2
                            WHEN '3rd QTR' THEN 3
                            WHEN '4th QTR' THEN 4
                        END
                """, fy, well_name)
            else:
                return []
        elif wellName is not None:
            cursor.execute("""
                SELECT FiscalYearPlanID, FY, QTR, WellName, WellDepth, PlanDetails
                FROM FiscalYearPlan
                WHERE FY = ? AND WellName = ?
                ORDER BY 
                    CASE QTR 
                        WHEN '1st QTR' THEN 1
                        WHEN '2nd QTR' THEN 2
                        WHEN '3rd QTR' THEN 3
                        WHEN '4th QTR' THEN 4
                    END
            """, fy, wellName)
        else:
            return []
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching fiscal year plans: {e}")
        return []
    finally:
        return_connection(conn)

@app.get("/fiscal-year-plans-all")
def get_fiscal_year_plans_all(fy: str = "2025-26"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT FiscalYearPlanID, FY, QTR, WellName,WellID, WellDepth, PlanDetails
            FROM FiscalYearPlan
            WHERE FY = ?
            ORDER BY WellName, 
                CASE QTR 
                    WHEN '1st QTR' THEN 1
                    WHEN '2nd QTR' THEN 2
                    WHEN '3rd QTR' THEN 3
                    WHEN '4th QTR' THEN 4
                END
        """, fy)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching all fiscal year plans: {e}")
        return []
    finally:
        return_connection(conn)



@app.put("/fiscal-year-plans/{plan_id}")
async def update_fiscal_year_plan(plan_id: int, request: Request):
    data = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE FiscalYearPlan
            SET WellName = ?, WellDepth = ?, PlanDetails = ?
            WHERE FiscalYearPlanID = ?
        """, (data.get("WellName", ""), data.get("WellDepth", ""), data.get("PlanDetails", ""), plan_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)
    return {"message": "Fiscal year plan updated successfully"}



@app.get("/debug/wells")
def debug_wells():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT w.WellID, w.WellName, do.DrillingOperationID
            FROM Well w
            LEFT JOIN DrillingOperation do ON w.WellID = do.WellID
            ORDER BY w.WellName
        """)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"wells": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        return_connection(conn)


@app.put("/drilling-operations/{operation_id}")
async def update_drilling_operation(operation_id: int, request: Request):
    data = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID, 
                   MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, 
                   LastUpdated, FiscalYearPlanID, GeneralNotes
            FROM DrillingOperation
            WHERE DrillingOperationID = ?
        """, (operation_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Drilling operation not found")
            cursor.execute("""
                INSERT INTO DrillingOperationHistory (
                    DrillingOperationID, SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID,
                MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated, 
                FiscalYearPlanID, GeneralNotes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_id,
                current[0], current[1], current[2], current[3], current[4], current[5], current[6],
                current[7], current[8], current[9], current[10], current[11], current[12],
                current[13], current[14]
            ))
        afe_plan_id = current[6]
        if afe_plan_id and ("DrlgDays" in data or "TestDays" in data):
            cursor.execute("""
                UPDATE AFEPlan
                SET DrlgDays = ?, TestDays = ?
                WHERE AFEPlanID = ?
            """, (
                data.get("DrlgDays"),
                data.get("TestDays"),
                afe_plan_id
            ))
        actual_rig_days_id = current[9]
        if actual_rig_days_id and ("DryDays" in data or "TestWODays" in data):
            cursor.execute("""
                UPDATE ActualRigDays
                SET DryDays = ?, TestWODays = ?
                WHERE ActualRigDaysID = ?
            """, (
                data.get("DryDays"),
                data.get("TestWODays"),
                actual_rig_days_id
            ))
        cursor.execute("""
            UPDATE DrillingOperation
            SET
                SrNo = ?,
                PresentDepthM = ?,
                TDM = ?,
                MDrld = ?,
                WeeklyM = ?,
                OperationLog = ?,
                StopCard = ?,
                GeneralNotes = ?,
                LastUpdated = ?
            WHERE DrillingOperationID = ?
        """, (
            data.get("SrNo", current[0]),
            data.get("PresentDepthM", current[4]),
            data.get("TDM", current[5]),
            data.get("MDrld", current[7]),
            data.get("WeeklyM", current[8]),
            data.get("OperationLog", current[10]),
            data.get("StopCard", current[11]),
            data.get("GeneralNotes", current[14] if len(current) > 14 else None),
            datetime.now(),
            operation_id
        ))
        conn.commit()
        return {"message": "Updated successfully"}
    except Exception as e:
        print("UPDATE ERROR:", e)
        conn.rollback()
        import traceback
        print("Full traceback:", traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@app.put("/fiscal-year-plans/{plan_id}")
async def update_fiscal_year_plan(plan_id: int, request: Request):
    data = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE FiscalYearPlan
            SET WellName = ?, WellDepth = ?, PlanDetails = ?
            WHERE FiscalYearPlanID = ?
        """, (data.get("WellName"), data.get("WellDepth"), data.get("PlanDetails"), plan_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)
    return {"message": "Fiscal year plan updated successfully"}


@app.get("/well-depths-plot")
def well_depths_plot():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT w.WellName, do.PresentDepthM
            FROM DrillingOperation do
            JOIN Well w ON do.WellID = w.WellID
        """)
        data = cursor.fetchall()
        wells = [row[0] for row in data]
        depths = [row[1] for row in data]
        plt.figure(figsize=(8, 4))
        plt.bar(wells, depths, color='#1976d2')
        plt.xlabel('Well')
        plt.ylabel('Present Depth (m)')
        plt.title('Present Depth by Well')
        plt.tight_layout()
        img_path = 'well_depths.png'
        plt.savefig(img_path)
        plt.close()
        return FileResponse(img_path, media_type='image/png')
    finally:
        return_connection(conn)


@app.get("/drilling-operations/{operation_id}/history")
def get_drilling_operation_history(operation_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM DrillingOperationHistory
            WHERE DrillingOperationID = ?
            ORDER BY HistoryTimestamp DESC
        """, (operation_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


@app.get("/well-history/{well_id}")
def get_well_history(well_id: int):
    """
    Get all historical drilling operations for a specific well.
    Returns detailed history with rig, well, and block information.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                h.HistoryID,
                h.SrNo,
                h.SpudDate,
                h.PresentDepthM,
                h.TDM,
                h.MDrld,
                h.WeeklyM,
                h.OperationLog,
                h.StopCard,
                h.LastUpdated,
                h.HistoryTimestamp,
                h.GeneralNotes,
                r.RigNo,
                w.WellName,
                b.BlockName,
                w.Latitude,
                w.Longitude,
                ap.DrlgDays,
                ap.TestDays,
                ar.DryDays,
                ar.TestWODays
            FROM DrillingOperationHistory h
            JOIN Rig r ON h.RigID = r.RigID
            JOIN Well w ON h.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON h.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON h.ActualRigDaysID = ar.ActualRigDaysID
            WHERE h.WellID = ?
            ORDER BY h.HistoryTimestamp DESC
        """, (well_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching well history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        return_connection(conn)


@app.get("/well-history/{well_id}/by-date")
def get_well_history_by_date(well_id: int, date: str):
    """
    Get historical drilling operation for a specific well on a specific date.
    Returns detailed history with rig, well, and block information.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Convert date string to datetime for comparison
        search_date = datetime.strptime(date, "%Y-%m-%d").date()

        cursor.execute("""
            SELECT 
                h.HistoryID,
                h.SrNo,
                h.SpudDate,
                h.PresentDepthM,
                h.TDM,
                h.MDrld,
                h.WeeklyM,
                h.OperationLog,
                h.StopCard,
                h.LastUpdated,
                h.HistoryTimestamp,
                h.GeneralNotes,
                r.RigNo,
                w.WellName,
                b.BlockName,
                w.Latitude,
                w.Longitude,
                ap.DrlgDays,
                ap.TestDays,
                ar.DryDays,
                ar.TestWODays
            FROM DrillingOperationHistory h
            JOIN Rig r ON h.RigID = r.RigID
            JOIN Well w ON h.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON h.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON h.ActualRigDaysID = ar.ActualRigDaysID
            WHERE h.WellID = ? AND CAST(h.HistoryTimestamp AS DATE) = ?
            ORDER BY h.HistoryTimestamp DESC
        """, (well_id, search_date))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching well history by date: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        return_connection(conn)


@app.post("/drilling-operations")
async def add_drilling_operation(data: dict = Body(...)):
    """
    Add a new well and drilling operation.
    Expects: WellName, RigName, BlockName, Longitude, Latitude, SpudDate, TargetDepth, PlannedAFEDaysDrilling, PlannedAFEDaysActual
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Ensure Block exists or create it
        cursor.execute("SELECT BlockID FROM Block WHERE BlockName = ?", data["BlockName"])
        block = cursor.fetchone()
        if block:
            block_id = block[0]
        else:
            cursor.execute("INSERT INTO Block (BlockName) OUTPUT INSERTED.BlockID VALUES (?)", data["BlockName"])
            block_id = cursor.fetchone()[0]

        # 2. Ensure Well exists or create it
        cursor.execute("SELECT WellID FROM Well WHERE WellName = ?", data["WellName"])
        well = cursor.fetchone()
        if well:
            well_id = well[0]
        else:
            cursor.execute(
                "INSERT INTO Well (WellName, BlockID, Latitude, Longitude) OUTPUT INSERTED.WellID VALUES (?, ?, ?, ?)",
                (data["WellName"], block_id, data.get("Latitude"), data.get("Longitude")))
            well_id = cursor.fetchone()[0]

        # 3. Ensure Rig exists or create it
        cursor.execute("SELECT RigID FROM Rig WHERE RigNo = ?", data["RigName"])
        rig = cursor.fetchone()
        if rig:
            rig_id = rig[0]
        else:
            cursor.execute("INSERT INTO Rig (RigNo) OUTPUT INSERTED.RigID VALUES (?)", data["RigName"])
            rig_id = cursor.fetchone()[0]

        # 4. Create AFE Plan
        afe_plan_id = None
        if data.get("PlannedAFEDaysDrilling") or data.get("PlannedAFEDaysActual"):
            cursor.execute("""
                INSERT INTO AFEPlan (DrlgDays, TestDays) 
                OUTPUT INSERTED.AFEPlanID 
                VALUES (?, ?)
            """, (data.get("PlannedAFEDaysDrilling"), data.get("PlannedAFEDaysActual")))
            afe_plan_id = cursor.fetchone()[0]

        # 5. Create Actual Rig Days (initially empty)
        actual_rig_days_id = None
        cursor.execute("""
            INSERT INTO ActualRigDays (DryDays, TestWODays) 
            OUTPUT INSERTED.ActualRigDaysID 
            VALUES (NULL, NULL)
        """)
        actual_rig_days_id = cursor.fetchone()[0]

        # 6. Get next SrNo
        cursor.execute("SELECT ISNULL(MAX(SrNo), 0) + 1 FROM DrillingOperation")
        next_sr_no = cursor.fetchone()[0]

        # 7. Insert DrillingOperation
        cursor.execute("""
            INSERT INTO DrillingOperation (
                SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM, AFEPlanID, 
                MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated
            )
            OUTPUT INSERTED.DrillingOperationID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            next_sr_no,
            rig_id,
            well_id,
            data.get("SpudDate"),
            data.get("PresentDepthM", 0),
            data.get("TargetDepth"),
            afe_plan_id,
            data.get("PlannedAFEDaysDrilling"),
            data.get("PlannedAFEDaysActual"),
            actual_rig_days_id,
            "Well under Drilling. Initial setup completed.",  # Default operation log
            0,  # Default stop card
            datetime.now()
        ))
        drilling_operation_id = cursor.fetchone()[0]

        conn.commit()
        return {"success": True, "DrillingOperationID": drilling_operation_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@app.delete("/drilling-operations/{drilling_operation_id}")
async def delete_drilling_operation(drilling_operation_id: int):
    """
    Delete a drilling operation and store it in PastWell table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First, get the complete drilling operation data
        cursor.execute("""
            SELECT 
                do.DrillingOperationID, do.SrNo, do.RigID, do.WellID, do.SpudDate, 
                do.PresentDepthM, do.TDM, do.AFEPlanID, do.MDrld, do.WeeklyM, 
                do.ActualRigDaysID, do.OperationLog, do.StopCard, do.LastUpdated,
                do.FiscalYearPlanID, do.GeneralNotes,
                r.RigNo, w.WellName, b.BlockName, w.Latitude, w.Longitude,
                ap.DrlgDays, ap.TestDays, ar.DryDays, ar.TestWODays
            FROM DrillingOperation do
            JOIN Rig r ON do.RigID = r.RigID
            JOIN Well w ON do.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON do.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON do.ActualRigDaysID = ar.ActualRigDaysID
            WHERE do.DrillingOperationID = ?
        """, (drilling_operation_id,))

        operation_data = cursor.fetchone()
        if not operation_data:
            raise HTTPException(status_code=404, detail="Drilling operation not found")

        # Create PastWell table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PastWell]') AND type in (N'U'))
            BEGIN
                CREATE TABLE PastWell (
                    PastWellID INT PRIMARY KEY IDENTITY,
                    OriginalDrillingOperationID INT,
                    SrNo INT,
                    RigID INT,
                    WellID INT,
                    SpudDate DATE,
                    PresentDepthM INT,
                    TDM INT,
                    AFEPlanID INT,
                    MDrld VARCHAR(20),
                    WeeklyM VARCHAR(20),
                    ActualRigDaysID INT,
                    OperationLog NVARCHAR(MAX),
                    StopCard INT,
                    LastUpdated DATETIME,
                    FiscalYearPlanID INT,
                    GeneralNotes NVARCHAR(MAX),
                    RigNo VARCHAR(20),
                    WellName VARCHAR(50),
                    BlockName VARCHAR(50),
                    Latitude FLOAT,
                    Longitude FLOAT,
                    DrlgDays INT,
                    TestDays INT,
                    DryDays INT,
                    TestWODays INT,
                    DeletedAt DATETIME DEFAULT GETDATE()
                )
            END
        """)

        # Insert into PastWell table
        cursor.execute("""
            INSERT INTO PastWell (
                OriginalDrillingOperationID, SrNo, RigID, WellID, SpudDate, PresentDepthM, TDM,
                AFEPlanID, MDrld, WeeklyM, ActualRigDaysID, OperationLog, StopCard, LastUpdated,
                FiscalYearPlanID, GeneralNotes, RigNo, WellName, BlockName, Latitude, Longitude,
                DrlgDays, TestDays, DryDays, TestWODays
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation_data[0], operation_data[1], operation_data[2], operation_data[3], operation_data[4],
            operation_data[5], operation_data[6], operation_data[7], operation_data[8], operation_data[9],
            operation_data[10], operation_data[11], operation_data[12], operation_data[13], operation_data[14],
            operation_data[15], operation_data[16], operation_data[17], operation_data[18], operation_data[19],
            operation_data[20], operation_data[21], operation_data[22], operation_data[23], operation_data[24]
        ))

        # Now delete the DrillingOperation
        cursor.execute("DELETE FROM DrillingOperation WHERE DrillingOperationID = ?", drilling_operation_id)

        conn.commit()
        return {"success": True, "message": "Well moved to past wells"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@app.get("/past-wells")
def get_past_wells():
    """
    Get all past wells (deleted wells).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First ensure the table exists
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PastWell]') AND type in (N'U'))
            BEGIN
                CREATE TABLE PastWell (
                    PastWellID INT PRIMARY KEY IDENTITY,
                    OriginalDrillingOperationID INT,
                    SrNo INT,
                    RigID INT,
                    WellID INT,
                    SpudDate DATE,
                    PresentDepthM INT,
                    TDM INT,
                    AFEPlanID INT,
                    MDrld VARCHAR(20),
                    WeeklyM VARCHAR(20),
                    ActualRigDaysID INT,
                    OperationLog NVARCHAR(MAX),
                    StopCard INT,
                    LastUpdated DATETIME,
                    FiscalYearPlanID INT,
                    GeneralNotes NVARCHAR(MAX),
                    RigNo VARCHAR(20),
                    WellName VARCHAR(50),
                    BlockName VARCHAR(50),
                    Latitude FLOAT,
                    Longitude FLOAT,
                    DrlgDays INT,
                    TestDays INT,
                    DryDays INT,
                    TestWODays INT,
                    DeletedAt DATETIME DEFAULT GETDATE()
                )
            END
        """)

        cursor.execute("""
            SELECT 
                PastWellID, OriginalDrillingOperationID, SrNo, RigNo, WellName, BlockName,
                Latitude, Longitude, SpudDate, PresentDepthM, TDM, DrlgDays, TestDays,
                DryDays, TestWODays, OperationLog, StopCard, LastUpdated, DeletedAt
            FROM PastWell
            ORDER BY DeletedAt DESC
        """)

        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching past wells: {e}")
        return []
    finally:
        return_connection(conn)


@app.get("/drilling-operations/{operation_id}/history")
def get_drilling_operation_history(operation_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM DrillingOperationHistory
            WHERE DrillingOperationID = ?
            ORDER BY HistoryTimestamp DESC
        """, (operation_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()

@app.get("/well-history/{well_id}")
def get_well_history(well_id: int):
    """
    Get all historical drilling operations for a specific well.
    Returns detailed history with rig, well, and block information.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                h.HistoryID,
                h.SrNo,
                h.SpudDate,
                h.PresentDepthM,
                h.TDM,
                h.MDrld,
                h.WeeklyM,
                h.OperationLog,
                h.StopCard,
                h.LastUpdated,
                h.HistoryTimestamp,
                h.GeneralNotes,
                r.RigNo,
                w.WellName,
                b.BlockName,
                w.Latitude,
                w.Longitude,
                ap.DrlgDays,
                ap.TestDays,
                ar.DryDays,
                ar.TestWODays
            FROM DrillingOperationHistory h
            JOIN Rig r ON h.RigID = r.RigID
            JOIN Well w ON h.WellID = w.WellID
            JOIN Block b ON w.BlockID = b.BlockID
            LEFT JOIN AFEPlan ap ON h.AFEPlanID = ap.AFEPlanID
            LEFT JOIN ActualRigDays ar ON h.ActualRigDaysID = ar.ActualRigDaysID
            WHERE h.WellID = ?
            ORDER BY h.HistoryTimestamp DESC
        """, (well_id,))
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Error fetching well history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        return_connection(conn)

        return_connection(conn)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7157)