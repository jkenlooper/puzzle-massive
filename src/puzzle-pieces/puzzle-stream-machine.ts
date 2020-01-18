import { createMachine } from "@xstate/fsm";

export const puzzleStreamMachine = createMachine({
  id: "puzzle-stream",
  initial: "connecting",
  context: {
    retries: 0,
  },
  states: {
    connecting: {
      on: {
        ERROR: "disconnected",
        SUCCESS: {
          target: "connected",
          actions: ["startPing"],
        },
        PUZZLE_NOT_ACTIVE: "inactive",
        INVALID: "invalid",
      },
    },
    disconnected: {
      on: {
        RECONNECT: "connecting",
      },
    },
    connected: {
      on: {
        ERROR: "disconnected",
        PUZZLE_NOT_ACTIVE: "inactive",
        CLOSE: "disconnected",
      },
    },
    inactive: {},
    invalid: {},
  },
});
