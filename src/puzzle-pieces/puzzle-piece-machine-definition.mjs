import xstate from "@xstate/fsm";

// TODO: WIP
const IMMOVABLE = 1;
function isImmovable(context) {
  return context.s === IMMOVABLE;
}
function isMovable(context) {
  return context.s !== IMMOVABLE;
}
/*
const mutablePieceProperties = ["x", "y", "r", "s", "g"];
const immutablePieceProperties = ["id", "w", "h", "b"];
const pieceContext = ["token", "groupActive"];
const properties = pieceContext
  .concat(immutablePieceProperties, mutablePieceProperties)
  .reduce((acc, key) => {
    acc[key] = undefined;
    return acc;
  }, {});
  */
const puzzlePieceMachineDefinition = {
  id: "puzzle-piece",
  initial: "unknown",
  context: {
    // mutable piece properties
    x: undefined,
    y: undefined,
    r: undefined,
    s: undefined,
    g: undefined,
    // immutable piece properties
    id: undefined,
    w: undefined,
    h: undefined,
    b: undefined,
    // context
    token: undefined,
    groupActive: undefined,
  },
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
        MOUSEDOWN: [
          {
            target: "pendingClaim",
            actions: ["postPlayerAction"],
          },
        ],

        // server has new properties
        UPDATE: [
          {
            target: "immovable",
            cond: (context, event) => {
              // Check that the piece that is transitioning to immovable is not
              // currently part of a group that is being moved by the player.
              return (
                event.payload.s === IMMOVABLE &&
                context.groupActive === undefined
              );
            },
            actions: [
              xstate.assign({
                x: (context, event) => {
                  return event.payload.x;
                },
                y: (context, event) => {
                  return event.payload.y;
                },
                r: (context, event) => {
                  return event.payload.r;
                },
                s: (context, event) => {
                  return event.payload.s;
                },
                g: (context, event) => {
                  return event.payload.g;
                },
              }),
              "updatePiece",
            ],
          },
          {
            target: "immovable",
            cond: (context, event) => {
              // If the piece is currently part of group that is being moved by
              // the player.
              return (
                event.payload.s === IMMOVABLE &&
                context.groupActive !== undefined
              );
            },
            actions: [
              xstate.assign({
                x: (context, event) => {
                  return event.payload.x;
                },
                y: (context, event) => {
                  return event.payload.y;
                },
                r: (context, event) => {
                  return event.payload.r;
                },
                s: (context, event) => {
                  return event.payload.s;
                },
                g: (context, event) => {
                  return event.payload.g;
                },
              }),
              "abortPieceGroupMove",
              "updatePiece",
            ],
          },
          {
            target: "movable",
            cond: (context, event) => {
              return (
                event.payload.s !== IMMOVABLE &&
                context.groupActive !== undefined
              );
            },
            actions: [
              xstate.assign({
                x: (context, event) => {
                  return event.payload.x;
                },
                y: (context, event) => {
                  return event.payload.y;
                },
                r: (context, event) => {
                  return event.payload.r;
                },
                s: (context, event) => {
                  return event.payload.s;
                },
                g: (context, event) => {
                  return event.payload.g;
                },
              }),
              "updatePieceGroupMove",
              "updatePiece",
            ],
          },
        ],
      },
    },

    // player is getting token
    pendingClaim: {
      entry: ["getToken"],
      exit: [],
      on: {
        TOKEN_SUCCESS: [
          {
            target: "claimed",
            actions: [
              xstate.assign({
                token: (context, event) => {
                  return event.payload.token;
                },
              }),
            ],
          },
        ],
      },
    },

    // currently being moved by a player (5 second timeout)
    claimed: {
      entry: ["startClaimTimeout"],
      on: {
        "": [
          {
            target: "active",
            cond: (context, event) => {
              // Assume that if a token exists that the player has claimed it
              return !!context.token;
            },
          },
        ],
        // TODO: WIP should probably visualize this all first
        CLAIM_TIMEOUT: [
          {
            target: "claimed",
            cond: (context, event) => {
              // No token would imply that another player has claimed it
              return !context.token;
            },
          },
        ],
      },
    },

    // player is waiting to claim the piece
    queued: {},

    // player has selected the piece
    selected: {},

    // player is moving the piece (5 second timeout)
    active: {
      on: {
        CLAIM_TIMEOUT: [
          {
            target: "pendingClaim",
          },
        ],
        MOUSEUP: [
          {
            target: "pending",
          },
        ],
      },
    },

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
export default puzzlePieceMachineDefinition;
