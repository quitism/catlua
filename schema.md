# Schema Documentation

**Version:** `1.0`

---

# Actions

## LOG (`id: 0`)
`Log {any:any}`

---

## WARN (`id: 1`)
`Warn {any:any}`

---

## ERROR (`id: 2`)
`Error {any:any}`

---

## WAIT (`id: 3`)
`Wait {number:number} seconds`

---

## NAV_REDIRECT (`id: 4`)
`Redirect to {string:string}`

---

## AUDIO_PLAY (`id: 5`)
`Play audio {id:string} → {variable?:string}`

---

## AUDIO_STOP_ALL (`id: 7`)
`Stop all audio`

---

## LOOK_HIDE (`id: 8`)
`Make {object:object} invisible`

---

## LOOK_SHOW (`id: 9`)
`Make {object:object} visible`

---

## LOOK_SET_TEXT (`id: 10`)
`Set {object:object} text to {string:string}`

---

## VAR_SET (`id: 11`)
`Set {variable:string} to {any:string}`

---

## VAR_INC (`id: 12`)
`Increase {variable:string} by {number:number}`

---

## VAR_DEC (`id: 13`)
`Decrease {variable:string} by {number:number}`

---

## VAR_MUL (`id: 14`)
`Multiply {variable:string} by {number:number}`

---

## VAR_DIV (`id: 15`)
`Divide {variable:string} by {number:number}`

---

## VAR_ROUND (`id: 16`)
`Round {variable:string}`

---

## VAR_FLOOR (`id: 17`)
`Floor {variable:string}`

---

## IF_EQ (`id: 18`)
`If {any:string} is equal to {any:string}`

---

## IF_NEQ (`id: 19`)
`If {any:string} is not equal to {any:string}`

---

## IF_GT (`id: 20`)
`If {any:string} is greater than {any:string}`

---

## IF_LT (`id: 21`)
`If {any:string} is lower than {any:string}`

---

## REPEAT (`id: 22`)
`Repeat {number:number} times`

---

## REPEAT_FOREVER (`id: 23`)
`Repeat forever`

---

## BREAK (`id: 24`)
`Break`

---

## END (`id: 25`)
`end`

---

## AUDIO_PLAY_LOOP (`id: 26`)
`Play looped audio {id:string} → {variable?:string}`

---

## VAR_RANDOM (`id: 27`)
`Set {var:string} to random {n:number} - {n:number}`

---

## INPUT_GET_TEXT (`id: 30`)
`Get text from {input:object} → {variable:string}`

---

## LOOK_SET_PROP (`id: 31`)
`Set {property:string} of {object:object} to {any:any}`

---

## NET_BROADCAST_PAGE (`id: 32`)
`Broadcast {message:string} across page`

---

## NET_BROADCAST_SITE (`id: 33`)
`Broadcast {message:string} across site`

---

## COOKIE_SET (`id: 34`)
`Set {cookie:string} to {any:any}`

---

## COOKIE_INC (`id: 35`)
`Increase {cookie:string} by {number:number}`

---

## COOKIE_GET (`id: 36`)
`Get cookie {cookie:string} → {variable:string}`

---

## IF_CONTAINS (`id: 37`)
`If {string:string} contains {string:string}`

---

## IF_NOT_CONTAINS (`id: 38`)
`If {string:string} doesn't contain {string:string}`

---

## LOOK_GET_PROP (`id: 39`)
`Get {property:string} of {object:object} → {variable:string}`

---

## VAR_POW (`id: 40`)
`Raise {variable:string} to the power of {number:number}`

---

## VAR_MOD (`id: 41`)
`{variable:string} modulo {number:number}`

---

## STR_SUB (`id: 42`)
`Sub {variable:string} {start:number} - {end:number}`

---

## STR_REPLACE (`id: 43`)
`Replace {string:string} in {variable:string} by {string:string}`

---

## IF_AND (`id: 44`)
`If {variable:string} AND {variable:string}`

---

## IF_OR (`id: 45`)
`If {variable:string} OR {variable:string}`

---

## IF_NOR (`id: 46`)
`If {variable:string} NOR {variable:string}`

---

## IF_XOR (`id: 47`)
`If {variable:string} XOR {variable:string}`

---

## STR_LEN (`id: 48`)
`Get length of {string:string} → {variable:string}`

---

## LOOK_DUPLICATE (`id: 49`)
`Duplicate {object:object} → {variable:string}`

---

## LOOK_DELETE (`id: 50`)
`Delete {object:object}`

---

## USER_GET_NAME (`id: 51`)
`Get local username → {variable:string}`

---

