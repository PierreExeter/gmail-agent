# Calendar

The Calendar view integrates with Google Calendar to help you manage schedules and respond to meeting requests extracted from emails.

![Calendar View](../assets/images/calendar.png)

## Overview

Gmail Agent connects to your Google Calendar to:

- Display upcoming events
- Process meeting requests from emails
- Find available time slots
- Schedule new events

## Viewing Events

### Event List

The calendar view shows your upcoming events:

| Field | Description |
|-------|-------------|
| **Title** | Event name |
| **Date/Time** | When the event occurs |
| **Duration** | Length of the event |
| **Location** | Physical or virtual meeting location |
| **Attendees** | Other participants |

### Time Range

By default, the view shows events for the next 7 days. You can adjust this in Settings.

## Meeting Requests

When Gmail Agent classifies an email as **MEETING_REQUEST**, it extracts:

- Proposed meeting times
- Meeting subject/purpose
- Required attendees
- Suggested location or video call link

### Processing Meeting Requests

1. View the extracted meeting details
2. Check your calendar for conflicts
3. Accept, decline, or propose an alternative

### Finding Available Slots

Click **Find Availability** to:

1. Scan your calendar for free time
2. Display available slots matching the proposed duration
3. Select a slot to accept or counter-propose

## Creating Events

For confirmed meetings, Gmail Agent can create calendar events:

### Event Details

| Field | Required | Description |
|-------|----------|-------------|
| **Title** | Yes | Meeting name |
| **Start Time** | Yes | When it begins |
| **End Time** | Yes | When it ends |
| **Description** | No | Meeting notes or agenda |
| **Location** | No | Physical address or video link |
| **Attendees** | No | Email addresses to invite |

### Sending Invitations

When you add attendees, Gmail Agent can:

- Send calendar invitations
- Track responses
- Update event status

## Calendar Permissions

Gmail Agent requests the `calendar` scope which allows:

- Reading your calendar events
- Creating new events
- Modifying events it created
- Sending calendar invitations

!!! note "Privacy"
    Gmail Agent only reads event times and titles for availability checking. It does not analyze event content.

## Integration with Email

### Automatic Detection

Emails classified as **MEETING_REQUEST** are linked to the Calendar view:

- Click "Schedule" from the Inbox
- View extracted details in Calendar
- Create the event directly

### Reply Integration

When scheduling a meeting:

1. Create the calendar event
2. Gmail Agent drafts a confirmation email
3. Review and send the confirmation

## Handling Conflicts

If a proposed meeting conflicts with existing events:

1. Gmail Agent highlights the conflict
2. Shows alternative available times
3. Helps draft a counter-proposal email

## Tips

### Keeping Calendars Clean

- Regularly review and remove outdated events
- Use consistent naming for easy searching
- Block focus time to prevent over-scheduling

### Meeting Request Best Practices

- Always verify extracted details before accepting
- Check time zones for remote meetings
- Include video call links in event descriptions

### Troubleshooting

If calendar events aren't appearing:

- Verify Google Calendar API is enabled
- Check OAuth permissions include calendar scope
- Refresh the calendar view
- Re-authenticate if necessary
