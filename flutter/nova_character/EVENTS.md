# Nova app events

Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova character repo, so this list always matches the lines in this package.

## Every line

| Event | What the app should do |
|---|---|
| `line_end` | Sent automatically when a line finishes. Use it to move to the next step. |

## Onboarding: welcome

Line id: `onboarding_nova_dialogue1`

| Time | Event | What the app should do |
|---|---|---|
| 0.56 s | `show_logo` | Sample only: show the Neelo logo. Replaced when the real FTUX audio arrives. |
| 2.88 s | `show_path` | Sample only: show the path forward. Replaced when the real FTUX audio arrives. |

## Account setup: child's name

Line id: `voice_line_1`

No events in this line.

## Planned (not in a line yet)

Names agreed for the FTUX flow. They appear in a line once its audio is timed.

| Event | What the app should do |
|---|---|
| `highlight_shops` | Highlight the shops on the home map ("See those shops?"). |
| `highlight_coins` | Highlight the coin counter ("As you earn coins..."). |
| `highlight_home` | Highlight the home on the map with the arrow ("let's head inside your home"). It stays until the child taps the home. |
| `highlight_sticker_book` | Highlight the sticker book in the room. |
| `highlight_closet` | Highlight the closet with the arrow. It stays until the child taps the closet. |
| `highlight_back_arrow` | Highlight the back arrow ("Tap the back arrow, and let's go!"). It stays until the child taps it. |
| `highlight_next_world_arrow` | Highlight the arrow that rotates to the next world ("Tap the arrow to keep traveling through worlds"). |
| `highlight_enter` | Highlight the Enter button on the world selection screen. |
| `nova_exit` | Nova leaves the screen; the scene stays for the child to explore and choose. |
