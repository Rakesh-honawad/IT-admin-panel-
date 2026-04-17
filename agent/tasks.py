import os

BASE_URL = os.getenv("BASE_URL")

def task_onboard_user(name: str, email: str, role: str = "Engineer", product: str = "GitHub Enterprise") -> str:
    return f"""
You are an IT admin agent operating the admin panel at {BASE_URL}.

TASK: Onboard a new user with the following details:
  - Name:  {name}
  - Email: {email}
  - Role:  {role}
  - License to assign: {product}

Follow these steps EXACTLY:

STEP 1 — Check if user already exists:
  Go to {BASE_URL}/users.
  Look at the email column in the users table.
  If you can see "{email}" already in the table, skip to STEP 3.
  If "{email}" is NOT in the table, proceed to STEP 2.

STEP 2 — Create the user:
  Click the "+ Add User" button.
  Wait for the modal to appear.
  Fill in Full Name as "{name}".
  Fill in Email as "{email}".
  Select Role as "{role}".
  Click "Create User".
  Wait for the page to reload and confirm "{name}" appears in the table.
  Take a screenshot confirming the user was created.

STEP 3 — Assign the license:
  Navigate to {BASE_URL}/licenses.
  Click the "+ Assign License" button.
  Fill in the email field with "{email}".
  Select "{product}" from the product dropdown.
  Click "Assign".
  Wait for the page to reload.
  Confirm a row appears with "{name}" and "{product}".
  Take a screenshot confirming the license assignment.

STEP 4 — Final report:
  State clearly: "Onboarding complete for {name}. User created: yes/no (already existed). License assigned: {product}."
"""


def task_security_lockdown(target_name: str, target_user_id: int) -> str:
    return f"""
You are an IT admin agent operating the admin panel at {BASE_URL}.

TASK: Perform a security lockdown for user "{target_name}" (user_id={target_user_id}).

Follow these steps EXACTLY:

STEP 1 — Navigate to security page:
  Go to {BASE_URL}/security.
  Find the row for "{target_name}" in the security table.
  Note their current session count and MFA status.
  Take a screenshot of the current state.

STEP 2 — Revoke all sessions:
  In the row for "{target_name}", click "Revoke Sessions".
  Wait for the page to reload.
  Confirm the sessions count for "{target_name}" now shows 0.
  Take a screenshot confirming sessions were revoked.

STEP 3 — Reset MFA:
  In the row for "{target_name}", click "Reset MFA".
  Wait for the page to reload.
  Confirm the status badge for "{target_name}" now shows "Secured".
  Look for any success banner or confirmation message and note it.
  Take a screenshot of the final secured state.

STEP 4 — Final report:
  State clearly: "Security lockdown complete for {target_name}. Sessions revoked: yes. MFA reset: yes. Final status: Secured."
"""