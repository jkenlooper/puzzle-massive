import { assign } from "@xstate/fsm";
// Set the reconnect interval to be 5 seconds.
export const RECONNECT_INTERVAL = 5 * 1000;
// Stop trying to reconnect after 2 minutes.
export const RECONNECT_TIMEOUT = 2 * 60 * 1000;
const MAX_PING_COUNT = 15;
const defaultContext = {
    pingCount: 0,
    reconnectCount: 0,
};
export const puzzleStreamMachineDefinition = {
    id: "puzzle-stream",
    initial: "connecting",
    context: defaultContext,
    states: {
        connecting: {
            entry: [
                "sendPing",
                assign({
                    pingCount: (context = defaultContext) => {
                        return context["pingCount"] + 1;
                    },
                    reconnectCount: (context = defaultContext) => {
                        return context["reconnectCount"] + 1;
                    },
                }),
            ],
            on: {
                PING: {
                    target: "connecting",
                    actions: ["sendPing"],
                    cond: (context) => {
                        return context.pingCount <= MAX_PING_COUNT;
                    },
                },
                PING_ERROR: {
                    target: "connecting",
                    actions: ["broadcastPingError"],
                    cond: (context) => {
                        return context.pingCount > MAX_PING_COUNT;
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
                //PUZZLE_NOT_ACTIVE: {
                //  target: "inactive",
                //  actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                //},
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
                    cond: (context) => {
                        return (context.reconnectCount <
                            Math.round(RECONNECT_TIMEOUT / RECONNECT_INTERVAL));
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
                    actions: ["broadcastPuzzleStatus"],
                },
                PUZZLE_FROZEN: {
                    target: "inactive",
                    actions: ["broadcastPuzzleStatus"],
                },
                PUZZLE_DELETED: {
                    target: "inactive",
                    actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                },
                PUZZLE_NOT_ACTIVE: {
                    target: "inactive",
                    actions: ["broadcastPuzzleStatus"],
                },
                PUZZLE_ACTIVE: {
                    target: "connected",
                    actions: ["broadcastPuzzleStatus"],
                },
                CLOSE: {
                    target: "disconnected",
                    actions: ["destroyEventSource", "broadcastDisconnected"],
                },
                INVALID: {
                    target: "invalid",
                    actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                },
            },
        },
        inactive: {
            entry: [
                assign({
                    pingCount: 0,
                    reconnectCount: 0,
                }),
            ],
            on: {
                PUZZLE_COMPLETED: {
                    target: "inactive",
                    actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                },
                PUZZLE_FROZEN: {
                    target: "inactive",
                    actions: ["broadcastPuzzleStatus"],
                },
                PUZZLE_DELETED: {
                    target: "inactive",
                    actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                },
                PUZZLE_NOT_ACTIVE: {
                    target: "inactive",
                    actions: ["broadcastPuzzleStatus"],
                },
                PUZZLE_ACTIVE: {
                    //target: "inactive",
                    //actions: ["destroyEventSource", "broadcastPuzzleStatus"],
                    target: "connected",
                    actions: ["broadcastPuzzleStatus"],
                },
            },
        },
        invalid: {},
    },
};
