# Nova app events

Events Nova sends to the app while he talks. Listen for them on `NovaController.events`; each `NovaEvent` has the `name` below and the time in the line. Generated from the Nova character repo, so this list always matches the lines in this package.

## Highlights

- A highlight has two parts: the spotlight (a dark overlay with a cut-out around the item) and an arrow pointing at the item. They appear together.
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
| 17.30 s | `clear_spotlight` | End only the spotlight: the spotlight fades, the arrow stays and blinks until the child taps the item (or until a later [Stop highlight]). |

## FTUX: home return

Line id: `ftux_home_return`

| Time | Event | What the app should do |
|---|---|---|
| 5.13 s | `highlight_back_arrow` | Highlight the back arrow ("Tap the back arrow, and let's go!"): spotlight it and point the arrow at it. |
| 7.60 s | `clear_spotlight` | End only the spotlight: the spotlight fades, the arrow stays and blinks until the child taps the item (or until a later [Stop highlight]). |

## FTUX: room

Line id: `ftux_room`

| Time | Event | What the app should do |
|---|---|---|
| 4.23 s | `highlight_sticker_book` | Highlight the sticker book in the room: spotlight it and point the arrow at it. |
| 13.57 s | `highlight_closet` | Highlight the closet: spotlight it and point the arrow at it. |
| 18.38 s | `clear_spotlight` | End only the spotlight: the spotlight fades, the arrow stays and blinks until the child taps the item (or until a later [Stop highlight]). |

## FTUX: world 1

Line id: `ftux_w1`

No events in this line.

## FTUX: world 2

Line id: `ftux_w2`

No events in this line.

## FTUX: world 3

Line id: `ftux_w3`

No events in this line.

## FTUX: world 4

Line id: `ftux_w4`

No events in this line.

## FTUX: world select

Line id: `ftux_world_select`

| Time | Event | What the app should do |
|---|---|---|
| 2.95 s | `start_world_rotation` | Start rotating the worlds on the world selection screen: slide to the next world, pause briefly, and repeat, at a pace the app chooses, until [Stop world rotation]. |
| 7.76 s | `stop_world_rotation` | Stop rotating the worlds: finish the slide in progress and stay on that world. |
| 9.21 s | `highlight_next_world_arrow` | Highlight the arrow that rotates to the next world ("Tap the arrow to keep traveling through worlds"): spotlight it and point the arrow at it. |
| 10.84 s | `clear_highlight` | End the highlight: the spotlight and the arrow fade out together. |
| 14.27 s | `highlight_enter` | Highlight the Enter button on the world selection screen: spotlight it and point the arrow at it. |
| 15.88 s | `clear_highlight` | End the highlight: the spotlight and the arrow fade out together. |

## Planned (not in a line yet)

Names agreed for the FTUX flow. They appear in a line once its audio is timed.

| Event | What the app should do |
|---|---|
| `nova_exit` | Nova leaves the screen; the scene stays for the child to explore and choose. |
