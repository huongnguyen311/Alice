---
name: alice-book-meeting
description: Book, cancel, or reschedule a calendar meeting via Alice. Uses Alice's personal contacts and Google Calendar MCP.
scope: calendar
triggers:
  - "book a meeting"
  - "schedule a meeting"
  - "set up a call"
  - "create a meeting"
  - "cancel meeting"
  - "reschedule meeting"
  - "move the meeting"
  - "change meeting time"
mcp_required: claude.ai Google Calendar
---

# Skill: Book Meeting

## Rule — Always Clarify Before Acting

Never create, cancel, or reschedule a meeting from a short request alone. Always check for missing information first.

---

## Booking a Meeting

### Step 1 — Check what the user has provided

| Required | Provided? | If missing → ask |
|---|---|---|
| Attendee(s) | — | "Who should I invite?" |
| Date & time | — | "When would you like to meet?" |
| **Meeting objective** | — | "What's the objective of this meeting?" |
| **Pre-information / agenda** | — | "Any context or agenda you'd like included?" |

Ask all missing fields in a single message — do not ask one at a time.

If the user provides all details upfront (including objective), skip the clarification and book directly.

### Step 2 — Check availability

Before booking, call `gcal_list_events` for the proposed time slot to confirm it's free.
If there's a conflict, flag it and suggest the nearest free slot.

### Step 3 — Create the event

Use `gcal_create_event` with:
- `summary`: clear title reflecting the objective
- `description`: include the pre-information / agenda if provided
- `attendees`: user + all invitees (include user's own email with `organizer: true`)
- `timeZone`: `{TIMEZONE}`
- `sendUpdates`: `"all"` — always notify attendees

### Step 4 — Confirm to user

Reply with a one-line summary:
> "Booked: [title] on [date] [time] with [attendees]. Invite sent."

---

## Cancelling a Meeting

### Step 1 — Always ask for the reason first

> "Before I cancel — is there a reason you'd like me to note or communicate to the attendees?"

Wait for the answer before proceeding.

### Step 2 — Cancel and notify

Use `gcal_delete_event` or update status. Pass the reason to attendees in the cancellation message if appropriate.

---

## Rescheduling a Meeting

### Step 1 — Always ask for the reason first

> "Before I reschedule — is there a reason you'd like me to share with the attendees?"

Wait for the answer.

### Step 2 — Check the new slot

Call `gcal_list_events` to confirm the new time is free.

### Step 3 — Update and notify

Use `gcal_update_event`. Include the reason in the updated event description if provided.

---

## Key Contacts

{CONTACTS}

---

## Notes

- Timezone is always `{TIMEZONE}` unless user specifies otherwise
- Default meeting duration is {MEETING_DURATION_HOURS} hour(s) unless specified
- Always add Google Meet if `{ADD_GOOGLE_MEET_FOR_EXTERNAL}` is true and the meeting is with external parties or remote attendees
