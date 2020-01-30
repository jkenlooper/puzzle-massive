import { createMachine } from "@xstate/fsm";

export const puzzleAlertMachine = createMachine({
  id: "puzzle-alert",
  initial: "connecting",
  context: {},
  states: {
    connecting: {
      on: {
        SUCCESS: {
          target: "active",
          actions: ["setStatusConnected"],
        },
        RECONNECTING: {
          target: "connecting",
          actions: ["setStatusReconnecting"],
        },
        DISCONNECTED: {
          target: "disconnected",
          actions: ["setStatusDisconnected"],
        },
        PUZZLE_INVALID: {
          target: "inactive",
          actions: ["setInvalid"],
        },
        PING_ERROR: {
          target: "connecting",
          actions: ["setStatusError"],
        }
      },
    },
    active: {
      on: {
        LATENCY_UPDATED: {
          target: "active",
          actions: ["updateLatency"],
        },
        PIECE_MOVE_BLOCKED: {
          target: "active",
          actions: ["showPieceMoveBlocked"],
        },
        PIECE_MOVE_BLOCKED_TIMER: {
          target: "active",
          actions: ["hidePieceMoveBlocked"],
        },
        DISCONNECTED: {
          target: "disconnected",
          actions: ["setStatusDisconnected"],
        },
        PUZZLE_COMPLETED: {
          target: "inactive",
          actions: ["setStatusCompleted"],
        },
        PUZZLE_FROZEN: {
          target: "inactive",
          actions: ["setStatusFrozen"],
        },
        PUZZLE_DELETED: {
          target: "inactive",
          actions: ["setStatusDeleted"],
        },
        PUZZLE_IN_QUEUE: {
          target: "inactive",
          actions: ["setStatusInQueue"],
        },
      },
    },
    inactive: {},
    disconnected: {
      on: {
        RECONNECTING: {
          target: "connecting",
          actions: ["setStatusReconnecting"],
        },
        DISCONNECTED: {
          target: "disconnected",
          actions: ["setStatusDisconnected"],
        },
      },
    },
  },
});