## USER_GET_ID (`id: 52`)
`Get local user ID → {variable:string}`

---

## USER_GET_DISPLAY (`id: 53`)
`Get local display name → {variable:string}`

---

## TABLE_CREATE (`id: 54`)
`Create table {table:string}`

---

## TABLE_SET (`id: 55`)
`Set entry {entry:string} of {table:string} to {any:string}`

---

## TABLE_GET (`id: 56`)
`Get entry {entry:string} of {table:string} → {variable:string}`

---

## STR_SPLIT (`id: 57`)
`Split {string:string} {separator:string} → {table:string}`

---

## HIER_PARENT (`id: 58`)
`Parent {object:object} under {object:object}`

---

## TABLE_LEN (`id: 59`)
`Get length of {array:string} → {variable:string}`

---

## COOKIE_DEL (`id: 62`)
`Delete cookie {cookie:string}`

---

## FUNC_RUN_BG (`id: 63`)
`Run function in background {function:string} {tuple:tuple}`

---

## TABLE_SET_OBJ (`id: 66`)
`Set entry {entry:string} of {table:string} to {object:object}`

---

## NAV_GET_QUERY (`id: 67`)
`Get query string parameter {string:string} → {variable:string}`

---

## TIME_GET_UNIX (`id: 68`)
`Get unix timestamp → {variable:string}`

---

## STR_LOWER (`id: 69`)
`Lower {string:string} → {variable:string}`

---

## STR_UPPER (`id: 70`)
`Upper {string:string} → {variable:string}`

---

## TIME_FORMAT_NOW (`id: 71`)
`Format current date/time {format:string} → {variable:string}`

---

## TIME_FORMAT_UNIX (`id: 72`)
`Format from unix {number:number} {format:string} → {variable:string}`

---

## AUDIO_SET_VOL (`id: 73`)
`Set volume of {variable:string} to {number:number}`

---

## AUDIO_STOP (`id: 74`)
`Stop audio {variable:string}`

---

## AUDIO_PAUSE (`id: 75`)
`Pause audio {variable:string}`

---

## AUDIO_RESUME (`id: 76`)
`Resume audio {variable:string}`

---

## AUDIO_SET_SPEED (`id: 77`)
`Set speed of {variable:string} to {number:number}`

---

## VAR_CEIL (`id: 78`)
`Ceil {variable:string}`

---

## IF_MOUSE_LEFT (`id: 79`)
`If left mouse button down`

---

## IF_MOUSE_MIDDLE (`id: 80`)
`If middle mouse button down`

---

## IF_MOUSE_RIGHT (`id: 81`)
`If right mouse button down`

---

## IF_KEY_DOWN (`id: 82`)
`If {key:key} down`

---

## TIME_GET_TICK (`id: 83`)
`Get tick → {variable:string}`

---

## INPUT_GET_VIEWPORT (`id: 84`)
`Get viewport size → {x:string} {y:string}`

---

## INPUT_GET_CURSOR (`id: 85`)
`Get cursor position → {x:string} {y:string}`

---

## FUNC_RUN (`id: 87`)
`Run function {function:string} {tuple:tuple} → {variable?:string}`

---

## LOOK_TWEEN (`id: 88`)
`Tween {property:string} of {object:object} to {any:any} - {time:number} {style:string} {direction:string}`

---

## TABLE_INSERT (`id: 89`)
`Insert {any:string} at position {number?:number} of {array:string}`

---

## TABLE_DEL (`id: 90`)
`Delete entry {entry:string} of {table:string}`

---

## TABLE_REMOVE (`id: 91`)
`Remove entry at position {number?:number} of {array:string}`

---

## IF_EXISTS (`id: 92`)
`If {variable:string} exists`

---

## IF_NOT_EXISTS (`id: 93`)
`If {variable:string} doesn't exist`

---

## AVAR_SET (`id: 94`)
`Set {property:string} of {variable:string} to {any:any}`

---

## AVAR_GET (`id: 95`)
`Get {property:string} of {variable:string} → {variable:string}`

---

## VAR_DEL (`id: 96`)
`Delete {variable:string}`

---

## HIER_GET_PARENT (`id: 97`)
`Get parent of {object:object} → {variable:string}`

---

## HIER_FIND_ANCESTOR (`id: 98`)
`Find ancestor named {string:string} in {object:object} → {variable:string}`

---

## HIER_FIND_CHILD (`id: 99`)
`Find child named {string:string} in {object:object} → {variable:string}`

---

## HIER_FIND_DESCENDANT (`id: 100`)
`Find descendant named {string:string} in {object:object} → {variable:string}`

---

