# Nova app events

Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova character repo, so this list always matches the lines in this package.

## Highlights

- Every highlight dims the screen with a cut-out around the item, and shows an arrow pointing at it. The dim and the arrow appear together.
- A highlight stays until the script says [Stop highlight] (clear_highlight), or until a new highlight replaces it. Finishing the line does not end it.
- Spotlight: at [Stop highlight] the dim and the arrow fade out together.
- Tap target: at [Stop highlight] the dim fades out, but the arrow stays and blinks until the child taps the item.

## Every line

| Event | What the app should do |
|---|---|
| `line_end` | Sent automatically when a line finishes. Use it to move to the next step. |

## FTUX: home

Line id: `ftux_home`

| Time | Event | What the app should do |
|---|---|---|
| 5.65 s | `highlight_shops` | Spotlight the shops on the home map ("See those shops?"). |
| 13.45 s | `highlight_home` | Spotlight the home on the map. Tap target: after [Stop highlight] the arrow keeps blinking until the child taps the home. |

## Planned (not in a line yet)

Names agreed for the FTUX flow. They appear in a line once its audio is timed.

| Event | What the app should do |
|---|---|
| `highlight_sticker_book` | Spotlight the sticker book in the room. |
| `highlight_closet` | Spotlight the closet. Tap target: after [Stop highlight] the arrow keeps blinking until the child taps the closet. |
| `highlight_back_arrow` | Spotlight the back arrow ("Tap the back arrow, and let's go!"). Tap target: after [Stop highlight] the arrow keeps blinking until the child taps it. |
| `highlight_next_world_arrow` | Spotlight the arrow that rotates to the next world ("Tap the arrow to keep traveling through worlds"). |
| `highlight_enter` | Spotlight the Enter button on the world selection screen. |
| `clear_highlight` | End the current highlight: the dim fades out. A spotlight's arrow fades with it; a tap target's arrow stays and blinks until the child taps. |
| `nova_exit` | Nova leaves the screen; the scene stays for the child to explore and choose. |
