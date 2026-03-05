# CloudDesk SaaS Documentation

*A Sample Knowledge Base for a SaaS Technical Support Agent*

---

# 1. Introduction

CloudDesk is a cloud-based customer support platform designed to help teams manage, track, and resolve customer issues efficiently. It provides tools for ticket management, team collaboration, API integration, and analytics.

This documentation provides guidance for common operations including account setup, ticket management, troubleshooting, API integration, and billing.

---

# 2. Account Setup

## Creating a CloudDesk Account

To create an account:

1. Navigate to the CloudDesk homepage.
2. Click **Sign Up**.
3. Enter your email address and create a secure password.
4. Verify your email address using the verification link sent to your inbox.

After verification, users will be directed to the **workspace setup page**.

---

## Workspace Configuration

During setup, users must configure their workspace by entering:

* Workspace Name
* Company Name
* Support Email
* Time Zone

These settings can be modified later from:

**Settings → Workspace Preferences**

---

## Inviting Team Members

To add members to your workspace:

1. Go to **Settings → Team Members**.
2. Click **Invite Member**.
3. Enter the email address of the user.
4. Assign a role.

Available roles include:

* **Admin** – Full system access
* **Agent** – Can manage tickets
* **Viewer** – Read-only access

Invited users will receive an email invitation.

---

# 3. Ticket Management

## Creating Tickets

Tickets are created automatically when customers contact support via:

* Email
* Live Chat
* Web Form
* API

Agents can also create tickets manually.

### Manual Ticket Creation

1. Click **New Ticket**
2. Enter customer email
3. Add subject and description
4. Submit ticket

---

## Ticket Status Types

CloudDesk supports four ticket states:

| Status   | Description                |
| -------- | -------------------------- |
| Open     | Ticket has been created    |
| Pending  | Waiting for customer reply |
| Resolved | Issue has been solved      |
| Closed   | Ticket archived            |

---

## Assigning Tickets

Tickets can be assigned to a specific agent or support team.

Steps:

1. Open the ticket.
2. Click **Assign Agent**.
3. Choose an available agent.

This ensures accountability and faster resolution.

---

# 4. Troubleshooting Guide

## Login Issues

### Problem

User cannot log into the CloudDesk dashboard.

### Possible Causes

* Incorrect password
* Expired session
* Browser cookies disabled

### Solution

1. Confirm correct email and password.
2. Use **Forgot Password** to reset credentials.
3. Clear browser cache and cookies.
4. Enable cookies in browser settings.

---

## Account Locked

### Problem

User account becomes locked after multiple failed login attempts.

### Solution

1. Wait **15 minutes** before retrying login.
2. Reset password.
3. Contact the workspace administrator.

---

# 5. API Integration

## Overview

CloudDesk provides a REST API that allows developers to integrate support ticket functionality into external applications.

---

## API Authentication

All API requests require an API Key.

To generate an API key:

1. Navigate to **Settings → Developer → API Keys**
2. Click **Generate New Key**
3. Copy and securely store the key

API keys should never be shared publicly.

---

## Example API Request

Create a ticket.

Endpoint:

```
POST /api/v1/tickets
```

Example request body:

```json
{
  "customer_email": "user@example.com",
  "subject": "Login issue",
  "description": "Unable to access my account"
}
```

---

## API Rate Limits

To ensure fair usage, the API enforces limits.

| Limit Type | Restriction   |
| ---------- | ------------- |
| Per Minute | 100 requests  |
| Per Day    | 5000 requests |

Requests exceeding these limits return:

```
HTTP 429 - Too Many Requests
```

---

# 6. Billing and Subscription

## Subscription Plans

CloudDesk offers three subscription tiers.

| Plan       | Price          | Features                  |
| ---------- | -------------- | ------------------------- |
| Starter    | $19/month      | Basic ticketing           |
| Pro        | $49/month      | Automation + integrations |
| Enterprise | Custom pricing | Advanced analytics        |

---

## Updating Payment Method

To update billing information:

1. Navigate to **Settings → Billing**
2. Click **Update Payment Method**
3. Enter new card details
4. Save changes

---

## Failed Payments

If a payment fails:

* The system retries automatically within **24 hours**
* A notification email is sent
* Access may be restricted after **7 days**

---

# 7. Integrations

CloudDesk supports integrations with several external platforms.

Supported integrations include:

* Slack
* Microsoft Teams
* Zapier
* Jira

Integrations can be enabled via:

**Settings → Integrations**

---

# 8. Data Export

Users can export ticket data for reporting.

Steps:

1. Go to **Reports → Export Data**
2. Select export format (CSV or JSON)
3. Download the generated report

Exports include ticket details, timestamps, and agent assignments.

---

# 9. Frequently Asked Questions

## How do I reset my password?

Click **Forgot Password** on the login page and follow the instructions sent to your email.

---

## How can I export support tickets?

Navigate to:

**Reports → Export Data**

Select CSV format and download the file.

---

## Can I integrate CloudDesk with Slack?

Yes. Slack integration is available under:

**Settings → Integrations → Slack**

---

## How do I generate an API key?

Go to:

**Settings → Developer → API Keys**

Click **Generate New Key**.

---

# 10. Support Contact

If issues cannot be resolved using the documentation, users may contact CloudDesk support.

Support channels include:

* Email: [support@clouddesk.com](mailto:support@clouddesk.com)
* Live Chat (available inside dashboard)
* Support Portal

Support hours: **Monday – Friday, 9 AM – 6 PM UTC**

---

# End of Documentation