## HIER_GET_CHILDREN (`id: 101`)
`Get children of {object:object} → {table:string}`

---

## HIER_GET_DESCENDANTS (`id: 102`)
`Get descendants of {object:object} → {table:string}`

---

## IF_IS_ANCESTOR (`id: 103`)
`If {object:object} is ancestor of {object:object}`

---

## IF_IS_CHILD (`id: 104`)
`If {object:object} is child of {object:object}`

---

## IF_IS_DESCENDANT (`id: 105`)
`If {object:object} is descendant of {object:object}`

---

## LOOK_SET_IMG (`id: 106`)
`Set {object:object} image to {id:id}`

---

## LOOK_SET_AVATAR (`id: 107`)
`Set {object:object} image to avatar of {userid:number} {resolution?:string}`

---

## IF_DARK_THEME (`id: 108`)
`If dark theme enabled`

---

## STR_CONCAT (`id: 109`)
`Concatenate {string:string} with {string:string} → {variable:string}`

---

## TABLE_JOIN (`id: 110`)
`Join {array:string} using {string:string} → {variable:string}`

---

## ELSE (`id: 112`)
`else`

---

## TABLE_ITER (`id: 113`)
`Iterate through {table:string} ({l!index},{l!value})`

---

## MATH_RUN (`id: 114`)
`Run math function {function:string} {tuple:tuple} → {variable:string}`

---

## RETURN (`id: 115`)
`Return {any:string}`

---

## TIME_GET_SERVER_UNIX (`id: 116`)
`Get server unix timestamp → {variable:string}`

---

## NAV_GET_URL (`id: 117`)
`Get URL → {variable:string}`

---

## TIME_GET_TIMEZONE (`id: 118`)
`Get timezone → {variable:string}`

---

## COLOR_HEX_TO_RGB (`id: 119`)
`Convert {hex:string} to RGB → {variable:string}`

---

## COLOR_HEX_TO_HSV (`id: 120`)
`Convert {hex:string} to HSV → {variable:string}`

---

## COLOR_RGB_TO_HEX (`id: 121`)
`Convert {RGB:string} to hex → {variable:string}`

---

## COLOR_HSV_TO_HEX (`id: 122`)
`Convert {HSV:string} to hex → {variable:string}`

---

## COLOR_LERP (`id: 123`)
`Lerp {hex:string} to {hex:string} by {alpha:number} → {variable:string}`

---

## COMMENT (`id: 124`)
`{comment:string}`

---

## IF_GTE (`id: 125`)
`If {any:string} is greater or equal to {any:string}`

---

## IF_LTE (`id: 126`)
`If {any:string} is lower or equal to {any:string}`

---

## LOOK_GET_AT_POS (`id: 127`)
`Get objects at position {x:string} {y:string} → {array:string}`

---

## FUNC_RUN_PROTECTED (`id: 128`)
`Run protected function {function:string} {tuple:tuple} → {success_variable?:string} {variable?:string}`

---

## LOOK_GET_ASSET_INFO (`id: 129`)
`Get {info:string} of asset {id:string} → {variable:string}`

---

## NET_BROADCAST_CROSSSITE (`id: 130`)
`Broadcast {message:string} cross-site to {page:string}`

---

# Events

## LOADED (`id: 0`)
`When website loaded...`

---

## PRESSED (`id: 1`)
`When {button:object} pressed...`

**Params:** object

---

## KEY_PRESSED (`id: 2`)
`When {key:key} pressed...`

**Params:** key

---

## MOUSE_ENTER (`id: 3`)
`When mouse enters {object:object} ...`

**Params:** object

---

## MOUSE_LEAVE (`id: 5`)
`When mouse leaves {object:object} ...`

**Params:** object

---

## FUNC_DEF (`id: 6`)
`Define function {function:string}`

**Params:** function_name, args

---

## DONATION (`id: 7`)
`When {donation:object} bought...`

**Params:** object

---

## INPUT_SUBMIT (`id: 8`)
`When {input:object} submitted...`

**Params:** object

---

## MSG_RECEIVED (`id: 9`)
`When message received...`

---

## CHANGED (`id: 10`)
`When {object:object} changed...`

**Params:** object

---

## MOUSE_DOWN (`id: 11`)
`When mouse down on {button:object} ...`

**Params:** object

---

## MOUSE_UP (`id: 12`)
`When mouse up on {button:object} ...`

**Params:** object

---

## RIGHT_CLICKED (`id: 13`)
`When {button:object} right clicked...`

**Params:** object

---

## CROSSSITE_MSG (`id: 14`)
`When cross-site message received...`

---

