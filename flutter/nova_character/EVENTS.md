# Nova app events

Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova character repo, so this list always matches the lines in this package.

## Highlights

- A new highlight replaces the one before it.
- Highlights clear when Nova finishes the line (line_end), unless the event says it stays until the child taps.
- clear_highlight removes whatever is highlighted, for a highlight that should end mid-line.

## Every line

| Event | What the app should do |
|---|---|
| `line_end` | Sent automatically when a line finishes. Use it to move to the next step. |

## FTUX: home

Line id: `ftux_home`

| Time | Event | What the app should do |
|---|---|---|
| 5.65 s | `highlight_shops` | Highlight the shops on the home map ("See those shops?"). |
| 13.45 s | `highlight_home` | Highlight the home on the map with the arrow ("let's head inside your home"). It stays until the child taps the home. |

## Planned (not in a line yet)

Names agreed for the FTUX flow. They appear in a line once its audio is timed.

| Event | What the app should do |
|---|---|
| `highlight_sticker_book` | Highlight the sticker book in the room. |
| `highlight_closet` | Highlight the closet with the arrow. It stays until the child taps the closet. |
| `highlight_back_arrow` | Highlight the back arrow ("Tap the back arrow, and let's go!"). It stays until the child taps it. |
| `highlight_next_world_arrow` | Highlight the arrow that rotates to the next world ("Tap the arrow to keep traveling through worlds"). |
| `highlight_enter` | Highlight the Enter button on the world selection screen. |
| `clear_highlight` | Remove whatever is highlighted right now. Use it when a highlight should end before the line does. |
| `nova_exit` | Nova leaves the screen; the scene stays for the child to explore and choose. |
