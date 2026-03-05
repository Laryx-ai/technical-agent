# CloudDesk Changelog

*Latest product updates, new features, and known issues.*

---

## March 2026

### New Features
- **Conversation Memory in AI Agent:** The AI support agent now remembers earlier messages in the same conversation, making interactions feel more natural and continuous.
- **RAG-powered Responses:** The AI agent can now answer questions using your internal knowledge base documents for more accurate and company-specific answers.
- **Provider Selection:** Users can now choose between Groq and Mistral AI as the underlying model for the AI agent from the interface settings.

### Improvements
- Response streaming is now smoother on slower connections.
- Sidebar now shows the active AI service and provider clearly.

### Bug Fixes
- Fixed an issue where the chat history was not preserved when switching services.
- Fixed a 500 error that occurred when the knowledge base folder was empty during index build.

---

## February 2026

### New Features
- **Slack Integration:** Receive real-time ticket notifications in your Slack channels.
- **Ticket Export:** Download all support ticket data in CSV or JSON format from **Reports → Export Data**.
- **Microsoft Teams Integration:** Connect CloudDesk to Teams channels for ticket alerts.

### Improvements
- Faster ticket search across workspaces with more than 10,000 tickets.
- API key generation now includes an option to set key expiry dates.

### Bug Fixes
- Fixed a bug where ticket assignment rules were not applying to tickets created via the API.
- Resolved an issue where the billing page showed an incorrect renewal date for annual plans.

---

## January 2026

### New Features
- **Zapier Integration:** Connect CloudDesk to thousands of apps using Zapier automation.
- **Jira Escalation:** Escalate CloudDesk tickets to Jira issues directly from the ticket view.
- **Custom Ticket Fields:** Admins can now add custom fields to the ticket creation form.

### Improvements
- Team invitation emails now include a workspace preview before the user accepts.
- API rate limit responses now include a `Retry-After` header.

### Bug Fixes
- Fixed an issue where the password reset email was delivered to spam on certain email providers.
- Resolved a UI glitch where the ticket status dropdown appeared behind the sidebar.

---

## December 2025

### New Features
- **Live Chat Channel:** Customers can now start support conversations via live chat embedded on your website.
- **Automation Rules:** Set up auto-assignment, auto-tagging, and auto-reply rules based on ticket content.

### Improvements
- Workspace settings now load 40% faster.
- Improved mobile responsiveness on the ticket detail page.

### Bug Fixes
- Fixed a rare issue where tickets created via web form did not notify the assigned agent.

---

## Known Issues

- **PDF export:** Ticket exports to PDF are currently unavailable. Use CSV or JSON as a workaround. Expected fix: Q2 2026.
- **2FA recovery codes:** Recovery codes are not yet supported. If you lose access to your 2FA device, contact support to manually disable 2FA on your account.
- **Jira sync delay:** Status sync between CloudDesk and Jira can take up to 2 minutes in some regions.

---

## Upcoming Features (Roadmap)

- Email templates editor (Q2 2026)
- Customer satisfaction (CSAT) surveys after ticket resolution (Q2 2026)
- SLA breach alerts and escalation workflows (Q3 2026)
- Dark mode for the dashboard (Q3 2026)
