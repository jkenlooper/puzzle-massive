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
          actions: ["broadcastConnected", "startPingInterval"],
        },
        PUZZLE_NOT_ACTIVE: "inactive",
        INVALID: "invalid",
      },
    },
    disconnected: {
      on: {
        RECONNECT: {
          target: "connecting",
          actions: ["setEventSource", "broadcastReconnecting"],
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
        CLOSE: {
          target: "disconnected",
          actions: ["destroyEventSource", "broadcastDisconnected"],
        },
      },
    },
    inactive: {},
    invalid: {},
  },
});
