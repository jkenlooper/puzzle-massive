import { createMachine } from "@xstate/fsm";
import { puzzleStreamMachineDefinition } from "./puzzle-stream-machine-definition";

export {
  RECONNECT_INTERVAL,
  RECONNECT_TIMEOUT,
} from "./puzzle-stream-machine-definition";

type State =
  | {
      value: "connecting";
      context: Context;
    }
  | {
      value: "disconnected";
      context: Context;
    }
  | {
      value: "connected";
      context: Context;
    }
  | {
      value: "inactive";
      context: Context;
    }
  | {
      value: "invalid";
      context: Context;
    };

type Event =
  | { type: "CLOSE" }
  | { type: "ERROR" }
  | { type: "INVALID" }
  | { type: "PING" }
  | { type: "PING_ERROR" }
  | { type: "PONG" }
  | { type: "PUZZLE_ACTIVE" }
  | { type: "PUZZLE_COMPLETED" }
  | { type: "PUZZLE_DELETED" }
  | { type: "PUZZLE_FROZEN" }
  | { type: "PUZZLE_NOT_ACTIVE" }
  | { type: "RECONNECT" }
  | { type: "RECONNECT_TIMEOUT" }
  | { type: "SUCCESS" }
  | { type: "WAITING_TO_RECONNECT" };

interface Context {
  pingCount: number;
  reconnectCount: number;
}

export const puzzleStreamMachine = createMachine<Context, Event, State>(
  puzzleStreamMachineDefinition
);
