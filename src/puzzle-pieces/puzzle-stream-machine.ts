import { createMachine, assign } from "@xstate/fsm";

interface Context {
  pingCount: number;
  reconnectCount: number;
}

// Set the reconnect interval to be 5 seconds.
export const RECONNECT_INTERVAL = 5 * 1000;

// Stop trying to reconnect after 2 minutes.
export const RECONNECT_TIMEOUT = 2 * 60 * 1000;

export const puzzleStreamMachine = createMachine<Context>({
  id: "puzzle-stream",
  initial: "connecting",
  context: {
    pingCount: 0,
    reconnectCount: 0,
  },
  states: {
    connecting: {
      entry: [
        "sendPing",
        assign({
          pingCount: (context: Context) => {
            return context.pingCount + 1;
          },
          reconnectCount: (context: Context) => {
            return context.reconnectCount + 1;
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
          actions: [
            "destroyEventSource",
            "broadcastDisconnected",
            "startReconnectTimeout",
          ],
        },
        SUCCESS: {
          target: "connected",
          actions: ["sendPing", "broadcastConnected"],
        },
        PUZZLE_NOT_ACTIVE: {
          target: "inactive",
          actions: ["destroyEventSource", "broadcastPuzzleStatus"],
        },
        INVALID: {
          target: "invalid",
          actions: ["destroyEventSource", "broadcastPuzzleStatus"],
        },
      },
    },
    disconnected: {
      entry: [
        assign({
          pingCount: 0,
        }),
      ],
      on: {
        WAITING_TO_RECONNECT: {
          target: "disconnected",
          actions: ["broadcastReconnecting"],
        },
        RECONNECT_TIMEOUT: {
          target: "disconnected",
          actions: ["broadcastDisconnected"],
        },
        RECONNECT: {
          target: "connecting",
          actions: ["setEventSource"],
          cond: (context: Context) => {
            return (
              context.reconnectCount <
              Math.round(RECONNECT_TIMEOUT / RECONNECT_INTERVAL)
            );
          },
        },
      },
    },
    connected: {
      entry: [
        assign({
          pingCount: 0,
          reconnectCount: 0,
        }),
      ],
      on: {
        ERROR: {
          target: "disconnected",
          actions: [
            "destroyEventSource",
            "broadcastDisconnected",
            "startReconnectTimeout",
          ],
        },
        PING: {
          target: "connected",
          actions: ["sendPing"],
        },
        PONG: {
          target: "connected",
          actions: ["broadcastPlayerLatency"],
        },
        PUZZLE_COMPLETED: {
          target: "inactive",
          actions: ["destroyEventSource", "broadcastPuzzleStatus"],
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
