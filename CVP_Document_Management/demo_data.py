"""Fictional examples for the local DMS; existing records are never overwritten."""

from datetime import date, datetime, timedelta
from pathlib import Path
import shutil


def load_demo_data(connection, upload_dir, username="admin", today=None):
    """Insert missing examples in one transaction and return the inserted count."""
    today = today or date.today()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    day = lambda offset: (today + timedelta(days=offset)).isoformat()
    count = 0

    def insert(table, key, values):
        nonlocal count
        if connection.execute(
            f"SELECT 1 FROM {table} WHERE {key}=?", (values[key],)
        ).fetchone():
            return None
        values = {"created_at": timestamp, **values}
        columns = ",".join(values)
        placeholders = ",".join("?" for _ in values)
        cursor = connection.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        count += 1
        return cursor.lastrowid

    with connection:
        for code, name, department, designation in [
            ("DEMO-EMP-001", "Asha Demo", "Engineering", "Design Engineer"),
            ("DEMO-EMP-002", "Ravi Demo", "Projects", "Project Manager"),
            ("DEMO-EMP-003", "Meera Demo", "HR", "HR Executive"),
        ]:
            insert("employees", "employee_code", dict(
                employee_code=code, name=name, department=department,
                designation=designation, manager="Ravi Demo", joining_date=day(-180),
                email=f"{code.lower()}@example.com", employment_type="Permanent",
                status="Active", user_role="Employee",
            ))
        insert("projects", "project_code", dict(
            project_code="DEMO-PRJ-001", name="Demo Warehouse Expansion",
            client="Example Industries", manager="Ravi Demo", start_date=day(-60),
            end_date=day(120), status="Active", location="Demo Site",
            description="Fictional project for exploring linked records.",
        ))
        for number, title, status, stage, expiry in [
            ("DEMO-DOC-001", "Demo quality procedure", "Approved", "Completed", 180),
            ("DEMO-DOC-002", "Demo site inspection report", "Pending Review", "Manager Review", 90),
            ("DEMO-DOC-003", "Demo safety certificate", "Approved", "Completed", 10),
        ]:
            if connection.execute("SELECT 1 FROM documents WHERE doc_no=?", (number,)).fetchone():
                continue
            folder = upload_dir / "documents" / "demo"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{number}.txt"
            if not path.exists():
                path.write_text(
                    f"{title}\nDocument: {number}\nProject: DEMO-PRJ-001\n\n"
                    "FICTIONAL DEMO EXAMPLE\nUse this file to try download, revision, "
                    "check-out and approval features.\n", encoding="utf-8",
                )
            doc_id = insert("documents", "doc_no", dict(
                doc_no=number, title=title, category="Engineering", doc_type="Report",
                department="Engineering", related_to="Project", related_ref="DEMO-PRJ-001",
                project_code="DEMO-PRJ-001", owner="Asha Demo", prepared_by="Asha Demo",
                checked_by="manager", approved_by="admin" if status == "Approved" else "",
                revision="R0", issue_date=day(-30), expiry_date=day(expiry), reminder_days=30,
                version=1, confidentiality="Internal", description="Fictional demo example.",
                filename=path.name, filepath=str(path.resolve()), status=status,
                approval_stage=stage, created_by=username, updated_at=timestamp,
            ))
            if status == "Pending Review":
                connection.execute(
                    "INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,created_at) "
                    "VALUES(?,?,?,?,?,?)", (doc_id, "Manager", "manager", "Pending", "Demo review", timestamp),
                )
        company_number = "DEMO-COMPANY-001"
        if not connection.execute("SELECT 1 FROM documents WHERE doc_no=?", (company_number,)).fetchone():
            source = Path(__file__).resolve().parent / "examples" / f"{company_number}.pdf"
            destination = upload_dir / "documents" / "demo" / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copyfile(source, destination)
            insert("documents", "doc_no", dict(
                doc_no=company_number, title="Company Document Control Procedure (Demo)",
                category="Quality", doc_type="SOP", department="Quality",
                related_to="Project", related_ref="DEMO-PRJ-001", project_code="DEMO-PRJ-001",
                owner="Asha Demo", prepared_by="Asha Demo", checked_by="Ravi Demo",
                revision="R0", issue_date="2026-10-01", reminder_days=30,
                version=1, confidentiality="Internal",
                description="Fictional company SOP with responsibilities, review workflow and revision history.",
                filename=destination.name, filepath=str(destination.resolve()),
                status="Draft", approval_stage="Draft", created_by=username, updated_at=timestamp,
            ))
        for number, expiry in [("DEMO-POL-001", 15), ("DEMO-POL-002", -5)]:
            insert("insurance", "policy_no", dict(
                policy_no=number, policy_type="Asset Insurance", company="Example Insurance",
                related_type="Asset", related_ref="DEMO-AST-001", start_date=day(-365),
                expiry_date=day(expiry), premium=12000, sum_insured=500000,
                broker="Demo Broker", reminder_days=30,
                status="Active" if expiry >= 0 else "Expired", updated_at=timestamp,
            ))
        insert("contracts", "contract_no", dict(
            contract_no="DEMO-CON-001", title="Demo equipment maintenance agreement",
            counterparty="Example Services", start_date=day(-90), expiry_date=day(20),
            value=75000, owner="Ravi Demo", reminder_days=30, status="Active",
        ))
        insert("salary", "employee_code", dict(
            employee_code="DEMO-EMP-001", salary_month=today.strftime("%Y-%m"),
            basic=30000, hra=12000, allowances=3000, bonus=0, pf=1800, tax=1500,
            other_deductions=200, gross=45000, deductions=3500, net=41500,
        ))
        for reference, entry_type, amount in [
            ("DEMO-ACC-001", "Receipt", 150000), ("DEMO-ACC-002", "Payment", 12000),
        ]:
            insert("accounts", "reference", dict(
                reference=reference, entry_date=day(-2), entry_type=entry_type,
                category="Project", amount=amount, party="Example Industries",
                description="Fictional demo transaction", created_by=username,
            ))
        for title, module, reference, due in [
            ("Demo: renew equipment insurance", "Insurance", "DEMO-POL-001", 7),
            ("Demo: review site inspection", "Documents", "DEMO-DOC-002", -2),
        ]:
            insert("tasks", "title", dict(
                title=title, module=module, record_ref=reference, assignee="manager",
                due_date=day(due), priority="High", status="Open", escalation="admin",
                notes="Fictional example for reminders and overdue tasks.",
            ))
        for index, module in enumerate([
            "Drawing Register", "MDR", "Transmittal", "Correspondence", "MOM",
            "Vendor Register", "Compliance Register",
        ], start=1):
            insert("generic_registers", "record_no", dict(
                record_no=f"DEMO-REG-{index:03d}", module=module,
                title=f"Demo {module} example", project_code="DEMO-PRJ-001",
                owner="Ravi Demo", record_date=day(-1), status="Open",
                remarks="Fictional example linked to the demo project.",
            ))
        # ---- Bulk demo set: about 20 records per section ----
        first = ["Aarav","Vivaan","Aditya","Sai","Arjun","Reyansh","Krishna","Ishaan","Rohan","Kabir",
                 "Ananya","Diya","Meera","Saanvi","Priya","Neha","Riya","Kavya","Isha","Pooja"]
        last = ["Patil","Deshmukh","Kulkarni","Joshi","Shinde","Pawar","More","Gaikwad","Jadhav","Kale"]
        depts = ["Engineering","Projects","Quality","HR","Accounts","Administration","IT","Management"]
        roles = ["Design Engineer","Site Engineer","Project Manager","QA Engineer","HR Executive","Accountant","CAD Draftsman","Admin Officer","IT Support","Senior Engineer"]
        banks = ["State Bank of India","HDFC Bank","ICICI Bank","Axis Bank","Bank of Maharashtra"]
        clients = ["Ludhiana Infra Corporation","Bhubaneswar Smart Utilities","Patna Jal Board","Ranchi Smart City Ltd","Pune Metro Works"]
        statuses = ["Active","Planning","On Hold","Completed"]
        names = [f"{first[i]} {last[i % 10]}" for i in range(20)]
        for i in range(20):
            n = i + 1
            insert("employees", "employee_code", dict(
                employee_code=f"CVP-E{n:03d}", name=names[i], department=depts[i % 8], designation=roles[i % 10],
                manager=names[0], joining_date=day(-90 - i * 40), mobile=f"98{n:08d}",
                email=f"{first[i].lower()}.{last[i % 10].lower()}@cvpa.example", employment_type="Permanent",
                status="Active", user_role="Employee", bank_name=banks[i % 5],
                account_number=f"5010{n:08d}", ifsc=f"{banks[i % 5][:4].upper()}0001{n:03d}"[:11],
                pan=f"ABCDE{1000 + n}F", uan=f"1000{n:08d}", pf_number=f"PUPUN{n:07d}", esi_number=f"3100{n:07d}",
            ))
            insert("projects", "project_code", dict(
                project_code=f"PRJ-{n:03d}", name=f"{clients[i % 5].split()[0]} Project Phase {n}",
                client=clients[i % 5], manager=names[i], start_date=day(-200 + i * 8),
                end_date=day(30 + i * 20), status=statuses[i % 4], location=["Pune","Mumbai","Nagpur","Nashik","Satara"][i % 5],
                description="Sample engineering project for demonstration.",
            ))
            number = f"DOC-{n:03d}"
            if not connection.execute("SELECT 1 FROM documents WHERE doc_no=?", (number,)).fetchone():
                folder = upload_dir / "documents" / "demo"
                folder.mkdir(parents=True, exist_ok=True)
                path = folder / f"{number}.txt"
                if not path.exists():
                    path.write_text(f"Sample document {number}\nProject: PRJ-{n:03d}\n\nDemo file.\n", encoding="utf-8")
                status = ["Approved","Pending Review","Draft","Approved","Correction Required"][i % 5]
                doc_id = insert("documents", "doc_no", dict(
                    doc_no=number, title=["Design Basis Report","Structural Calculation","Site Inspection Report","Quality Plan","Method Statement"][i % 5] + f" {n}",
                    category=["Engineering","Quality","Safety","Commercial"][i % 4], doc_type=["Report","Drawing","SOP","Certificate"][i % 4],
                    department=depts[i % 8], related_to="Project", related_ref=f"PRJ-{n:03d}", project_code=f"PRJ-{n:03d}",
                    owner=names[i], prepared_by=names[i], checked_by=names[(i + 1) % 20],
                    approved_by=names[0] if status == "Approved" else "", revision=f"R{i % 3}", issue_date=day(-60 + i),
                    expiry_date=day(10 + i * 18), reminder_days=30, version=1 + i % 3, confidentiality=["Internal","Confidential","Public"][i % 3],
                    description="Sample document for demonstration.", filename=path.name, filepath=str(path.resolve()),
                    status=status, approval_stage="Completed" if status == "Approved" else "Manager Review",
                    created_by=username, updated_at=timestamp,
                ))
                if doc_id and status in ("Pending Review", "Correction Required"):
                    connection.execute(
                        "INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,created_at) VALUES(?,?,?,?,?,?)",
                        (doc_id, "Manager", "manager", "Pending", "Sample review", timestamp))
            insert("insurance", "policy_no", dict(
                policy_no=f"POL-{n:03d}", policy_type=["Asset Insurance","Vehicle Insurance","Health Insurance","Fire Insurance","Professional Indemnity"][i % 5],
                company=["LIC","New India Assurance","HDFC Ergo","ICICI Lombard"][i % 4], related_type="Asset", related_ref=f"AST-{n:03d}",
                start_date=day(-300), expiry_date=day(-10 + i * 17), premium=8000 + i * 1500, sum_insured=300000 + i * 50000,
                broker="CVP Brokers", reminder_days=30, status="Active", updated_at=timestamp,
            ))
            insert("contracts", "contract_no", dict(
                contract_no=f"CON-{n:03d}", title=["Maintenance Agreement","Consultancy Agreement","Software License","Site Services","Rental Agreement"][i % 5] + f" {n}",
                counterparty=clients[i % 5], start_date=day(-120), expiry_date=day(5 + i * 21),
                value=100000 + i * 35000, owner=names[i], reminder_days=30, status="Active",
            ))
            if not connection.execute("SELECT 1 FROM salary WHERE employee_code=? AND salary_month=?", (f"CVP-E{n:03d}", today.strftime("%Y-%m"))).fetchone():
                basic = 30000 + i * 2500; hra = basic * 0.4; allow = 3000 + i * 200
                pf = round(basic * 0.12); tax = 500 * (i % 6); other = 200
                gross = basic + hra + allow
                insert("salary", "id", dict(id=None, employee_code=f"CVP-E{n:03d}", salary_month=today.strftime("%Y-%m"),
                    basic=basic, hra=hra, allowances=allow, bonus=0, pf=pf, tax=tax, other_deductions=other,
                    gross=gross, deductions=pf + tax + other, net=gross - pf - tax - other))
            insert("accounts", "reference", dict(
                reference=f"ACC-{n:03d}", entry_date=day(-i * 3), entry_type="Receipt" if i % 3 else "Payment",
                category=["Project","Salary","Office","Travel","Software"][i % 5], amount=15000 + i * 7500,
                party=clients[i % 5], description="Sample transaction for demonstration.", created_by=username,
            ))
            insert("tasks", "title", dict(
                title=f"Sample task {n}: " + ["review drawings","renew policy","submit report","update register","follow up client"][i % 5],
                module=["Documents","Insurance","Projects","Contracts"][i % 4], record_ref=f"DOC-{n:03d}", assignee=names[i],
                due_date=day(-3 + i * 2), priority=["High","Medium","Low","Urgent"][i % 4], status=["Open","In Progress","Waiting"][i % 3],
                escalation="admin", notes="Sample task for demonstration.",
            ))
            insert("assets", "asset_code", dict(
                asset_code=f"AST-{n:03d}", asset_type=["Laptop","Vehicle","Total Station","Printer","Workstation"][i % 5],
                description=f"Sample asset {n}", assigned_to=names[i], location=["Pune Office","Site A","Site B"][i % 3],
                purchase_date=day(-400 + i * 10), value=40000 + i * 9000, insurance_policy=f"POL-{n:03d}", status="In Use",
            ))
            for m, module in enumerate(["Drawing Register","MDR","Transmittal","Correspondence","MOM","Vendor Register","Compliance Register"]):
                insert("generic_registers", "record_no", dict(
                    record_no=f"{module[:3].upper()}-{n:03d}", module=module, title=f"{module} entry {n}",
                    project_code=f"PRJ-{n:03d}", owner=names[(i + m) % 20], record_date=day(-i),
                    status=["Open","Draft","Issued","Approved","Closed"][(i + m) % 5], remarks="Sample register entry.",
                ))
        if count:
            connection.execute(
                "INSERT INTO audit_log(timestamp,username,action,module,record_ref,details) VALUES(?,?,?,?,?,?)",
                (timestamp, username, "LOAD_DEMO", "System", "DEMO", f"Added {count} fictional example records"),
            )
    return count
