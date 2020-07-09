import xstate from "@xstate/fsm";

// TODO: WIP
const IMMOVABLE = 1;
function isImmovable(context) {
  return context.s === IMMOVABLE;
}
function isMovable(context) {
  return context.s !== IMMOVABLE;
}
const pieceProperties = ["id", "x", "y", "r", "s", "w", "h", "b"].reduce(
  (acc, key) => {
    acc[key] = undefined;
    return acc;
  },
  {}
);
export const puzzlePieceMachineDefinition = {
  id: "puzzle-piece",
  initial: "unknown",
  context: pieceProperties,
  states: {
    unknown: {
      // Immediately transition to the next state
      // depending on the status ('s') value.
      on: {
        "": [
          {
            target: "immovable",
            cond: isImmovable,
          },
          {
            target: "movable",
            cond: isMovable,
          },
        ],
      },
    },

    // waiting for initial response from server
    //frozen: {
    //  entry: [
    //    // sync properties?
    //  ],
    //  on: {},
    //},

    // locked in it's current position
    immovable: {
      type: "final",
    },

    // can be moved
    movable: {
      entry: [],
      exit: [],
      on: {
        // mousedown or touchstart
        MOUSEDOWN: {},

        // server has new properties
        UPDATE: [
          {
            target: "immovable",
            cond: (context, event) => {
              return event.payload.s === IMMOVABLE;
            },
            actions: [
              xstate.assign({
                x: (context, event) => {
                  return event.payload.x;
                } /* "y", "r", "s",*/,
              }),
            ],
          },
          {
            target: "movable",
            cond: (context, event) => {
              return event.payload.s !== IMMOVABLE;
            },
            actions: [
              xstate.assign({
                x: (context, event) => {
                  return event.payload.x;
                } /* "y", "r", "s",*/,
              }),
            ],
          },
        ],
      },
    },

    // currently being moved by a player (5 second timeout)
    claimed: {},

    // player is waiting to claim the piece
    queued: {},

    // player has selected the piece
    selected: {},

    // player is moving the piece (5 second timeout)
    active: {},

    // player has dropped the piece and is waiting for server response
    pending: {},

    //// is transitioning to new position
    //animating: {
    //  entry: [
    //    "startAnimation",
    //    assign({
    //    }),
    //  ]
    //},
  },
};
