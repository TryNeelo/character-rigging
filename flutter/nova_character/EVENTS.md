# Nova app events

Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova character repo, so this list always matches the lines in this package.

## Highlights

- A highlight has two parts: the spotlight (the screen dims, with a cut-out around the item) and an arrow pointing at the item. They appear together.
- A highlight stays until the script ends it, or until a new highlight replaces it. Finishing the line does not end it.
- [Stop highlight] (clear_highlight): the spotlight and the arrow fade out together.
- [Stop spotlight] (clear_spotlight): only the spotlight fades. The arrow stays and blinks until the child taps the item (or a later [Stop highlight]).

## Every line

| Event | What the app should do |
|---|---|
| `line_end` | Sent automatically when a line finishes. Use it to move to the next step. |

## FTUX: home

Line id: `ftux_home`

| Time | Event | What the app should do |
|---|---|---|
| 5.65 s | `highlight_shops` | Highlight the shops on the home map ("See those shops?"): spotlight it and point the arrow at it. |
| 13.45 s | `highlight_home` | Highlight the home on the map: spotlight it and point the arrow at it. |

## Planned (not in a line yet)

Names agreed for the FTUX flow. They appear in a line once its audio is timed.

| Event | What the app should do |
|---|---|
| `highlight_sticker_book` | Highlight the sticker book in the room: spotlight it and point the arrow at it. |
| `highlight_closet` | Highlight the closet: spotlight it and point the arrow at it. |
| `highlight_back_arrow` | Highlight the back arrow ("Tap the back arrow, and let's go!"): spotlight it and point the arrow at it. |
| `highlight_next_world_arrow` | Highlight the arrow that rotates to the next world ("Tap the arrow to keep traveling through worlds"): spotlight it and point the arrow at it. |
| `highlight_enter` | Highlight the Enter button on the world selection screen: spotlight it and point the arrow at it. |
| `clear_highlight` | End the highlight: the spotlight and the arrow fade out together. |
| `clear_spotlight` | End only the spotlight: the dim fades, the arrow stays and blinks until the child taps the item (or until a later [Stop highlight]). |
| `nova_exit` | Nova leaves the screen; the scene stays for the child to explore and choose. |
