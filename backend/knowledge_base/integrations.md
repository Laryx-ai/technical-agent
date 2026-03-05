# CloudDesk Integrations

---

## Overview

CloudDesk supports integrations with popular tools to help your team stay connected and automate workflows. Integrations can be managed from:

**Settings → Integrations**

---

## Slack

Connect CloudDesk to your Slack workspace to receive ticket notifications directly in Slack channels.

**How to set up:**
1. Go to **Settings → Integrations → Slack**
2. Click **Connect Slack**
3. Sign in to your Slack workspace and authorize CloudDesk
4. Select the Slack channel where notifications should be sent
5. Click **Save**

**What you get:**
- New ticket alerts in Slack
- Ticket status update notifications
- Team mentions when a ticket is assigned

**Troubleshooting:**
- If notifications stop, re-authorize the Slack integration from the same settings page.
- Make sure the CloudDesk bot has permission to post in your chosen channel.

---

## Microsoft Teams

Receive CloudDesk notifications in Microsoft Teams channels.

**How to set up:**
1. Go to **Settings → Integrations → Microsoft Teams**
2. Click **Connect Teams**
3. Sign in with your Microsoft account
4. Choose the team and channel for notifications
5. Save the integration

---

## Zapier

Use Zapier to connect CloudDesk with thousands of other apps — automate ticket creation, send data to CRMs, trigger emails, and more.

**How to set up:**
1. Go to **Settings → Integrations → Zapier**
2. Copy your CloudDesk API key
3. In Zapier, create a new Zap
4. Select **CloudDesk** as the trigger app
5. Authenticate with your API key
6. Configure your trigger and action

**Common Zap examples:**
- New CloudDesk ticket → Create a row in Google Sheets
- New CloudDesk ticket → Send a notification in Telegram
- Form submission in Typeform → Create a CloudDesk ticket

---

## Jira

Link CloudDesk tickets to Jira issues for engineering escalations.

**How to set up:**
1. Go to **Settings → Integrations → Jira**
2. Enter your Jira domain (e.g., yourcompany.atlassian.net)
3. Enter your Jira API token
4. Map CloudDesk ticket fields to Jira issue fields
5. Save the integration

**What you get:**
- Escalate a CloudDesk ticket to a Jira issue with one click
- Sync status between CloudDesk and Jira
- View linked Jira issues directly from the ticket

---

## Email Channels

Connect a support email address so that incoming emails automatically create tickets.

**How to set up:**
1. Go to **Settings → Channels → Email**
2. Click **Add Email Channel**
3. Enter your support email address (e.g., support@yourcompany.com)
4. Follow the instructions to set up email forwarding from your email provider
5. Verify the connection

**Supported email providers:** Gmail, Outlook, Yahoo, custom SMTP

---

## API Integration (Custom)

For custom integrations, CloudDesk provides a REST API.

**Base URL:** `https://api.clouddesk.io/v1`

**Authentication:** Include your API key in every request header:
```
Authorization: Bearer YOUR_API_KEY
```

**Key endpoints:**

| Action              | Method | Endpoint                  |
| ------------------- | ------ | ------------------------- |
| Create ticket       | POST   | /api/v1/tickets           |
| List tickets        | GET    | /api/v1/tickets           |
| Get ticket by ID    | GET    | /api/v1/tickets/{id}      |
| Update ticket       | PATCH  | /api/v1/tickets/{id}      |
| Close ticket        | DELETE | /api/v1/tickets/{id}      |

**Rate limits:**
- 100 requests per minute
- 5000 requests per day

---

## Removing an Integration

To disconnect any integration:
1. Go to **Settings → Integrations**
2. Find the integration you want to remove
3. Click **Disconnect**

This will immediately stop CloudDesk from sending data to that service.
