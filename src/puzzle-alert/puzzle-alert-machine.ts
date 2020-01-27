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
      },
    },
    active: {
      on: {
        LATENCY_UPDATED: {
          target: "active",
          actions: ["updateLatency"],
        },
        PIECE_MOVE_BLOCKED: {
          target: "blocked",
          actions: ["showPieceMoveBlocked"],
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
        PUZZLE_IN_QUEUE: {
          target: "inactive",
          actions: ["setStatusInQueue"],
        },
      },
    },
    blocked: {
      on: {
        PIECE_MOVE_BLOCKED_TIMER: {
          target: "active",
          actions: ["hidePieceMoveBlocked"],
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
