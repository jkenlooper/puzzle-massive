import { createMachine, assign } from "@xstate/fsm";

interface Context {
  pingCount: number;
}

export const puzzleStreamMachine = createMachine({
  id: "puzzle-stream",
  initial: "connecting",
  context: {
    pingCount: 0,
  },
  states: {
    connecting: {
      entry: [
        "sendPing",
        assign({
          pingCount: (context: Context) => {
            return context.pingCount + 1;
          },
        }),
      ],
      on: {
        PING: {
          target: "connecting",
          actions: ["sendPing"],
          cond: (context: Context) => {
            return context.pingCount <= 15;
          },
        },
        ERROR: {
          target: "disconnected",
          actions: ["destroyEventSource", "startReconnectTimeout"],
        },
        SUCCESS: {
          target: "connected",
          actions: ["broadcastConnected", "sendPing"],
        },
        PUZZLE_NOT_ACTIVE: "inactive",
        INVALID: "invalid",
      },
    },
    disconnected: {
      entry: [
        assign({
          pingCount: 0,
        }),
      ],
      on: {
        RECONNECT: {
          target: "connecting",
          actions: ["setEventSource", "broadcastReconnecting", "sendPing"],
        },
      },
    },
    connected: {
      entry: [
        assign({
          pingCount: 0,
        }),
      ],
      on: {
        ERROR: {
          target: "disconnected",
          actions: ["destroyEventSource", "startReconnectTimeout"],
        },
        PING: {
          target: "connected",
          actions: ["sendPing"],
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
