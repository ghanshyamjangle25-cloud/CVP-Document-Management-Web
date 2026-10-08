# CVP Document Management

A ready-to-run Python + Streamlit document management application for CVP.


## Updated interface structure
- Persistent left-side navigation inspired by the supplied Asset Management structure
- CVP-specific light teal/slate visual design (not a copy of the Asset Management theme)
- Role-based navigation automatically shows only permitted modules
- User identity and role shown in the sidebar
- Logout control placed in the sidebar
- Existing dashboard, document approval, employee, project, insurance, contract, salary, accounts, reminders, engineering registers, reports, audit and administration functions retained

## Included modules
- Role-based login: Admin, HR, Manager, Accounts, Employee
- Dashboard and expiry/renewal alerts
- Document register, upload, automatic numbering, metadata and search
- Revision/version control and check-in/check-out
- Manager → Authorized Reviewer → Admin approval workflow
- QR code for document identification
- Employee master, bank/account, PAN/UAN/PF/ESI details
- Projects
- Insurance policies, linked assets/employees, expiry status and renewal/archive workflow
- Contracts
- Salary calculation: gross, deductions and net salary
- Accounts receipt/payment register
- Tasks, due dates and escalation
- Drawing Register, MDR, Transmittals, Correspondence, MOM, Vendor and Compliance registers
- Reports and CSV export
- Audit trail
- Recycle bin
- ZIP backup

## Folder structure
```
CVP_Document_Management/
  app.py
  requirements.txt
  README.md
  RUN_APP.bat
  data/
  uploads/
    documents/
    insurance/
    contracts/
  archive/
  backups/
```

## Run in VS Code / PowerShell
1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open `app.py`.
4. Open **Terminal → New Terminal**.
5. Run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Or double-click `RUN_APP.bat`.

## Demo users
| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| HR | hr | cvp123 |
| Manager | manager | cvp123 |
| Accounts | accounts | cvp123 |

Change these passwords/users before real deployment.

## Data

### Demo examples

A formatted fictional company SOP is included at
[`examples/DEMO-COMPANY-001.pdf`](examples/DEMO-COMPANY-001.pdf).
Loading examples also adds it to **Documents** as
**Company Document Control Procedure (Demo)**, ready to download.

Log in as `admin` / `admin123`, open **Administration > Examples**, and click
**Load Demo Examples**. This adds fictional employees, a linked warehouse project,
three downloadable documents (including one awaiting approval), active and expired
insurance policies, a contract nearing expiry, salary and account entries,
tasks, and an example in every engineering register.

Try **Documents** to download a sample or check it out, **Approvals** to review
`DEMO-DOC-002`, and **Dashboard** to see expiry alerts. **Reports** exports the data
as CSV. Dates are relative to the day you load the examples.

Examples use `DEMO` references and are loaded only when requested. Loading again
skips existing examples without replacing edits or duplicating records. The sample
documents are stored in `uploads/documents/demo/`.
The app automatically creates `data/cvp_dms.db` on first run. Uploaded files are stored under `uploads/`. Backups can be created from **Administration → Backup**.

## Production upgrade path
This ZIP is self-contained with SQLite for easy local use. For multi-user production deployment, move the database layer to PostgreSQL and uploaded documents to shared/object storage, then place the app behind HTTPS and enterprise authentication.

## Git / GitHub repository notes
This source package is repository-ready. Runtime/private content is intentionally excluded by `.gitignore`, including the SQLite database, uploaded files, archives, generated backups, caches, local secrets and virtual environments.

After cloning, run the app normally. It automatically recreates `data/`, `uploads/`, `archive/` and `backups/` as required. Do not commit those runtime folders. Change the built-in demo/default passwords before production use.
