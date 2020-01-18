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
        ERROR: {
          target: "disconnected",
          actions: ["destroyEventSource", "startReconnectTimeout"],
        },
        SUCCESS: {
          target: "connected",
          actions: ["startPingInterval"],
        },
        PUZZLE_NOT_ACTIVE: "inactive",
        INVALID: "invalid",
      },
    },
    disconnected: {
      on: {
        RECONNECT: {
          target: "connecting",
          actions: ["setEventSource"],
        },
      },
    },
    connected: {
      on: {
        ERROR: {
          target: "disconnected",
          actions: ["destroyEventSource", "startReconnectTimeout"],
        },
        PONG: {
          target: "connected",
          actions: ["broadcastPlayerLatency"],
        },
        PUZZLE_NOT_ACTIVE: "inactive",
        CLOSE: "disconnected",
      },
    },
    inactive: {},
    invalid: {},
  },
});
