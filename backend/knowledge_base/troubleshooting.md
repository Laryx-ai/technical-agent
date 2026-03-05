# CloudDesk Troubleshooting Guide

---

## Login & Account Issues

### Cannot Log In

**Symptoms:** Login page shows an error or the page just reloads.

**Steps to fix:**
1. Double-check your email address and password for typos.
2. Click **Forgot Password** to reset your credentials.
3. Clear your browser cache and cookies, then try again.
4. Make sure cookies are enabled in your browser settings.
5. Try a different browser or incognito mode.
6. If the issue persists, contact your workspace admin to check if your account is active.

---

### Account Locked

**Symptoms:** Message says "Account locked" or "Too many failed attempts."

**Why it happens:** CloudDesk temporarily locks accounts after multiple failed login attempts for security reasons.

**Steps to fix:**
- Wait **15 minutes** and try again.
- Reset your password using **Forgot Password** on the login page.
- Contact your workspace admin if the lock doesn't lift after a reset.

---

### Password Reset Email Not Arriving

**Steps to fix:**
1. Check your spam or junk folder.
2. Make sure you are entering the correct registered email address.
3. Wait up to 5 minutes for delivery.
4. Try requesting the reset email again.
5. Contact support if the email still does not arrive.

---

### Two-Factor Authentication (2FA) Issues

**Symptoms:** 2FA code is not accepted.

**Steps to fix:**
1. Ensure your device's time is synchronized correctly — 2FA codes are time-sensitive.
2. Use a fresh code from your authenticator app.
3. If you have lost access to your 2FA device, contact your workspace admin to disable 2FA for your account.

---

## Ticket Issues

### Tickets Not Being Created from Email

**Symptoms:** Customers send emails but no tickets appear in the dashboard.

**Steps to fix:**
1. Go to **Settings → Channels → Email** and confirm the support email is correctly configured.
2. Check your email provider's forwarding rules are active.
3. Make sure the connected mailbox is not full.
4. Review the spam filters on your email provider — CloudDesk emails may be getting blocked.

---

### Ticket Assignment Not Working

**Symptoms:** Tickets stay unassigned even with auto-assignment rules set up.

**Steps to fix:**
1. Go to **Settings → Automation** and verify the assignment rules are enabled.
2. Confirm the target agents have the **Agent** role and are not set to "Away."
3. Check if the rule conditions match the ticket properties being submitted.

---

### Cannot Change Ticket Status

**Symptoms:** Status dropdown is greyed out or changes don't save.

**Steps to fix:**
1. Confirm you have **Agent** or **Admin** role — Viewers cannot change ticket status.
2. Refresh the page and try again.
3. If the ticket is marked **Closed**, it must be reopened first.

---

## API Issues

### HTTP 401 – Unauthorized

**Cause:** Invalid or missing API key.

**Steps to fix:**
1. Check that you are sending the API key in the request header: `Authorization: Bearer YOUR_API_KEY`
2. Verify the key is still valid from **Settings → Developer → API Keys**.
3. Generate a new key if the current one has been revoked.

---

### HTTP 429 – Too Many Requests

**Cause:** Your application has exceeded the rate limit (100 requests/minute or 5000/day).

**Steps to fix:**
1. Implement request throttling or a queue in your integration.
2. Add retry logic with exponential backoff.
3. Upgrade to Enterprise plan for higher rate limits.

---

### HTTP 422 – Validation Error

**Cause:** Missing or incorrectly formatted fields in the request body.

**Steps to fix:**
1. Review the API documentation for required fields.
2. Ensure `customer_email` is a valid email format.
3. Check that all required fields are included in the request body.

---

### API Requests Timing Out

**Steps to fix:**
1. Check the [CloudDesk status page] for any ongoing incidents.
2. Reduce request payload size if sending large amounts of data.
3. Ensure your server's outbound connections to the CloudDesk API are not blocked by a firewall.

---

## Billing Issues

### Payment Failing Repeatedly

**Steps to fix:**
1. Go to **Settings → Billing → Update Payment Method** and re-enter your card details.
2. Contact your bank to confirm the card is not being blocked for international transactions.
3. Try a different payment method (e.g., PayPal instead of a card).

---

### Features Suddenly Unavailable

**Likely cause:** Payment failure or plan downgrade.

**Steps to fix:**
1. Go to **Settings → Billing** and check your subscription status.
2. If a payment failed, update the payment method and retry.
3. If you were downgraded, upgrade your plan to restore access.

---

## Integration Issues

### Slack Notifications Not Arriving

**Steps to fix:**
1. Go to **Settings → Integrations → Slack** and confirm the integration is connected.
2. Re-authorize the Slack integration if the token has expired.
3. Check that the correct Slack channel is selected for notifications.
4. Confirm the Slack bot has permission to post in that channel.

---

### Zapier Zaps Not Triggering

**Steps to fix:**
1. Check the Zap history in Zapier for error messages.
2. Re-connect the CloudDesk app in Zapier and re-authenticate.
3. Ensure the trigger event in CloudDesk (e.g., "New Ticket") matches the Zap configuration.

---

## Performance Issues

### Dashboard Loading Slowly

**Steps to fix:**
1. Clear your browser cache and reload.
2. Disable browser extensions that may be interfering.
3. Try a different network connection.
4. Check the CloudDesk status page for any performance incidents.

---

## Contacting Support

If none of the above steps resolve your issue:
- Email: support@clouddesk.io
- Live chat: Available in the bottom-right corner of the dashboard
- Support hours: Monday to Friday, 9am – 6pm UTC
